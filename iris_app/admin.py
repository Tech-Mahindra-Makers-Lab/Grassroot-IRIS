from django.contrib import admin
from .models import (
    Role, IrisUser, UserRole, EmployeeDetail,
    Challenge, ChallengePanel, ChallengeMentor,
    Idea, IdeaDetail, IdeaCategory, IdeaCategoryMapping,
    CoIdeator, IdeaDocument,
    Review, WorkflowLog, Reward, Badge, UserBadge,
    ReviewParameter, ReviewRating, ChallengeReviewParameter,
    ImprovementCategory, ImprovementSubCategory, GrassrootIdea, GrassrootEvaluation, UserLoginLog,
    IrisCollage, IrisEmployeeMaster, IrisLocationMaster, IrisGradeRoleMaster, IrisMailMaster, IrisClusterIbgIbu, IrisRoleMs
)
from .admin_custom import ChallengeOwner, ChallengeOwnerAdmin, UserLoginLogAdmin
from import_export.admin import ImportExportModelAdmin

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'description', 'role_id')
    search_fields = ('role_name',)

@admin.register(IrisEmployeeMaster)
class IrisEmployeeMasterAdmin(ImportExportModelAdmin):
    list_display = ('empname', 'empcode', 'emailid', 'emptitle', 'grade', 'status_flag')
    search_fields = ('empname', 'empcode', 'emailid')
    list_filter = ('grade', 'status_flag')

@admin.register(IrisUser)
class IrisUserAdmin(ImportExportModelAdmin):
    list_display = ('full_name', 'email', 'user_type', 'get_roles', 'employee_master', 'created_at')
    list_filter = ('user_type', 'created_at', 'userrole__role')
    search_fields = ('full_name', 'email', 'employee_master__empcode')
    autocomplete_fields = ['employee_master']

    def get_roles(self, obj):
        return ", ".join([r.role.role_name for r in obj.userrole_set.all()])
    get_roles.short_description = 'Roles'

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__email', 'role__role_name')

@admin.register(EmployeeDetail)
class EmployeeDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_project_code', 'current_project_name', 'ibu_name')
    search_fields = ('user__email', 'current_project_code', 'current_project_name')

class ChallengeReviewParameterInline(admin.TabularInline):
    model = ChallengeReviewParameter
    extra = 1

class ChallengePanelInline(admin.TabularInline):
    model = ChallengePanel
    extra = 1

@admin.register(Challenge)
class ChallengeAdmin(ImportExportModelAdmin):
    list_display = ('title', 'status', 'start_date', 'end_date', 'visibility', 'challenge_owner')
    list_filter = ('status', 'visibility', 'target_audience', 'start_date')
    search_fields = ('title', 'description')
    inlines = [ChallengeReviewParameterInline, ChallengePanelInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'keywords', 'challenge_icon', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'round1_eval_start', 'round1_eval_end', 'round2_eval_start', 'round2_eval_end')
        }),
        ('Targeting & Visibility', {
            'fields': ('target_audience', 'visibility', 'challenge_owner', 'created_by')
        }),
        ('Insights & Outcomes', {
            'fields': ('key_insights', 'expected_outcome')
        }),
        ('Templates & Documents', {
            'fields': ('has_idea_template', 'idea_template_file', 'challenge_document')
        }),
    )

@admin.register(ChallengePanel)
class ChallengePanelAdmin(admin.ModelAdmin):
    list_display = ('panel_name', 'challenge', 'round_number')
    list_filter = ('round_number',)
    search_fields = ('panel_name',)

@admin.register(ChallengeMentor)
class ChallengeMentorAdmin(admin.ModelAdmin):
    list_display = ('panel', 'mentor')
    search_fields = ('panel__panel_name', 'mentor__email')

@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'submitter', 'status', 'sharing_scope', 'submission_date')
    list_filter = ('status', 'sharing_scope', 'submission_date', 'is_confidential')
    search_fields = ('title', 'submitter__email')

@admin.register(IdeaDetail)
class IdeaDetailAdmin(admin.ModelAdmin):
    list_display = ('idea', 'innovation_type')
    list_filter = ('innovation_type',)

@admin.register(IdeaCategory)
class IdeaCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'theme_name')
    search_fields = ('category_name', 'theme_name')

@admin.register(IdeaCategoryMapping)
class IdeaCategoryMappingAdmin(admin.ModelAdmin):
    list_display = ('idea', 'category')
    list_filter = ('category',)

@admin.register(CoIdeator)
class CoIdeatorAdmin(admin.ModelAdmin):
    list_display = ('idea', 'user')
    search_fields = ('idea__title', 'user__email')

@admin.register(IdeaDocument)
class IdeaDocumentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'idea', 'uploaded_at')
    search_fields = ('file_name', 'idea__title')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'decision', 'reviewer', 'rating', 'review_date')
    list_filter = ('entity_type', 'decision', 'rating', 'review_date')
    search_fields = ('comments', 'reviewer__email')
    inlines = [] # Will add ReviewRatingInline below

class ReviewRatingInline(admin.TabularInline):
    model = ReviewRating
    extra = 1

ReviewAdmin.inlines = [ReviewRatingInline]

@admin.register(ReviewParameter)
class ReviewParameterAdmin(ImportExportModelAdmin):
    list_display = ('parameter_name', 'is_active', 'parameter_id')
    list_filter = ('is_active',)
    search_fields = ('parameter_name',)

@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'previous_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('entity_type', 'changed_at')
    search_fields = ('remarks', 'changed_by__email')

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'reason', 'date_earned')
    search_fields = ('user__email', 'reason')

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('badge_name', 'description')
    search_fields = ('badge_name',)

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    list_filter = ('badge', 'earned_at')
    search_fields = ('user__email', 'badge__badge_name')


@admin.register(ImprovementCategory)
class ImprovementCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ImprovementSubCategory)
class ImprovementSubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(GrassrootIdea)
class GrassrootIdeaAdmin(admin.ModelAdmin):
    list_display = ('ideator', 'improvement_category', 'status', 'created_at')
    list_filter = ('status', 'improvement_category', 'created_at')
    search_fields = ('ideator__full_name', 'ideator__email')

@admin.register(GrassrootEvaluation)
class GrassrootEvaluationAdmin(admin.ModelAdmin):
    list_display = ('idea', 'evaluator', 'evaluator_role', 'evaluated_at')
    list_filter = ('evaluator_role', 'evaluated_at')

admin.site.register(ChallengeOwner, ChallengeOwnerAdmin)
admin.site.register(UserLoginLog, UserLoginLogAdmin)

@admin.register(IrisCollage)
class IrisCollageAdmin(ImportExportModelAdmin):
    list_display = ('collage_name', 'university_id', 'created_by', 'created_on')
    search_fields = ('collage_name',)

@admin.register(IrisLocationMaster)
class IrisLocationMasterAdmin(admin.ModelAdmin):
    list_display = ('location_id', 'location_name', 'status_flag')
    list_filter = ('status_flag',)

@admin.register(IrisGradeRoleMaster)
class IrisGradeRoleMasterAdmin(admin.ModelAdmin):
    list_display = ('role_code', 'role_description', 'sub_band', 'category')
    search_fields = ('role_code', 'role_description')

@admin.register(IrisMailMaster)
class IrisMailMasterAdmin(admin.ModelAdmin):
    list_display = ('status_id', 'mail_subject')
    search_fields = ('mail_subject',)

@admin.register(IrisClusterIbgIbu)
class IrisClusterIbgIbuAdmin(admin.ModelAdmin):
    list_display = ('functioncode', 'function_lg_desc', 'function_type', 'function_level')
    list_filter = ('function_type', 'function_level')

@admin.register(IrisRoleMs)
class IrisRoleMsAdmin(ImportExportModelAdmin):
    list_display = ('role_lg_desc', 'rolecode', 'grade_desc', 'job_code', 'status_flag')
    search_fields = ('role_lg_desc', 'rolecode', 'job_code')
    list_filter = ('status_flag', 'grade_desc')
