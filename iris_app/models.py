import uuid
from django.db import models

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'IRIS_ROLES'
        managed = True

    def __str__(self):
        return self.role_name

class IrisUser(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=100)
    USER_TYPE_CHOICES = [
        ('INTERNAL', 'Internal'),
        ('EXTERNAL', 'External'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'IRIS_USERS'
        managed = True

    def __str__(self):
        return self.full_name

    @property
    def is_challenge_owner(self):
        return UserRole.objects.filter(user=self, role__role_name='Challenge Owner').exists()

    @property
    def is_ibu_head(self):
        return UserRole.objects.filter(user=self, role__role_name='IBU Head').exists()

    @property
    def is_rm(self):
        # A user is an RM if they have at least one reporter
        return self.reporters.exists()

class UserRole(models.Model):
    user = models.ForeignKey(IrisUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'IRIS_USER_ROLES'
        unique_together = (('user', 'role'),)
        managed = True

class EmployeeDetail(models.Model):
    user = models.OneToOneField(IrisUser, on_delete=models.CASCADE, primary_key=True)
    current_project_code = models.CharField(max_length=50, blank=True, null=True)
    current_project_name = models.CharField(max_length=100, blank=True, null=True)
    current_customer = models.CharField(max_length=100, blank=True, null=True)
    pm_dm_name = models.CharField(max_length=100, blank=True, null=True)
    service_line = models.CharField(max_length=100, blank=True, null=True)
    reporting_manager = models.ForeignKey(IrisUser, on_delete=models.SET_NULL, null=True, related_name='reporters')
    ibu_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'IRIS_EMPLOYEE_DETAILS'
        managed = True

class Challenge(models.Model):
    challenge_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_by = models.ForeignKey(IrisUser, on_delete=models.SET_NULL, null=True)
    
    # New fields from postchalleage.docx
    keywords = models.CharField(max_length=255, blank=True, null=True)
    challenge_icon = models.ImageField(upload_to='challenge_icons/', blank=True, null=True)
    
    round1_eval_start = models.DateTimeField(blank=True, null=True)
    round1_eval_end = models.DateTimeField(blank=True, null=True)
    round2_eval_start = models.DateTimeField(blank=True, null=True)
    round2_eval_end = models.DateTimeField(blank=True, null=True)
    
    key_insights = models.TextField(blank=True, null=True)
    expected_outcome = models.TextField(blank=True, null=True)
    
    has_idea_template = models.BooleanField(default=False)
    idea_template_file = models.FileField(upload_to='challenge_templates/', blank=True, null=True)
    challenge_document = models.FileField(upload_to='challenge_docs/', blank=True, null=True)
    
    VISIBILITY_CHOICES = [('PUBLIC', 'Public'), ('PRIVATE', 'Private')]
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='PUBLIC')
    
    TARGET_AUDIENCE_CHOICES = [('INTERNAL', 'Internal'), ('EXTERNAL', 'External'), ('BOTH', 'Both')]
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES, default='INTERNAL')
    
    STATUS_CHOICES = [('DRAFT', 'Draft'), ('LIVE', 'Live'), ('COMPLETED', 'Completed'), ('ARCHIVED', 'Archived')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'IRIS_CHALLENGES'
        managed = True

    def __str__(self):
        return self.title

class ChallengeReviewParameter(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='review_parameters')
    parameter = models.ForeignKey('ReviewParameter', on_delete=models.CASCADE)
    weightage = models.IntegerField(help_text="Weightage (e.g., 5, 10, 15, 20). Total must be 100.")

    class Meta:
        db_table = 'IRIS_CHALLENGE_REVIEW_PARAMS'
        unique_together = (('challenge', 'parameter'),)
        managed = True

class ChallengePanel(models.Model):
    panel_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    panel_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    round_number = models.IntegerField()

    class Meta:
        db_table = 'IRIS_CHALLENGE_PANELS'
        managed = True

class ChallengeMentor(models.Model):
    panel = models.ForeignKey(ChallengePanel, on_delete=models.CASCADE)
    mentor = models.ForeignKey(IrisUser, on_delete=models.CASCADE)

    class Meta:
        db_table = 'IRIS_CHALLENGE_MENTORS'
        unique_together = (('panel', 'mentor'),)
        managed = True

class Idea(models.Model):
    idea_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    submitter = models.ForeignKey(IrisUser, on_delete=models.SET_NULL, null=True)
    challenge = models.ForeignKey(Challenge, on_delete=models.SET_NULL, null=True, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'), ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'),
        ('IMPLEMENTED', 'Implemented'), ('ARCHIVED', 'Archived')
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='SUBMITTED')
    
    is_confidential = models.BooleanField(default=False)
    
    SHARING_SCOPE_CHOICES = [
        ('CUSTOMER', 'Customer'), ('ECOSYSTEM', 'Ecosystem'),
        ('PUBLIC', 'Public'), ('NONE', 'None')
    ]
    sharing_scope = models.CharField(max_length=50, choices=SHARING_SCOPE_CHOICES, default='NONE')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'IRIS_IDEAS'
        managed = True

    def __str__(self):
        return self.title

class IdeaDetail(models.Model):
    idea = models.OneToOneField(Idea, on_delete=models.CASCADE, primary_key=True)
    problem_statement = models.TextField(blank=True, null=True)
    proposed_solution = models.TextField(blank=True, null=True)
    business_value_monetary = models.TextField(blank=True, null=True)
    business_value_non_monetary = models.TextField(blank=True, null=True)
    assumptions = models.TextField(blank=True, null=True)
    risks = models.TextField(blank=True, null=True)
    context = models.TextField(blank=True, null=True)
    
    INNOVATION_TYPE_CHOICES = [
        ('INCREMENTAL', 'Incremental'),
        ('ADJACENT', 'Adjacent'),
        ('DISRUPTIVE', 'Disruptive')
    ]
    innovation_type = models.CharField(max_length=50, choices=INNOVATION_TYPE_CHOICES, blank=True, null=True)

    class Meta:
        db_table = 'IRIS_IDEA_DETAILS'
        managed = True

class IdeaCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100)
    theme_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'IRIS_IDEA_CATEGORIES'
        managed = True

    def __str__(self):
        return self.category_name

class IdeaCategoryMapping(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE)
    category = models.ForeignKey(IdeaCategory, on_delete=models.CASCADE)

    class Meta:
        db_table = 'IRIS_IDEA_CATEGORY_MAPPING'
        unique_together = (('idea', 'category'),)
        managed = True

class CoIdeator(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE)
    user = models.ForeignKey(IrisUser, on_delete=models.CASCADE)

    class Meta:
        db_table = 'IRIS_CO_IDEATORS'
        unique_together = (('idea', 'user'),)
        managed = True

class IdeaDocument(models.Model):
    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_url = models.FileField(upload_to='idea_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'IRIS_IDEA_DOCUMENTS'
        managed = True

class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    ENTITY_TYPE_CHOICES = [('IDEA', 'Idea'), ('CHALLENGE_SOLUTION', 'Challenge Solution')]
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPE_CHOICES, blank=True, null=True)
    
    entity_id = models.UUIDField() # Generic link, could use GenericForeignKey but keeping simple as per SQL
    reviewer = models.ForeignKey(IrisUser, on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(blank=True, null=True) # Validator could be added
    comments = models.TextField(blank=True, null=True)
    stage = models.CharField(max_length=50, blank=True, null=True)
    
    DECISION_CHOICES = [('APPROVE', 'Approve'), ('REJECT', 'Reject'), ('REWORK', 'Rework')]
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, blank=True, null=True)
    
    review_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'IRIS_REVIEWS'
        managed = True

class WorkflowLog(models.Model):
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=20, blank=True, null=True)
    entity_id = models.UUIDField(blank=True, null=True)
    previous_status = models.CharField(max_length=50, blank=True, null=True)
    new_status = models.CharField(max_length=50, blank=True, null=True)
    changed_by = models.ForeignKey(IrisUser, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'IRIS_WORKFLOW_LOGS'
        managed = True

class Reward(models.Model):
    reward_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(IrisUser, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    reason = models.CharField(max_length=255, blank=True, null=True)
    date_earned = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'IRIS_REWARDS'
        managed = True

class Badge(models.Model):
    badge_id = models.AutoField(primary_key=True)
    badge_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon_url = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'IRIS_BADGES'
        managed = True

    def __str__(self):
        return self.badge_name

class UserBadge(models.Model):
    user = models.ForeignKey(IrisUser, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'IRIS_USER_BADGES'
        unique_together = (('user', 'badge'),)
        managed = True

class ReviewParameter(models.Model):
    parameter_id = models.AutoField(primary_key=True)
    parameter_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'IRIS_REVIEW_PARAMETERS'
        managed = True

    def __str__(self):
        return self.parameter_name

class ReviewRating(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='ratings')
    parameter = models.ForeignKey(ReviewParameter, on_delete=models.CASCADE)
    score = models.IntegerField() # e.g., 1-5

    class Meta:
        db_table = 'IRIS_REVIEW_RATINGS'
        unique_together = (('review', 'parameter'),)
        managed = True

class ImprovementCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'IRIS_IMPROVEMENT_CATEGORIES'
        managed = True

    def __str__(self):
        return self.name

class ImprovementSubCategory(models.Model):
    category = models.ForeignKey(ImprovementCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'IRIS_IMPROVEMENT_SUB_CATEGORIES'
        managed = True

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class GrassrootIdea(models.Model):
    idea_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ideator = models.ForeignKey(IrisUser, on_delete=models.CASCADE, related_name='grassroot_ideas')
    
    # Idea Details
    improvement_category = models.ForeignKey(ImprovementCategory, on_delete=models.SET_NULL, null=True)
    improvement_sub_category = models.ForeignKey(ImprovementSubCategory, on_delete=models.SET_NULL, null=True)
    
    business_value = models.TextField()
    monetary_value = models.TextField()
    proposed_idea = models.TextField()
    non_monetary_value = models.TextField()
    additional_information = models.TextField(blank=True, null=True)
    assumptions = models.TextField()
    key_risks = models.TextField()
    
    STATUS_CHOICES = [
        ('SUBMITTED_RM', 'Submitted to RM'),
        ('REWORK_RM', 'Rework Required by RM'),
        ('APPROVED_RM', 'Approved by RM'),
        ('REJECTED_RM', 'Rejected by RM'),
        ('SUBMITTED_IBU', 'Submitted to IBU'),
        ('REWORK_IBU', 'Rework Required by IBU'),
        ('APPROVED_IBU', 'Approved by IBU'),
        ('REJECTED_IBU', 'Rejected by IBU'),
        ('PENDING_CUSTOMER', 'Pending Customer Input'),
        ('COMPLETED', 'Completed'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='SUBMITTED_RM')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Customer Input Fields
    confidentiality = models.CharField(max_length=100, blank=True, null=True)
    customer_feedback = models.TextField(blank=True, null=True)
    innovation_context = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'IRIS_GRASSROOT_IDEAS'
        managed = True

    def __str__(self):
        return f"Grassroot Idea by {self.ideator.full_name}"

class GrassrootEvaluation(models.Model):
    idea = models.ForeignKey(GrassrootIdea, on_delete=models.CASCADE, related_name='evaluations')
    evaluator = models.ForeignKey(IrisUser, on_delete=models.CASCADE)
    evaluator_role = models.CharField(max_length=20) # RM or IBU
    
    is_desirable = models.BooleanField(default=False)
    is_feasible = models.BooleanField(default=False)
    is_viable = models.BooleanField(default=False)
    
    remarks = models.TextField(blank=True, null=True)
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'IRIS_GRASSROOT_EVALUATIONS'
        managed = True

class Notification(models.Model):
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(IrisUser, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(IrisUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'IRIS_NOTIFICATIONS'
        managed = True
        ordering = ['-created_at']


class UserLoginLog(models.Model):
    user = models.ForeignKey(IrisUser, on_delete=models.CASCADE)
    login_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'IRIS_USER_LOGIN_LOGS'
        managed = True
        ordering = ['-login_at']

    def __str__(self):
        return f"{self.user.full_name} logged in at {self.login_at}"

class IrisCollage(models.Model):
    collage_id = models.DecimalField(primary_key=True, max_digits=38, decimal_places=0)
    university_id = models.DecimalField(max_digits=38, decimal_places=0)
    collage_name = models.CharField(max_length=200)
    collage_description = models.CharField(max_length=2000, blank=True, null=True)
    created_by = models.CharField(max_length=200)
    created_on = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'IRIS_COLLAGE'
        verbose_name = 'Collage'
        verbose_name_plural = 'Collages'

class IrisEmployeeMaster(models.Model):
    empcode = models.CharField(primary_key=True, max_length=11)
    empname = models.CharField(max_length=100, blank=True, null=True)
    doj = models.DateTimeField(blank=True, null=True)
    emailid = models.CharField(max_length=100, blank=True, null=True)
    prev_exp = models.DecimalField(max_digits=38, decimal_places=0, blank=True, null=True)
    tm_exp = models.DecimalField(max_digits=38, decimal_places=0, blank=True, null=True)
    officercode = models.CharField(max_length=1, blank=True, null=True)
    emptitle = models.CharField(max_length=50, blank=True, null=True)
    project_id = models.CharField(max_length=20, blank=True, null=True)
    status_flag = models.CharField(max_length=1, blank=True, null=True)
    jobcode = models.CharField(max_length=10, blank=True, null=True)
    functioncode = models.CharField(max_length=30, blank=True, null=True)
    base_location = models.CharField(max_length=40, blank=True, null=True)
    current_location = models.CharField(max_length=40, blank=True, null=True)
    supervisor = models.CharField(max_length=11, blank=True, null=True)
    grade = models.CharField(max_length=5, blank=True, null=True)
    empl_status = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'IRIS_EMPLOYEE_MASTER'

class IrisLocationMaster(models.Model):
    location_id = models.CharField(primary_key=True, max_length=20)
    location_name = models.CharField(max_length=200, blank=True, null=True)
    status_flag = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'IRIS_LOCATION_MASTER'

class IrisGradeRoleMaster(models.Model):
    # Using ROLE_CODE as primary key as it's the most unique-looking field
    role_code = models.CharField(primary_key=True, max_length=20)
    category = models.CharField(max_length=200, blank=True, null=True)
    sub_band = models.CharField(max_length=200, blank=True, null=True)
    role_description = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'IRIS_GRADE_ROLE_MASTER'

class IrisMailMaster(models.Model):
    status_id = models.DecimalField(primary_key=True, max_digits=38, decimal_places=0)
    mail_subject = models.CharField(max_length=200)
    mail_body = models.CharField(max_length=4000)

    class Meta:
        managed = False
        db_table = 'IRIS_MAIL_MASTER'

class IrisClusterIbgIbu(models.Model):
    functioncode = models.CharField(primary_key=True, max_length=50)
    function_type = models.CharField(max_length=10)
    function_lg_desc = models.CharField(max_length=100)
    function_head = models.CharField(max_length=11, blank=True, null=True)
    function_gdu = models.CharField(max_length=50, blank=True, null=True)
    function_gdu_head = models.CharField(max_length=11, blank=True, null=True)
    function_sdu = models.CharField(max_length=50, blank=True, null=True)
    function_sdu_head = models.CharField(max_length=11, blank=True, null=True)
    function_status = models.CharField(max_length=1)
    function_level = models.CharField(max_length=15)
    function_evp = models.CharField(max_length=11)

    class Meta:
        managed = False
        db_table = 'IRIS_CLUSTER_IBG_IBU'
