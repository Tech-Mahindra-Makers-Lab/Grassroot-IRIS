from django import forms
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.http import HttpResponse
import csv
from .models import Role, IrisUser, UserRole, UserLoginLog
from django.db import models

class AddChallengeOwnerForm(forms.Form):
    employee_search = forms.CharField(required=False, label="Search Employee (Name/ID/Email)")
    bulk_emails = forms.CharField(required=False, widget=forms.Textarea, label="Bulk Emails (separated by ;)")

    def clean(self):
        cleaned_data = super().clean()
        search = cleaned_data.get("employee_search")
        bulk = cleaned_data.get("bulk_emails")
        if not search and not bulk:
            raise forms.ValidationError("Please provide either a search term or bulk emails.")
        return cleaned_data

class ChallengeOwnerAdmin(admin.ModelAdmin):
    change_list_template = "admin/challenge_owner_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add-challenge-owner/', self.admin_site.admin_view(self.add_challenge_owner_view), name='add_challenge_owner'),
        ]
        return my_urls + urls

    def add_challenge_owner_view(self, request):
        if request.method == "POST":
            form = AddChallengeOwnerForm(request.POST)
            if form.is_valid():
                search = form.cleaned_data.get("employee_search")
                bulk = form.cleaned_data.get("bulk_emails")
                
                added_count = 0
                
                # Fetch Role
                try:
                    role = Role.objects.get(role_name="Challenge Owner")
                except Role.DoesNotExist:
                    messages.error(request, "Role 'Challenge Owner' not found in DB.")
                    return redirect("..")

                # Handle Search (Mock logic for now, or simple filter)
                if search:
                    users = IrisUser.objects.filter(email__icontains=search) | IrisUser.objects.filter(full_name__icontains=search)
                    for user in users:
                        UserRole.objects.get_or_create(user=user, role=role)
                        added_count += 1
                        
                # Handle Bulk
                if bulk:
                    emails = [e.strip() for e in bulk.split(';') if e.strip()]
                    for email in emails:
                        # Find or Create user? Doc says "insert Challenge Owner details in table IRIS_USERS".
                        # Assuming user must exist or we create basic? 
                        # Let's assume we find existing or create new with minimal info
                        user, created = IrisUser.objects.get_or_create(email=email, defaults={'full_name': 'Unknown', 'password_hash': 'temp'})
                        UserRole.objects.get_or_create(user=user, role=role)
                        added_count += 1

                messages.success(request, f"Added {added_count} Challenge Owners.")
                return redirect("..")
        else:
            form = AddChallengeOwnerForm()
            
        context = dict(
           self.admin_site.each_context(request),
           form=form,
           title="Add Challenge Owner"
        )
        return render(request, "admin/add_challenge_owner.html", context)

# Re-register Role with this custom admin if focusing on Roles, 
# or maybe create a proxy model for "ChallengeOwner" management?
# Let's create a proxy model to expose this specific workflow.

class ChallengeOwnerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role__role_name="Challenge Owner")

class ChallengeOwner(UserRole):
    class Meta:
        proxy = True
        verbose_name = "Challenge Owner"
        verbose_name_plural = "Challenge Owners"


class UserLoginLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_at', 'ip_address', 'user_agent')
    list_filter = ('login_at', 'user__user_type')
    search_fields = ('user__full_name', 'user__email', 'ip_address')
    readonly_fields = ('user', 'login_at', 'ip_address', 'user_agent')
    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected to CSV"
