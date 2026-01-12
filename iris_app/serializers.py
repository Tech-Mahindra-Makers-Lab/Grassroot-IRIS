from rest_framework import serializers
from .models import (
    IrisUser, Role, UserRole, EmployeeDetail, Challenge, 
    ChallengeReviewParameter, ReviewParameter, ChallengePanel, 
    ChallengeMentor, Idea, IdeaDetail, IdeaCategory, 
    IdeaCategoryMapping, CoIdeator, IdeaDocument, Review, 
    WorkflowLog, Reward, Badge, UserBadge, ImprovementCategory, 
    ImprovementSubCategory, GrassrootIdea, GrassrootEvaluation, 
    Notification
)

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class IrisUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = IrisUser
        fields = ['user_id', 'email', 'full_name', 'user_type', 'employee_id', 'created_at']
        extra_kwargs = {'password_hash': {'write_only': True}}

class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role.role_name')
    class Meta:
        model = UserRole
        fields = ['user', 'role', 'role_name', 'assigned_at']

class EmployeeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetail
        fields = '__all__'

class ReviewParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewParameter
        fields = '__all__'

class ChallengeReviewParameterSerializer(serializers.ModelSerializer):
    parameter_name = serializers.ReadOnlyField(source='parameter.parameter_name')
    class Meta:
        model = ChallengeReviewParameter
        fields = ['challenge', 'parameter', 'parameter_name', 'weightage']

class ChallengeSerializer(serializers.ModelSerializer):
    review_parameters = ChallengeReviewParameterSerializer(many=True, read_only=True)
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    
    class Meta:
        model = Challenge
        fields = '__all__'

class ChallengePanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengePanel
        fields = '__all__'

class ChallengeMentorSerializer(serializers.ModelSerializer):
    mentor_name = serializers.ReadOnlyField(source='mentor.full_name')
    class Meta:
        model = ChallengeMentor
        fields = ['panel', 'mentor', 'mentor_name']

class IdeaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdeaDetail
        fields = '__all__'

class IdeaSerializer(serializers.ModelSerializer):
    details = IdeaDetailSerializer(source='ideadetail', read_only=True)
    submitter_name = serializers.ReadOnlyField(source='submitter.full_name')
    challenge_title = serializers.ReadOnlyField(source='challenge.title')
    
    class Meta:
        model = Idea
        fields = '__all__'

class IdeaCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IdeaCategory
        fields = '__all__'

class CoIdeatorSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    class Meta:
        model = CoIdeator
        fields = ['idea', 'user', 'user_name']

class IdeaDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdeaDocument
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.ReadOnlyField(source='reviewer.full_name')
    class Meta:
        model = Review
        fields = '__all__'

class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = '__all__'

class ImprovementCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImprovementCategory
        fields = '__all__'

class ImprovementSubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    class Meta:
        model = ImprovementSubCategory
        fields = ['id', 'category', 'category_name', 'name']

class GrassrootIdeaSerializer(serializers.ModelSerializer):
    ideator_name = serializers.ReadOnlyField(source='ideator.full_name')
    category_name = serializers.ReadOnlyField(source='improvement_category.name')
    subcategory_name = serializers.ReadOnlyField(source='improvement_sub_category.name')
    
    class Meta:
        model = GrassrootIdea
        fields = '__all__'

class GrassrootEvaluationSerializer(serializers.ModelSerializer):
    evaluator_name = serializers.ReadOnlyField(source='evaluator.full_name')
    class Meta:
        model = GrassrootEvaluation
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
