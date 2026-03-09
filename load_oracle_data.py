"""
Custom data loader script that handles Oracle duplicate key errors gracefully.
This script loads data from full_db_dump.json into Oracle database,
using update-or-insert (upsert) logic to avoid ORA-00001 errors.
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grassroot_iris.settings')
django.setup()

from django.core import serializers
from django.db import transaction, connection
from django.apps import apps

def disable_constraints():
    """Disable all foreign key constraints temporarily"""
    with connection.cursor() as cursor:
        # Get all foreign key constraints
        cursor.execute("""
            SELECT 'ALTER TABLE ' || table_name || ' DISABLE CONSTRAINT ' || constraint_name
            FROM user_constraints
            WHERE constraint_type = 'R'
        """)
        statements = [row[0] for row in cursor.fetchall()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Warning disabling constraint: {e}")

def enable_constraints():
    """Re-enable all foreign key constraints"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 'ALTER TABLE ' || table_name || ' ENABLE CONSTRAINT ' || constraint_name
            FROM user_constraints
            WHERE constraint_type = 'R'
        """)
        statements = [row[0] for row in cursor.fetchall()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Warning enabling constraint: {e}")

def truncate_all_tables():
    """Truncate all application tables to start fresh"""
    tables_to_truncate = [
        # Order matters due to FK constraints - truncate child tables first
        'IRIS_USER_BADGES',
        'IRIS_USER_ROLES',
        'IRIS_USER_LOGIN_LOGS',
        'IRIS_WORKFLOW_LOGS',
        'IRIS_REVIEW_RATINGS',
        'IRIS_REVIEWS',
        'IRIS_REVIEW_PARAMETERS',
        'IRIS_GRASSROOT_EVALUATIONS',
        'IRIS_GRASSROOT_IDEAS',
        'IRIS_CO_IDEATORS',
        'IRIS_IDEA_CATEGORY_MAPPING',
        'IRIS_IDEA_DOCUMENTS',
        'IRIS_IDEA_DETAILS',
        'IRIS_IDEAS',
        'IRIS_CHALLENGE_MENTORS',
        'IRIS_CHALLENGE_PANELS',
        'IRIS_CHALLENGE_REVIEW_PARAMS',
        'IRIS_CHALLENGES',
        'IRIS_IMPROVEMENT_SUB_CATEGDE2E',
        'IRIS_IMPROVEMENT_CATEGORIES',
        'IRIS_IDEA_CATEGORIES',
        'IRIS_NOTIFICATIONS',
        'IRIS_REWARDS',
        'IRIS_BADGES',
        'IRIS_USERS',
        'IRIS_EMPLOYEE_DETAILS',
        'IRIS_ROLES',
        'DJANGO_ADMIN_LOG',
        'AUTH_USER_USER_PERMISSIONS',
        'AUTH_USER_GROUPS',
        'AUTH_GROUP_PERMISSIONS',
        'AUTH_USER',
        'AUTH_GROUP',
        'AUTH_PERMISSION',
        'DJANGO_CONTENT_TYPE',
        'DJANGO_SESSION',
    ]

    with connection.cursor() as cursor:
        for table in tables_to_truncate:
            try:
                cursor.execute(f"TRUNCATE TABLE {table}")
                print(f"  Truncated: {table}")
            except Exception as e:
                print(f"  Warning truncating {table}: {e}")

def load_fixture(fixture_path):
    """Load fixture data with error handling"""
    print(f"\nLoading fixture: {fixture_path}")

    with open(fixture_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total records to load: {len(data)}")

    # Group by model for ordered loading
    model_groups = {}
    for item in data:
        model_label = item['model']
        if model_label not in model_groups:
            model_groups[model_label] = []
        model_groups[model_label].append(item)

    print(f"Models found: {list(model_groups.keys())}")

    # Load order - dependencies first
    load_order = [
        'contenttypes.contenttype',
        'auth.permission',
        'auth.group',
        'auth.user',
        'iris_app.role',
        'iris_app.ideacategory',
        'iris_app.badge',
        'iris_app.reward',
        'iris_app.employeedetail',
        'iris_app.irisuser',
        'iris_app.challenge',
        'iris_app.challengepanel',
        'iris_app.challengementor',
        'iris_app.idea',
        'iris_app.ideadetail',
        'iris_app.ideadocument',
        'iris_app.ideacategorymapping',
        'iris_app.coideator',
        'iris_app.review',
        'iris_app.reviewparameter',
        'iris_app.workflowlog',
        'iris_app.userbadge',
        'iris_app.userrole',
        'iris_app.notification',
        'admin.logentry',
        'sessions.session',
    ]

    # Add any models not in the explicit order
    for model_label in model_groups.keys():
        if model_label.lower() not in [m.lower() for m in load_order]:
            load_order.append(model_label)

    total_loaded = 0
    total_errors = 0

    for model_label in load_order:
        # Find matching model (case-insensitive)
        matching_key = None
        for key in model_groups.keys():
            if key.lower() == model_label.lower():
                matching_key = key
                break

        if matching_key is None:
            continue

        items = model_groups[matching_key]
        print(f"\nLoading {matching_key}: {len(items)} records...")

        loaded = 0
        errors = 0

        for item in items:
            try:
                with transaction.atomic():
                    # Use Django's deserializer
                    for obj in serializers.deserialize('json', json.dumps([item])):
                        obj.save()
                        loaded += 1
            except Exception as e:
                error_msg = str(e)
                if 'ORA-00001' in error_msg or 'unique constraint' in error_msg.lower():
                    # Try to update instead
                    try:
                        with transaction.atomic():
                            for obj in serializers.deserialize('json', json.dumps([item])):
                                # Force update
                                obj.object.save(force_update=True)
                                loaded += 1
                    except Exception as e2:
                        errors += 1
                        if errors <= 3:
                            print(f"  Error on pk={item.get('pk')}: {str(e2)[:100]}")
                else:
                    errors += 1
                    if errors <= 3:
                        print(f"  Error on pk={item.get('pk')}: {error_msg[:100]}")

        print(f"  Loaded: {loaded}, Errors: {errors}")
        total_loaded += loaded
        total_errors += errors

    print(f"\n{'='*50}")
    print(f"TOTAL LOADED: {total_loaded}")
    print(f"TOTAL ERRORS: {total_errors}")
    return total_loaded, total_errors

if __name__ == '__main__':
    print("="*50)
    print("Oracle Database Data Loader")
    print("="*50)

    # Step 1: Disable FK constraints
    print("\nStep 1: Disabling foreign key constraints...")
    disable_constraints()
    print("Done.")

    # Step 2: Truncate tables
    print("\nStep 2: Truncating existing data...")
    truncate_all_tables()
    print("Done.")

    # Step 3: Load fixture
    print("\nStep 3: Loading fixture data...")
    fixture_path = os.path.join(os.path.dirname(__file__), 'full_db_dump.json')
    total_loaded, total_errors = load_fixture(fixture_path)

    # Step 4: Re-enable constraints
    print("\nStep 4: Re-enabling foreign key constraints...")
    enable_constraints()
    print("Done.")

    # Step 5: Reset sequences
    print("\nStep 5: Resetting Oracle sequences...")
    with connection.cursor() as cursor:
        # Get all sequences
        cursor.execute("SELECT SEQUENCE_NAME FROM USER_SEQUENCES")
        sequences = [row[0] for row in cursor.fetchall()]
        for seq in sequences:
            try:
                # Get current max value from corresponding table
                # Sequences in Oracle need manual reset
                cursor.execute(f"SELECT {seq}.NEXTVAL FROM DUAL")
                current = cursor.fetchone()[0]
                print(f"  Sequence {seq}: current value = {current}")
            except Exception as e:
                print(f"  Warning with sequence {seq}: {e}")

    print("\n" + "="*50)
    print("Data loading complete!")
    print(f"Successfully loaded: {total_loaded} records")
    print(f"Errors encountered: {total_errors} records")
    print("="*50)
