from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    IrisUserViewSet, ChallengeViewSet, IdeaViewSet,
    GrassrootIdeaViewSet, NotificationViewSet,
    ImprovementCategoryViewSet, ImprovementSubCategoryViewSet,
    ChallengePanelViewSet, ChallengeMentorViewSet,
    StatsView
)

router = DefaultRouter()
router.register(r'users', IrisUserViewSet)
router.register(r'challenges', ChallengeViewSet)
router.register(r'challenge-panels', ChallengePanelViewSet)
router.register(r'challenge-mentors', ChallengeMentorViewSet)
router.register(r'ideas', IdeaViewSet)
router.register(r'grassroot-ideas', GrassrootIdeaViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'improvement-categories', ImprovementCategoryViewSet)
router.register(r'improvement-subcategories', ImprovementSubCategoryViewSet)
router.register(r'stats', StatsView, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
]
