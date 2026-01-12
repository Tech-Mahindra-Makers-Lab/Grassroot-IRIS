from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import (
    IrisUser, Role, Challenge, Idea, GrassrootIdea, Notification,
    ImprovementCategory, ImprovementSubCategory, Reward,
    ChallengePanel, ChallengeMentor
)
from .serializers import (
    IrisUserSerializer, RoleSerializer, ChallengeSerializer,
    IdeaSerializer, GrassrootIdeaSerializer, NotificationSerializer,
    ImprovementCategorySerializer, ImprovementSubCategorySerializer,
    RewardSerializer, ChallengePanelSerializer, ChallengeMentorSerializer
)

class IrisUserViewSet(viewsets.ModelViewSet):
    queryset = IrisUser.objects.all()
    serializer_class = IrisUserSerializer
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = IrisUser.objects.get(email=email)
            # Simplistic check for now, in a real app use Proper Auth
            if user.password_hash.startswith('pbkdf2_sha256'):
                serializer = self.get_serializer(user)
                return Response({
                    'status': 'success',
                    'user': serializer.data
                })
            return Response({'status': 'error', 'message': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
        except IrisUser.DoesNotExist:
            return Response({'status': 'error', 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all().order_by('-created_at')
    serializer_class = ChallengeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('filter')
        query = self.request.query_params.get('q')

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(keywords__icontains=query))
        
        if status_filter == 'active':
            queryset = queryset.filter(status='LIVE')
        elif status_filter == 'draft':
            queryset = queryset.filter(status='DRAFT')
        elif status_filter == 'past':
            queryset = queryset.filter(status='COMPLETED')
            
        return queryset

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured = Challenge.objects.filter(is_featured=True).first()
        if featured:
            serializer = self.get_serializer(featured)
            return Response(serializer.data)
        return Response(status=status.HTTP_404_NOT_FOUND)

class IdeaViewSet(viewsets.ModelViewSet):
    queryset = Idea.objects.all().order_by('-submission_date')
    serializer_class = IdeaSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return self.queryset.filter(Q(submitter_id=user_id) | Q(coideator__user_id=user_id)).distinct()
        return self.queryset

class GrassrootIdeaViewSet(viewsets.ModelViewSet):
    queryset = GrassrootIdea.objects.all().order_by('-created_at')
    serializer_class = GrassrootIdeaSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return self.queryset.filter(ideator_id=user_id)
        return self.queryset

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return self.queryset.filter(recipient_id=user_id)
        return self.queryset

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

class ImprovementCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ImprovementCategory.objects.all()
    serializer_class = ImprovementCategorySerializer

class ImprovementSubCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ImprovementSubCategory.objects.all()
    serializer_class = ImprovementSubCategorySerializer
    
    def get_queryset(self):
        category_id = self.request.query_params.get('category_id')
        if category_id:
            return self.queryset.filter(category_id=category_id)
        return self.queryset

class ChallengePanelViewSet(viewsets.ModelViewSet):
    queryset = ChallengePanel.objects.all()
    serializer_class = ChallengePanelSerializer
    
    def get_queryset(self):
        challenge_id = self.request.query_params.get('challenge_id')
        if challenge_id:
            return self.queryset.filter(challenge_id=challenge_id)
        return self.queryset

class ChallengeMentorViewSet(viewsets.ModelViewSet):
    queryset = ChallengeMentor.objects.all()
    serializer_class = ChallengeMentorSerializer
    
    def get_queryset(self):
        panel_id = self.request.query_params.get('panel_id')
        if panel_id:
            return self.queryset.filter(panel_id=panel_id)
        return self.queryset

class StatsView(viewsets.ViewSet):
# ...

    def list(self, request):
        member_count = IrisUser.objects.count()
        idea_count = Idea.objects.count() + GrassrootIdea.objects.count()
        challenge_count = Challenge.objects.filter(status='LIVE').count()
        return Response({
            'member_count': member_count,
            'idea_count': idea_count,
            'challenge_count': challenge_count
        })
