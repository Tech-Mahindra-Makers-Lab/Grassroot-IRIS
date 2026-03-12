from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
import csv
from .models import (
    Challenge, Idea, IrisUser, UserRole, ChallengePanel, ChallengeMentor, Role,
    ReviewParameter, ChallengeReviewParameter, Reward, IdeaDetail, CoIdeator, IdeaDocument,
    ImprovementCategory, ImprovementSubCategory, GrassrootIdea, GrassrootEvaluation, EmployeeDetail,
    Notification, UserLoginLog, IrisClusterIbgIbu, IrisEmployeeMaster, Review, ReviewRating
)
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
import datetime

def get_context_user(request):
    user_id = request.session.get('iris_user_id')
    if user_id:
        try:
            return IrisUser.objects.get(user_id=user_id)
        except IrisUser.DoesNotExist:
            pass
    return None

def send_notification(recipient, message, sender=None, link=None):
    """Helper function to create a notification."""
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        message=message,
        link=link
    )

def notification_list(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user
    notifications = Notification.objects.filter(recipient=user).order_by('-created_at')

    return render(request, 'iris_app/notifications.html', {'notifications': notifications})

def mark_notification_as_read(request, notification_id):
    user = get_context_user(request)
    if not user:
        return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=403)

    notification = get_object_or_404(Notification, notification_id=notification_id, recipient=user)
    notification.is_read = True
    notification.save()

    return JsonResponse({'status': 'success'})

def context_notifications(request):
    """Context processor to add unread notification count to templates."""
    user_id = request.session.get('iris_user_id')
    if user_id:
        try:
            user = IrisUser.objects.get(user_id=user_id)
            unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
            return {'unread_notifications_count': unread_count}
        except IrisUser.DoesNotExist:
            pass
    return {'unread_notifications_count': 0}

from django.contrib.auth.hashers import check_password, make_password

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = IrisUser.objects.get(email=email)
            if check_password(password, user.password_hash):
                # Log login event
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')

                UserLoginLog.objects.create(
                    user=user,
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )

                request.session['iris_user_id'] = str(user.user_id)
                request.session['iris_user_name'] = user.full_name
                messages.success(request, f"Welcome back, {user.full_name}!")
                return redirect('home')
            else:
                messages.error(request, "Invalid password.")
        except IrisUser.DoesNotExist:
            messages.error(request, "User not found.")

    return render(request, 'iris_app/login.html', {'hide_sidebar': True})

def logout_view(request):
    request.session.flush()
    return redirect('login')

def challenge_list(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user

    status_filter = request.GET.get('filter', 'active')
    query = request.GET.get('q', '')

    # Base queryset for the user
    challenges = Challenge.objects.all().order_by('end_date')

    # Apply Search Query FIRST (before complex joins to avoid Oracle NCLOB issues)
    if query:
        challenges = challenges.filter(models.Q(title__icontains=query) | models.Q(keywords__icontains=query))

    # Role definitions
    is_mentor = UserRole.objects.filter(user=user, role__role_name='Mentor').exists()
    print(f"User {user.full_name} roles - Mentor: {is_mentor}")  # Debug log
    is_challenge_owner = UserRole.objects.filter(user=user, role__role_name='Challenge Owner').exists()

    # Apply Role-based Base Visibility (after text search)
    if is_mentor:
        # Use subquery to get mentor's challenge IDs to avoid Oracle JOIN/NCLOB issues
        from django.db.models import Subquery
        mentor_challenges = ChallengePanel.objects.filter(
            challengementor__mentor=user
        ).values_list('challenge_id', flat=True).distinct()
        challenges = challenges.filter(challenge_id__in=mentor_challenges)
        print(f"User {user.full_name} is a mentor, filtered challenges count: {challenges.count()} ")
    elif is_challenge_owner:
        # Owners see everything they created + all LIVE challenges
        challenges = challenges.filter(models.Q(created_by=user) | models.Q(status='LIVE')).distinct()
    else:
        # Regular users/Ideators only see LIVE
        challenges = challenges.filter(status='LIVE')

    # Apply Status Filter from URL
    if status_filter == 'active':
        # Active challenges: end_date in the future and status is LIVE
        today = timezone.now().date()
        challenges = challenges.filter(status='LIVE', end_date__date__gte=today)
    elif status_filter == 'draft':
        challenges = challenges.filter(status='DRAFT')
    elif status_filter == 'past':
        # Challenges whose end_date is before today (including yesterday) are considered 'past'
        today = timezone.now().date()
        challenges = challenges.filter(end_date__date__lt=today)
    elif status_filter == 'all':
        # 'all' just respects the base visibility (e.g. owners see their drafts + live)
        pass

    featured_challenge = Challenge.objects.filter(is_featured=True).first()

    # Add user_idea_submitted info to each challenge
    user_submitted_challenges = Idea.objects.filter(submitter=user).values_list('challenge_id', flat=True)

    # Add flag to featured challenge if it exists
    if featured_challenge:
        featured_challenge.user_idea_submitted = featured_challenge.challenge_id in user_submitted_challenges

    # Convert to list and add submitted status to each challenge
    challenges_list = list(challenges)
    for challenge in challenges_list:
        challenge.user_idea_submitted = challenge.challenge_id in user_submitted_challenges
        print(f"Challenge: {challenge.title}, registration_required: '{challenge.registration_required}', user_submitted: {challenge.user_idea_submitted}")

    context = {
        'featured_challenge': featured_challenge,
        'challenges': challenges_list,
        'current_filter': status_filter,
        'query': query,
    }
    return render(request, 'iris_app/index.html', context)

def calculate_review_days(idea):
    """Helper function to calculate review days for an idea based on its challenge's panel dates"""
    try:
        if not idea.challenge:
            idea.review_days = 0
            idea.review_days_left = 0
            idea.panel_end_date = None
            return

        # Get the panel(s) associated with this challenge
        panel = ChallengePanel.objects.filter(challenge=idea.challenge).first()
        if panel and panel.start_date and panel.end_date:
            # Calculate the difference in days
            review_duration = (panel.end_date - panel.start_date).days
            idea.review_days = review_duration
            idea.panel_end_date = panel.end_date
            idea.review_days_left = (panel.end_date - timezone.now().date()).days
        else:
            idea.review_days = 0
            idea.panel_end_date = None
            idea.review_days_left = 0
    except Exception as e:
        print(f"Error calculating review days for idea {idea.title}: {str(e)}")
        idea.review_days = 0
        idea.panel_end_date = None
        idea.review_days_left = 0


def review_dashboard(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user

    # Only show ideas for challenges where the current user is assigned as evaluator (ChallengePanel.emailid)
    user_email = user.email
    from django.db.models import Exists, OuterRef
    # Find all panels assigned to this user
    assigned_panels = ChallengePanel.objects.filter(emailid=user_email)
    assigned_challenge_ids = assigned_panels.values_list('challenge_id', flat=True)

    # Determine if user is first or second reviewer (by round_number)
    first_panel_challenge_ids = assigned_panels.filter(round_number=1).values_list('challenge_id', flat=True)
    second_panel_challenge_ids = assigned_panels.filter(round_number=2).values_list('challenge_id', flat=True)

    first_review_exists = Review.objects.filter(entity_type='IDEA', entity_id=OuterRef('idea_id'), stage='FIRST EVALUATION')

    # For first reviewer: show ideas where first review is NOT done
    first_reviewer_ideas = Idea.objects.select_related('submitter', 'challenge').prefetch_related('ideadetail')\
        .filter(challenge_id__in=first_panel_challenge_ids)\
        .annotate(first_review_done=Exists(first_review_exists))\
        .filter(first_review_done=False)\
        .order_by('-submission_date')

    # For second reviewer: show ideas where first review IS done
    second_reviewer_ideas = Idea.objects.select_related('submitter', 'challenge').prefetch_related('ideadetail')\
        .filter(challenge_id__in=second_panel_challenge_ids)\
        .annotate(first_review_done=Exists(first_review_exists))\
        .filter(first_review_done=True)\
        .order_by('-submission_date')

    # Combine both sets as a queryset (PENDING IDEAS - not yet reviewed by current user)
    pending_ideas = first_reviewer_ideas | second_reviewer_ideas

    # Get reviewed ideas - Ideas already reviewed by current user
    reviewed_idea_ids = Review.objects.filter(
        reviewer=user,
        entity_type='IDEA'
    ).values_list('entity_id', flat=True)

    reviewed_ideas = Idea.objects.filter(
        idea_id__in=reviewed_idea_ids
    ).select_related('submitter', 'challenge').prefetch_related('ideadetail').order_by('-submission_date')

    # Check if we have any challenges with Arena or Pulse keywords
    arena_challenge_ids = Challenge.objects.filter(keywords__icontains='Arena').values_list('challenge_id', flat=True)
    pulse_challenge_ids = Challenge.objects.filter(keywords__icontains='Pulse').values_list('challenge_id', flat=True)

    # PENDING IDEAS - Separate by challenge type
    pending_arena_ideas = pending_ideas.filter(challenge_id__in=arena_challenge_ids)
    pending_pulse_ideas = pending_ideas.filter(challenge_id__in=pulse_challenge_ids)

    # REVIEWED IDEAS - Separate by challenge type
    reviewed_arena_ideas = reviewed_ideas.filter(challenge_id__in=arena_challenge_ids)
    reviewed_pulse_ideas = reviewed_ideas.filter(challenge_id__in=pulse_challenge_ids)

    # Debug: Print counts
    print(f"Arena challenges: {arena_challenge_ids.count()}, Pulse challenges: {pulse_challenge_ids.count()}")
    print(f"Pending Arena ideas: {pending_arena_ideas.count()}, Pending Pulse ideas: {pending_pulse_ideas.count()}")
    print(f"Reviewed Arena ideas: {reviewed_arena_ideas.count()}, Reviewed Pulse ideas: {reviewed_pulse_ideas.count()}")

    # If no challenges tagged with Arena or Pulse, use all for Arena and leave Pulse empty
    if not arena_challenge_ids.exists() and not pulse_challenge_ids.exists():
        # Fallback: If no keyword-based challenges exist, show all in Arena
        pending_arena_ideas = list(pending_ideas)
        pending_pulse_ideas = Idea.objects.none()
        reviewed_arena_ideas = list(reviewed_ideas)
        reviewed_pulse_ideas = Idea.objects.none()

        # Parse keywords and calculate review days
        for idea in pending_arena_ideas:
            if idea.ideadetail and idea.ideadetail.keywords:
                idea.keywords_list = [kw.strip() for kw in idea.ideadetail.keywords.split(',')][:3]
            else:
                idea.keywords_list = []
            calculate_review_days(idea)

        for idea in reviewed_arena_ideas:
            if idea.ideadetail and idea.ideadetail.keywords:
                idea.keywords_list = [kw.strip() for kw in idea.ideadetail.keywords.split(',')][:3]
            else:
                idea.keywords_list = []
            calculate_review_days(idea)
    else:
        # Convert to lists for template rendering
        pending_arena_ideas = list(pending_arena_ideas)
        pending_pulse_ideas = list(pending_pulse_ideas)
        reviewed_arena_ideas = list(reviewed_arena_ideas)
        reviewed_pulse_ideas = list(reviewed_pulse_ideas)

        # Parse keywords and calculate review days for pending ideas
        for idea in pending_arena_ideas:
            if idea.ideadetail and idea.ideadetail.keywords:
                idea.keywords_list = [kw.strip() for kw in idea.ideadetail.keywords.split(',')][:3]
            else:
                idea.keywords_list = []
            calculate_review_days(idea)

        for idea in pending_pulse_ideas:
            if idea.ideadetail and idea.ideadetail.keywords:
                idea.keywords_list = [kw.strip() for kw in idea.ideadetail.keywords.split(',')][:3]
            else:
                idea.keywords_list = []
            calculate_review_days(idea)

        # Parse keywords and calculate review days for reviewed ideas
        for idea in reviewed_arena_ideas:
            if idea.ideadetail and idea.ideadetail.keywords:
                idea.keywords_list = [kw.strip() for kw in idea.ideadetail.keywords.split(',')][:3]
            else:
                idea.keywords_list = []
            calculate_review_days(idea)

        for idea in reviewed_pulse_ideas:
            if idea.ideadetail and idea.ideadetail.keywords:
                idea.keywords_list = [kw.strip() for kw in idea.ideadetail.keywords.split(',')][:3]
            else:
                idea.keywords_list = []
            calculate_review_days(idea)

    # Calculate statistics for pending ideas
    pending_total = pending_ideas.count()
    pending_count = pending_ideas.filter(status='SUBMITTED').count()

    # Calculate statistics for reviewed ideas
    reviewed_total = reviewed_ideas.count()
    reviewed_approved_count = reviewed_ideas.filter(status='APPROVED').count()
    reviewed_rejected_count = reviewed_ideas.filter(status='REJECTED').count()

    # Convert querysets to lists and calculate review days for All Submissions tab
    pending_ideas = list(pending_ideas)
    reviewed_ideas = list(reviewed_ideas)

    for idea in pending_ideas:
        calculate_review_days(idea)

    for idea in reviewed_ideas:
        calculate_review_days(idea)

    context = {
        # Pending ideas (not yet reviewed by current user)
        'pending_ideas': pending_ideas,
        'pending_arena_ideas': pending_arena_ideas,
        'pending_pulse_ideas': pending_pulse_ideas,
        'pending_total': pending_total,
        'pending_count': pending_count,

        # Reviewed ideas (already reviewed by current user)
        'reviewed_ideas': reviewed_ideas,
        'reviewed_arena_ideas': reviewed_arena_ideas,
        'reviewed_pulse_ideas': reviewed_pulse_ideas,
        'reviewed_total': reviewed_total,
        'reviewed_approved_count': reviewed_approved_count,
        'reviewed_rejected_count': reviewed_rejected_count,
    }
    return render(request, 'iris_app/review_dashboard.html', context)


def idea_detail(request, idea_id):
    """Display comprehensive details of a single idea"""
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user

    try:
        # Fetch idea with all related objects
        idea = Idea.objects.select_related(
            'submitter', 'challenge'
        ).prefetch_related(
            'ideacategorymapping_set__category'
        ).get(idea_id=idea_id)
    except Idea.DoesNotExist:
        messages.error(request, "Idea not found.")
        return redirect('review_dashboard')

    # Get the IdeaDetail object
    try:
        idea_detail = IdeaDetail.objects.get(idea=idea)
    except IdeaDetail.DoesNotExist:
        idea_detail = None

    # Parse keywords and technology (they are stored as text, may need parsing)
    keywords = []
    if idea_detail and idea_detail.keywords:
        # Split by comma if stored as comma-separated
        keywords = [k.strip() for k in idea_detail.keywords.split(',') if k.strip()]

    technologies = []
    if idea_detail and idea_detail.technology:
        # Split by comma if stored as comma-separated
        technologies = [t.strip() for t in idea_detail.technology.split(',') if t.strip()]

    # Get category mappings
    category_mappings = idea.ideacategorymapping_set.all()

    context = {
        'idea': idea,
        'submitter': idea.submitter,
        'challenge': idea.challenge,
        'idea_detail': idea_detail,
        'keywords': keywords,
        'technologies': technologies,
        'category_mappings': category_mappings,
    }

    # If AJAX request (from slide panel), return fragment only (no base template)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'iris_app/review_idea_detail_fragment.html', context)

    return render(request, 'iris_app/review_idea_detail.html', context)


def reviewer_idea_page(request, idea_id):
    """Display evaluator remark/evaluation page for an idea"""
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user

    try:
        # Fetch idea with all related objects
        idea = Idea.objects.select_related(
            'submitter', 'challenge'
        ).prefetch_related(
            'ideadetail'
        ).get(idea_id=idea_id)
    except Idea.DoesNotExist:
        messages.error(request, "Idea not found.")
        return redirect('review_dashboard')

    # Get the IdeaDetail object
    try:
        idea_detail = IdeaDetail.objects.get(idea=idea)
    except IdeaDetail.DoesNotExist:
        idea_detail = None

    # Get review parameters for the challenge
    review_params = ChallengeReviewParameter.objects.filter(
        challenge=idea.challenge
    ).select_related('parameter').order_by('-weightage')

    # Parse submission date
    submission_date = idea.submission_date.strftime('%d/%m/%Y') if idea.submission_date else 'N/A'

    # Fetch assessment history (all previous reviews for this idea)
    assessment_history = Review.objects.filter(
        entity_type='IDEA',
        entity_id=idea_id
    ).select_related('reviewer').prefetch_related('ratings__parameter').order_by('-review_date')

    # Check if this is a second evaluator and if first evaluator has completed
    first_evaluator_review = Review.objects.filter(
        entity_type='IDEA',
        entity_id=idea_id,
        stage='FIRST EVALUATION'
    ).first()

    # Determine current evaluator's visibility based on stage
    can_evaluate = True
    current_review = Review.objects.filter(
        entity_type='IDEA',
        entity_id=idea_id,
        reviewer=user
    ).first()

    # Check if this is first or second evaluator workflow
    # is_first_evaluator = True when there's no completed first evaluation yet
    is_first_evaluator = (first_evaluator_review is None)

    print(f"DEBUG: first_evaluator_review={first_evaluator_review}, is_first_evaluator={is_first_evaluator}")

    if first_evaluator_review and first_evaluator_review.reviewer != user:
        # Second evaluator - can proceed
        current_stage = 'SECOND EVALUATION'
    elif is_first_evaluator:
        # First evaluator
        current_stage = 'FIRST EVALUATION'
    else:
        current_stage = 'COMPLETED' if current_review else 'PENDING'

    context = {
        'idea': idea,
        'idea_detail': idea_detail,
        'submitter': idea.submitter,
        'challenge': idea.challenge,
        'review_parameters': review_params,
        'submission_date': submission_date,
        'assessment_history': assessment_history,
        'current_stage': current_stage,
        'is_first_evaluator': is_first_evaluator,
        'can_evaluate': can_evaluate,
    }

    # If AJAX request (from slide panel), return fragment only (no base template)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'iris_app/evaluator_remark_fragment.html', context)

    return render(request, 'iris_app/evaluator_remark.html', context)



@transaction.atomic
def submit_evaluation(request, idea_id):
    """Handle evaluation form submission for an idea"""
    user = get_context_user(request)
    if not user:
        return redirect('login')

    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('review_dashboard')

    try:
        idea = Idea.objects.get(idea_id=idea_id)
    except Idea.DoesNotExist:
        messages.error(request, "Idea not found.")
        return redirect('review_dashboard')

    # Extract form data
    remarks = request.POST.get('remarks', '')
    rating = request.POST.get('rating', 0)

    # Validate required fields
    if not remarks or not remarks.strip():
        messages.error(request, "Remarks are required.")
        return redirect('reviewer_idea_page', idea_id=idea_id)

    if not rating:
        messages.error(request, "Rating is required.")
        return redirect('reviewer_idea_page', idea_id=idea_id)

    try:
        # Determine the stage for this evaluation
        first_evaluation_exists = Review.objects.filter(
            entity_type='IDEA',
            entity_id=idea_id,
            stage='FIRST EVALUATION'
        ).exists()

        # Set stage based on existing evaluations
        if first_evaluation_exists:
            stage = 'SECOND EVALUATION'
        else:
            stage = 'FIRST EVALUATION'

        # Calculate decision based on rating
        rating_int = int(rating) if rating else 0
        decision = 'APPROVE' if rating_int >= 3 else 'REJECT'

        # Create a Review record with the evaluation
        review = Review.objects.create(
            entity_type='IDEA',
            entity_id=idea_id,
            reviewer=user,
            rating=rating_int,
            comments=remarks,
            stage=stage,
            decision=decision
        )
        print(f"Review created successfully: {review.review_id} with stage: {stage}")

        # Create ReviewRating records for each parameter score
        rating_count = 0
        for key, value in request.POST.items():
            if key.startswith('param_score_'):
                try:
                    param_id = int(key.replace('param_score_', ''))
                    score = int(value) if value else 0

                    # Validate score range
                    if 0 <= score <= 5:
                        parameter = ReviewParameter.objects.get(parameter_id=param_id)
                        ReviewRating.objects.create(
                            review=review,
                            parameter=parameter,
                            score=score
                        )
                        rating_count += 1
                        print(f"ReviewRating created for parameter {param_id}: score {score}")
                except (ValueError, ReviewParameter.DoesNotExist) as e:
                    # Skip invalid parameter scores
                    print(f"Skipped invalid parameter {key}: {str(e)}")
                    continue

        print(f"Total ratings created: {rating_count}")

        # Send notification to idea submitter
        send_notification(
            recipient=idea.submitter,
            message=f"Your idea '{idea.title}' has been reviewed.",
            sender=user,
            link=f'/review-dashboard/idea-detail/{idea_id}/'
        )

        messages.success(request, "Evaluation submitted successfully!")
        return redirect('review_dashboard')

    except Exception as e:
        import traceback
        print(f"Error submitting evaluation: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"Error submitting evaluation: {str(e)}")
        return redirect('reviewer_idea_page', idea_id=idea_id)


def challenge_detail(request, challenge_id):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user
    challenge = get_object_or_404(Challenge, challenge_id=challenge_id)

    # Check permissions (basic)
    is_mentor = ChallengeMentor.objects.filter(panel__challenge=challenge, mentor=user).exists()
    is_owner = (challenge.created_by == user or challenge.challenge_owner == user)

    if challenge.status != 'LIVE' and not (is_owner or user.user_type == 'INTERNAL'):
        messages.error(request, "Access denied.")
        return redirect('challenge_list')

    # Check if user has already submitted an idea for this challenge
    user_idea_submitted = Idea.objects.filter(challenge=challenge, submitter=user).exists()

    context = {
        'challenge': challenge,
        'review_params': challenge.review_parameters.all(),
        'is_mentor': is_mentor,
        'is_owner': is_owner,
        'user_idea_submitted': user_idea_submitted,
    }
    return render(request, 'iris_app/challenge_detail.html', context)

def home_landing(request):
    user = get_context_user(request)
    # Don't redirect to login, allow public access

    if user:
        request.iris_user = user

    # Fetch real stats
    member_count = IrisUser.objects.count()
    idea_count = Idea.objects.count() + GrassrootIdea.objects.count()
    challenge_count = Challenge.objects.filter(status='LIVE').count()

    featured_challenge = Challenge.objects.filter(is_featured=True).first()

    context = {
        'member_count': member_count,
        'idea_count': idea_count,
        'challenge_count': challenge_count,
        'featured_challenge': featured_challenge,
        'is_landing': True,
        'hide_sidebar': True,
    }
    return render(request, 'iris_app/home_landing.html', context)

def challenge_suggestions(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)

    suggestions = Challenge.objects.filter(title__icontains=query).values('title')[:5]
    return JsonResponse(list(suggestions), safe=False)

def ibu_search(request):
    query = request.GET.get('q', '')
    print(f"IBU Search Query: '{query}'")  # Debug log
    if len(query) < 2:
        return JsonResponse({'results': []})

    # Search for IBU records with case-insensitive matching
    ibus = IrisClusterIbgIbu.objects.filter(
        models.Q(function_lg_desc__icontains=query) & models.Q(function_type__iexact='IBU')
    ).values_list('function_lg_desc', flat=True).distinct()[:20]

    # If no results found with 'IBU', try without function_type filter to debug
    if not ibus:
        ibus = IrisClusterIbgIbu.objects.filter(
            function_lg_desc__icontains=query
        ).values_list('function_lg_desc', flat=True).distinct()[:20]

    return JsonResponse({'results': [{'id': name, 'text': name} for name in ibus]})


def employee_search(request):
    query = request.GET.get('q', '')
    print(f"Employee Search Query: '{query}'")

    if len(query) < 2:
        return JsonResponse({'results': []})

    emp_search = IrisEmployeeMaster.objects.filter(
        models.Q(empname__icontains=query)
    ).values_list('empcode', 'empname', 'emailid').distinct()[:20]

    return JsonResponse({
        'results': [
            {
                'id': empcode,
                'text': f"{empname} ({empcode})",
                'employee_id': empcode,
                'employee_name': empname,
                'email': emailid
            }
            for empcode, empname, emailid in emp_search
        ]
    })
@transaction.atomic
def post_challenge(request):
    #import pdb; pdb.set_trace()
    print("request.method:", request)
    user = get_context_user(request)
    if not user or not user.is_challenge_owner:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Access denied.'})
        messages.error(request, "Access denied. Only Challenge Owners can post challenges.")
        return redirect('challenge_list')

    request.iris_user = user
    review_parameters = ReviewParameter.objects.filter(is_active=True)

    # Check if editing an existing challenge
    edit_challenge_id = request.GET.get('edit')
    edit_challenge = None
    challenge_data = {}

    if edit_challenge_id:
        try:
            edit_challenge = Challenge.objects.get(challenge_id=edit_challenge_id, created_by=user)
            # Prepare challenge data for pre-filling form
            challenge_data = {
                'challenge': edit_challenge,
                'panels': ChallengePanel.objects.filter(challenge=edit_challenge).order_by('round_number'),
                'review_params': ChallengeReviewParameter.objects.filter(challenge=edit_challenge)
            }
        except Challenge.DoesNotExist:
            messages.error(request, "Challenge not found or you don't have permission to edit it.")
            return redirect('challenge_list')

    if request.method == 'POST':
        # Step 1 & 2 & 4 Core Data
        title = request.POST.get('title')

        description = request.POST.get('description')
        ibu_name = request.POST.get('ibu_name')
        keywords = request.POST.get('keywords')
        start_date_str = request.POST.get('chan_start_date')
        end_date_str = request.POST.get('chan_end_date')
        target_audience = request.POST.get('target_audience')
        visibility = request.POST.get('visibility')
        expected_outcome = request.POST.get('expected_outcome')
        round1_eval_criteria = request.POST.get('round1_eval_criteria')
        num_rounds = request.POST.get('num_rounds', '1')

        # Get the challenge status from the form
        challenge_status = request.POST.get('challenge_status', 'LIVE')

        # New fields: Registration Required, Participation Type, Max Team Size
        registration_required = request.POST.get('registration_required')
        participation_type = request.POST.get('participation_type')
        max_team_size = request.POST.get('max_team_size')

        # Get challenge_id for editing
        challenge_id_to_edit = request.POST.get('challenge_id_edit')

        print(f"Received POST data: title={title}, ibu_name={ibu_name}, start_date={start_date_str}, end_date={end_date_str}, num_rounds={num_rounds}, registration_required={registration_required}, participation_type={participation_type}, max_team_size={max_team_size}, challenge_status={challenge_status}")

        # Files
       # challenge_icon = request.FILES.get('challenge_icon')
        challenge_doc = request.FILES.get('challenge_document')

        try:
            # Validate that dates are provided
            if not start_date_str or not end_date_str:
                return JsonResponse({'status': 'error', 'message': 'Start date and end date are required.'})

            # Parse dates
            start_date = timezone.make_aware(datetime.datetime.strptime(start_date_str, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.datetime.strptime(end_date_str, '%Y-%m-%d'))

            # Determine the status to save - use DRAFT if selected, otherwise LIVE
            save_status = 'DRAFT' if challenge_status == 'DRAFT' else 'LIVE'

            # Create or Update Challenge
            if challenge_id_to_edit:
                # Editing existing challenge
                challenge = Challenge.objects.get(challenge_id=challenge_id_to_edit, created_by=user)
                challenge.title = title
                challenge.description = description
                challenge.ibu_name = ibu_name
                challenge.keywords = keywords
                challenge.start_date = start_date
                challenge.end_date = end_date
                challenge.target_audience = target_audience
                challenge.visibility = visibility
                challenge.expected_outcome = expected_outcome
                challenge.round1_eval_criteria = round1_eval_criteria
                challenge.num_rounds = int(num_rounds)
                challenge.registration_required = registration_required
                challenge.participation_type = participation_type
                challenge.max_team_size = int(max_team_size) if max_team_size else None
                if challenge_doc:
                    challenge.challenge_document = challenge_doc
                challenge.status = save_status
                challenge.save()

                # Delete old panels and review parameters
                ChallengePanel.objects.filter(challenge=challenge).delete()
                ChallengeReviewParameter.objects.filter(challenge=challenge).delete()
            else:
                # Creating new challenge
                challenge = Challenge.objects.create(
                    title=title,
                    description=description,
                    ibu_name=ibu_name,
                    keywords=keywords,
                    start_date=start_date,
                    end_date=end_date,
                    target_audience=target_audience,
                    visibility=visibility,
                    expected_outcome=expected_outcome,
                    round1_eval_criteria=round1_eval_criteria,
                    num_rounds=int(num_rounds),
                    registration_required=registration_required,
                    participation_type=participation_type,
                    max_team_size=int(max_team_size) if max_team_size else None,
                   # challenge_icon=challenge_icon,
                    challenge_document=challenge_doc,
                    created_by=user,
                    status=save_status
                )

            # Step 3: Review Parameters
            # Read selected parameter IDs and weightages from the table
            selected_param_ids = request.POST.getlist('selected_params[]')
            param_weightages = request.POST.getlist('param_weightages[]')

            for param_id, weightage in zip(selected_param_ids, param_weightages):
                if param_id and weightage:
                    try:
                        # Get the parameter by ID
                        param_obj = ReviewParameter.objects.get(parameter_id=param_id)
                        # Create ChallengeReviewParameter record
                        ChallengeReviewParameter.objects.create(
                            challenge=challenge,
                            parameter=param_obj,
                            weightage=int(weightage)
                        )
                    except ReviewParameter.DoesNotExist:
                        print(f"Parameter with ID {param_id} not found")

            # Step 2: Create ChallengePanel for Round 1 with evaluator details
            round1_emp_name = request.POST.get('round1_employee_name')
            round1_emp_email = request.POST.get('round1_employee_email')
            round1_emp_id = request.POST.get('round1_employee_id')
            round1_start_date_str = request.POST.get('round1_start_date')
            round1_end_date_str = request.POST.get('round1_end_date')

            if round1_emp_name and round1_emp_email and round1_emp_id:
                round1_start = datetime.datetime.strptime(round1_start_date_str, '%Y-%m-%d').date() if round1_start_date_str else None
                round1_end = datetime.datetime.strptime(round1_end_date_str, '%Y-%m-%d').date() if round1_end_date_str else None

                round1_panel = ChallengePanel.objects.create(
                    challenge=challenge,
                    panel_name=round1_emp_name,  # Employee name
                    emp_id=round1_emp_id,  # Employee ID
                    emailid=round1_emp_email,  # Email ID
                    start_date=round1_start,
                    end_date=round1_end,
                    round_number=1
                )

                # Add mentor for Round 1 panel using the evaluator email
                try:
                    mentor = IrisUser.objects.get(email=round1_emp_email)
                    ChallengeMentor.objects.create(
                        panel=round1_panel,
                        mentor=mentor
                    )
                    print(f"ChallengeMentor created for Round 1: panel_id={round1_panel.panel_id}, mentor={mentor.full_name}")
                except IrisUser.DoesNotExist:
                    print(f"Mentor with email {round1_emp_email} not found in the system")

            # Step 2: Create ChallengePanel for Round 2 (if applicable) with evaluator details
            if int(num_rounds) == 2:
                round2_emp_name = request.POST.get('round2_employee_name')
                round2_emp_email = request.POST.get('round2_employee_email')
                round2_emp_id = request.POST.get('round2_employee_id')
                round2_start_date_str = request.POST.get('round2_start_date')
                round2_end_date_str = request.POST.get('round2_end_date')

                if round2_emp_name and round2_emp_email and round2_emp_id:
                    round2_start = datetime.datetime.strptime(round2_start_date_str, '%Y-%m-%d').date() if round2_start_date_str else None
                    round2_end = datetime.datetime.strptime(round2_end_date_str, '%Y-%m-%d').date() if round2_end_date_str else None

                    round2_panel = ChallengePanel.objects.create(
                        challenge=challenge,
                        panel_name=round2_emp_name,  # Employee name
                        emp_id=round2_emp_id,  # Employee ID
                        emailid=round2_emp_email,  # Email ID
                        start_date=round2_start,
                        end_date=round2_end,
                        round_number=2
                    )

                    # Add mentor for Round 2 panel using the evaluator email
                    try:
                        mentor = IrisUser.objects.get(email=round2_emp_email)
                        ChallengeMentor.objects.create(
                            panel=round2_panel,
                            mentor=mentor
                        )
                        print(f"ChallengeMentor created for Round 2: panel_id={round2_panel.panel_id}, mentor={mentor.full_name}")
                    except IrisUser.DoesNotExist:
                        print(f"Mentor with email {round2_emp_email} not found in the system")

            return JsonResponse({'status': 'success', 'challenge_id': str(challenge.challenge_id)})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Also fetch all challenge owners to be potential mentors/reviewers
    challenge_owners = IrisUser.objects.filter(userrole__role__role_name='Challenge Owner').distinct()

    return render(request, 'iris_app/post_challenge.html', {
        'review_parameters': review_parameters,
        'challenge_owners': challenge_owners,
        'edit_challenge': edit_challenge,
        'challenge_data': challenge_data
    })

def manage_panels(request, challenge_id):
    user = get_context_user(request)
    if not user or not user.is_challenge_owner:
        return redirect('challenge_list')

    request.iris_user = user
def manage_panels(request, challenge_id):
    user = get_context_user(request)
    if not user or not user.is_challenge_owner:
        messages.error(request, "Access denied.")
        return redirect('challenge_list')

    challenge = get_object_or_404(Challenge, challenge_id=challenge_id)
    round1_panels = ChallengePanel.objects.filter(challenge=challenge, round_number=1)
    round2_panels = ChallengePanel.objects.filter(challenge=challenge, round_number=2)

    if request.method == 'POST':
        if 'add_panel' in request.POST:
            round_num = int(request.POST.get('round_number'))
            panel_name = request.POST.get('panel_name')
            description = request.POST.get('description')

            # Count limits
            current_count = ChallengePanel.objects.filter(challenge=challenge, round_number=round_num).count()
            if round_num == 1 and current_count >= 3:
                messages.error(request, "Round 1 cannot have more than 3 panels.")
            elif round_num == 2 and current_count >= 2:
                messages.error(request, "Round 2 cannot have more than 2 panels.")
            else:
                ChallengePanel.objects.create(
                    challenge=challenge,
                    panel_name=panel_name,
                    description=description,
                    round_number=round_num
                )
                messages.success(request, f"Panel added to Round {round_num}.")
                return redirect('manage_panels', challenge_id=challenge_id)

        elif 'delete_panel' in request.POST:
            panel_id = request.POST.get('panel_id')
            panel = get_object_or_404(ChallengePanel, panel_id=panel_id, challenge=challenge)
            panel.delete()
            messages.success(request, "Panel deleted.")
            return redirect('manage_panels', challenge_id=challenge_id)

    return render(request, 'iris_app/manage_panels.html', {
        'challenge': challenge,
        'round1_panels': round1_panels,
        'round2_panels': round2_panels
    })

def manage_mentors(request, challenge_id):
    user = get_context_user(request)
    if not user or not user.is_challenge_owner:
        messages.error(request, "Access denied.")
        return redirect('challenge_list')

    challenge = get_object_or_404(Challenge, challenge_id=challenge_id)
    panels = ChallengePanel.objects.filter(challenge=challenge).order_by('round_number')

    if request.method == 'POST':
        if 'add_mentor' in request.POST:
            panel_id = request.POST.get('panel_id')
            email = request.POST.get('mentor_email')
            panel = get_object_or_404(ChallengePanel, panel_id=panel_id, challenge=challenge)

            try:
                mentor = IrisUser.objects.get(email=email)
                # Check if it's already in this panel
                if ChallengeMentor.objects.filter(panel=panel, mentor=mentor).exists():
                    messages.warning(request, f"{mentor.full_name} is already in this panel.")
                else:
                    ChallengeMentor.objects.create(panel=panel, mentor=mentor)
                    messages.success(request, f"Mentor {mentor.full_name} added to {panel.panel_name}.")
                    # Notify Mentor
                    send_notification(
                        recipient=mentor,
                        message=f"You have been assigned as a mentor for the challenge: {challenge.title} in panel: {panel.panel_name}.",
                        sender=user,
                        link='/challenges/'
                    )
            except IrisUser.DoesNotExist:
                messages.error(request, f"User with email {email} not found.")
            return redirect('manage_mentors', challenge_id=challenge_id)

        elif 'delete_mentor' in request.POST:
            panel_id = request.POST.get('panel_id')
            mentor_id = request.POST.get('mentor_id')
            panel_mentor = get_object_or_404(ChallengeMentor, panel_id=panel_id, mentor_id=mentor_id)
            panel_mentor.delete()
            messages.success(request, "Mentor removed.")
            return redirect('manage_mentors', challenge_id=challenge_id)

    # Enhance panels with their mentors for display
    for p in panels:
        p.mentors = ChallengeMentor.objects.filter(panel=p)

    return render(request, 'iris_app/manage_mentors.html', {
        'challenge': challenge,
        'panels': panels
    })

def submit_challenge(request, challenge_id):
    user = get_context_user(request)
    if not user or not user.is_challenge_owner:
        messages.error(request, "Access denied.")
        return redirect('challenge_list')

    challenge = get_object_or_404(Challenge, challenge_id=challenge_id, created_by=user)

    # Final validation
    r1_panels = list(ChallengePanel.objects.filter(challenge=challenge, round_number=1))
    r2_panels = list(ChallengePanel.objects.filter(challenge=challenge, round_number=2))

    if len(r1_panels) < 2 or len(r2_panels) < 1:
        messages.error(request, "Step 2 Incomplete: Please add at least 2 panels for Round 1 and 1 for Round 2.")
        return redirect('manage_panels', challenge_id=challenge_id)

    # Check Step 3
    all_panels = r1_panels + r2_panels
    for p in all_panels:
        if not ChallengeMentor.objects.filter(panel=p).exists():
            messages.error(request, f"Step 3 Incomplete: Panel '{p.panel_name}' has no mentors.")
            return redirect('manage_mentors', challenge_id=challenge_id)

    challenge.status = 'LIVE'
    challenge.save()

    messages.success(request, f"Challenge '{challenge.title}' is now LIVE! Emails sent to target audience.")
    return redirect('challenge_list')

def idea_details(request, challenge_id):
    """Display challenge details for idea submission"""
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user
    challenge = get_object_or_404(Challenge, challenge_id=challenge_id)

    # Check if ideation is open (basic check)
    now = timezone.now()
    if challenge.status != 'LIVE':
        messages.error(request, "Ideation is not open for this challenge.")
        return redirect('challenge_list')

    # Get review parameters for this challenge from ChallengeReviewParameter
    review_params = ChallengeReviewParameter.objects.filter(
        challenge_id=challenge_id
    ).select_related('parameter').order_by('-weightage')

    # Process keywords - split by comma if they exist
    keywords_list = []
    if challenge.keywords:
        keywords_list = [kw.strip() for kw in challenge.keywords.split(',')]

    context = {
        'challenge': challenge,
        'review_parameters': review_params,
        'keywords_list': keywords_list,
    }
    return render(request, 'iris_app/ideadetails.html', context)

def submit_idea(request, challenge_id):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    challenge = get_object_or_404(Challenge, challenge_id=challenge_id)

    # Check if ideation is open (basic check)
    now = timezone.now()
    if challenge.status != 'LIVE':
        messages.error(request, "Ideation is not open for this challenge.")
        return redirect('challenge_list')

    # Fetch employee details for the logged-in user
    employee_detail = EmployeeDetail.objects.filter(user=user).first()

    # Extract employee information to display and use on form
    empcode = user.employee_id
    empname = user.full_name
    emailid = user.email
    ibu_name = None
    service_line = None

    # if employee_detail:
    #     # Get employee master information if available
    #     if employee_detail.user.employee_master:
    #         empcode = employee_detail.user.employee_master.employee_id
    #         empname = employee_detail.user.employee_master.full_name
    #     ibu_name = employee_detail.ibu_name
    #     service_line = employee_detail.service_line

    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            is_confidential = request.POST.get('is_confidential') == 'on'
            sharing_scope = request.POST.get('sharing_scope', 'NONE')
            improvement_category = request.POST.get('improvement_category')
            improvement_theme = request.POST.get('improvement_theme')

            # IdeaDetail fields - Get ALL Step 2 fields
            problem_statement = request.POST.get('problem_statement')
            proposed_solution = request.POST.get('description')

            # Keywords - Collect from keywords field (comma-separated or similar)
            keywords_detail = request.POST.getlist('keywords')
            keywords = ', '.join(keywords_detail) if keywords_detail else ''
            # Technology/Tools - Collect all tool inputs and join them
            tools_list = request.POST.getlist('tools')
            technology = ', '.join(tools_list) if tools_list else ''

            # Monetary value from form
            monetary_value = request.POST.get('monetary_value')

            # Business value description
            business_value_monetary = request.POST.get('business_value_monetary')

            # Additional fields
            assumptions = request.POST.get('assumptions')
            risks = request.POST.get('risks')
            context = request.POST.get('context')
            innovation_type = request.POST.get('innovation_type')

            print(f"Received idea submission: title={title}, empcode={empcode}, empname={empname}, emailid={emailid}, ibu_name={ibu_name}, service_line={service_line}, is_confidential={is_confidential}, sharing_scope={sharing_scope}, improvement_category={improvement_category}, improvement_theme={improvement_theme}")
            print(f"IdeaDetail: problem_statement={problem_statement}, proposed_solution={proposed_solution}, keywords={keywords_detail}, technology={technology}, monetary_value={monetary_value}, business_value_monetary={business_value_monetary}, assumptions={assumptions}, risks={risks}, context={context}, innovation_type={innovation_type}")
            # 1. Create Idea with employee information
            idea = Idea.objects.create(
                title=title,
                submitter=user,
                challenge=challenge,
                status='SUBMITTED',
                empcode=empcode,
                empname=empname,
                emailid=emailid,
                ibu_name=ibu_name,
                service_line=service_line,
                is_confidential=is_confidential,
                sharing_scope=sharing_scope,
                improvement_category=improvement_category,
                improvement_theme=improvement_theme
            )

            # 2. Create IdeaDetail with ALL fields
            IdeaDetail.objects.create(
                idea=idea,
                problem_statement=problem_statement,
                proposed_solution=proposed_solution,
                keywords=keywords,
                technology=technology,
                business_monetary=monetary_value,
                business_value_monetary=business_value_monetary,
                assumptions=assumptions,
                risks=risks,
                context=context,
                innovation_type=innovation_type
            )

            # 3. Add Co-Ideators (Email list from hidden input or similar)
            co_ideator_emails = request.POST.getlist('co_ideators')
            for email in co_ideator_emails:
                try:
                    co_user = IrisUser.objects.get(email=email)
                    CoIdeator.objects.get_or_create(idea=idea, user=co_user)
                except IrisUser.DoesNotExist:
                    continue

            # 4. Handle Documents
            files = request.FILES.getlist('idea_documents')
            for f in files:
                IdeaDocument.objects.create(
                    idea=idea,
                    file_name=f.name,
                    file_url=f # FileField handles this
                )

            # 5. Reward Points (5 points for submission)
            Reward.objects.create(
                user=user,
                points=5,
                reason=f"Idea submission for {challenge.title}"
            )

            messages.success(request, f"Your idea '{title}' has been submitted successfully! You earned 5 IRIS points.")

            # Notify Challenge Owner
            if challenge.created_by:
                send_notification(
                    recipient=challenge.created_by,
                    message=f"New idea '{title}' submitted for your challenge: {challenge.title}.",
                    sender=user,
                    link='/my-ideas/'
                )

            # Notify Mentors
            mentors = IrisUser.objects.filter(challengementor__panel__challenge=challenge).distinct()
            for mentor in mentors:
                send_notification(
                    recipient=mentor,
                    message=f"New idea '{title}' submitted for the challenge you are mentoring: {challenge.title}.",
                    sender=user,
                    link='/challenges/'
                )

            return JsonResponse({'status': 'success', 'message': 'Idea submitted successfully'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # Extract employee information to display on form
    empcode = None
    empname = None
    emailid = user.email
    ibu_name = None
    service_line = None

    if employee_detail:
        # Get employee master information if available
        if employee_detail.user.employee_master:
            empcode = employee_detail.user.employee_master.employee_id
            empname = employee_detail.user.employee_master.full_name
        ibu_name = employee_detail.ibu_name
        service_line = employee_detail.service_line

    # For search (AJAX-like) - can be separate but keep simple for now
    context = {
        'challenge': challenge,
        'user': user,
        'employee_detail': employee_detail,
        'empcode': empcode,
        'empname': empname,
        'emailid': emailid,
        'ibu_name': ibu_name,
        'service_line': service_line,
        'innovation_types': IdeaDetail.INNOVATION_TYPE_CHOICES,
        'sharing_scopes': Idea.SHARING_SCOPE_CHOICES,
    }
    return render(request, 'iris_app/submit_idea.html', context)


def submit_grassroot_idea(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    # Attach user to request for base.html
    request.iris_user = user

    # Try to get employee details
    employee_detail = EmployeeDetail.objects.filter(user=user).first()
    categories = ImprovementCategory.objects.all()

    if request.method == 'POST':
        category_id = request.POST.get('improvement_category')
        subcategory_id = request.POST.get('improvement_sub_category')
        business_value = request.POST.get('business_value')
        monetary_value = request.POST.get('monetary_value')
        proposed_idea = request.POST.get('proposed_idea')
        non_monetary_value = request.POST.get('non_monetary_value')
        additional_info = request.POST.get('additional_info')
        assumptions = request.POST.get('assumptions')
        key_risks = request.POST.get('key_risks')

        category = ImprovementCategory.objects.get(id=category_id) if category_id else None
        subcategory = ImprovementSubCategory.objects.get(id=subcategory_id) if subcategory_id else None

        idea = GrassrootIdea.objects.create(
            ideator=user,
            improvement_category=category,
            improvement_sub_category=subcategory,
            business_value=business_value,
            monetary_value=monetary_value,
            proposed_idea=proposed_idea,
            non_monetary_value=non_monetary_value,
            additional_information=additional_info,
            assumptions=assumptions,
            key_risks=key_risks,
            status='SUBMITTED_RM'
        )

        # Notify Reporting Manager
        if employee_detail and employee_detail.reporting_manager:
            send_notification(
                recipient=employee_detail.reporting_manager,
                message=f"New grassroot idea submitted by {user.full_name}: {proposed_idea[:50]}...",
                sender=user,
                link='/rm-dashboard/'
            )

        messages.success(request, "Your idea has been submitted successfully!")
        return redirect('grassroot_dashboard')

    context = {
        'employee_detail': employee_detail,
        'categories': categories,
    }
    return render(request, 'iris_app/submit_grassroot_idea.html', context)

def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = ImprovementSubCategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)

def grassroot_dashboard(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user
    ideas = GrassrootIdea.objects.filter(ideator=user).order_by('-created_at')

    return render(request, 'iris_app/grassroot_dashboard.html', {'ideas': ideas})

def rm_dashboard(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    if not user.is_rm:
        messages.error(request, "Access denied. Only Reporting Managers can access this dashboard.")
        return redirect('challenge_list')

    request.iris_user = user
    # Ideas submitted by people reporting to this manager
    ideas = GrassrootIdea.objects.filter(
        ideator__employeedetail__reporting_manager=user,
        status='SUBMITTED_RM'
    ).order_by('-created_at')

    return render(request, 'iris_app/rm_dashboard.html', {'ideas': ideas})

def ibu_dashboard(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    if not user.is_ibu_head:
        messages.error(request, "Access denied. Only IBU Heads can access this dashboard.")
        return redirect('challenge_list')

    request.iris_user = user
    # Ideas approved by RM and pending IBU
    ideas = GrassrootIdea.objects.filter(status='APPROVED_RM').order_by('-created_at')

    return render(request, 'iris_app/ibu_dashboard.html', {'ideas': ideas})

def evaluate_grassroot(request, idea_id):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    idea = get_object_or_404(GrassrootIdea, idea_id=idea_id)

    if request.method == 'POST':
        is_desirable = request.POST.get('is_desirable') == 'YES'
        is_feasible = request.POST.get('is_feasible') == 'YES'
        is_viable = request.POST.get('is_viable') == 'YES'
        remarks = request.POST.get('remarks')

        role = 'RM' if idea.status == 'SUBMITTED_RM' else 'IBU'

        GrassrootEvaluation.objects.create(
            idea=idea,
            evaluator=user,
            evaluator_role=role,
            is_desirable=is_desirable,
            is_feasible=is_feasible,
            is_viable=is_viable,
            remarks=remarks
        )

        if role == 'RM':
            idea.status = 'APPROVED_RM'
            # Notify Ideator
            send_notification(
                recipient=idea.ideator,
                message=f"Your grassroot idea has been approved by your RM.",
                sender=user,
                link='/grassroot-dashboard/'
            )
            # Notify IBU Heads
            ibu_heads = IrisUser.objects.filter(userrole__role__role_name='IBU Head')
            for head in ibu_heads:
                send_notification(
                    recipient=head,
                    message=f"New grassroot idea approved by RM and pending IBU review: {idea.proposed_idea[:50]}...",
                    sender=user,
                    link='/ibu-dashboard/'
                )
        else:
            idea.status = 'APPROVED_IBU'
            # Notify Ideator
            send_notification(
                recipient=idea.ideator,
                message=f"Your grassroot idea has been approved by the IBU Head!",
                sender=user,
                link='/grassroot-dashboard/'
            )

        idea.save()
        messages.success(request, f"Idea evaluated successfully by {role}!")
        return redirect('rm_dashboard' if role == 'RM' else 'ibu_dashboard')

    return render(request, 'iris_app/evaluate_grassroot.html', {'idea': idea})

def rework_grassroot(request, idea_id):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    idea = get_object_or_404(GrassrootIdea, idea_id=idea_id)

    if request.method == 'POST':
        rework_needed = request.POST.get('rework_needed') == 'YES'
        if rework_needed:
            idea.status = 'REWORK_RM' if idea.status == 'SUBMITTED_RM' else 'REWORK_IBU'
            messages.success(request, "Rework requested.")
            send_notification(
                recipient=idea.ideator,
                message=f"Rework required for your grassroot idea: {idea.proposed_idea[:50]}...",
                sender=user,
                link='/grassroot-dashboard/'
            )
        else:
            idea.status = 'REJECTED_RM' if idea.status == 'SUBMITTED_RM' else 'REJECTED_IBU'
            messages.success(request, "Idea rejected.")
            send_notification(
                recipient=idea.ideator,
                message=f"Your grassroot idea has been rejected.",
                sender=user,
                link='/grassroot-dashboard/'
            )

        idea.save()
        return redirect('rm_dashboard' if 'RM' in idea.status else 'ibu_dashboard')

def customer_input(request, idea_id):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    idea = get_object_or_404(GrassrootIdea, idea_id=idea_id)

    if request.method == 'POST':
        idea.confidentiality = request.POST.get('confidentiality')
        idea.customer_feedback = request.POST.get('customer_feedback')
        idea.innovation_context = request.POST.get('innovation_context')
        idea.status = 'COMPLETED'
        idea.save()
        messages.success(request, "Customer input submitted successfully!")
        return redirect('ibu_dashboard')

    return render(request, 'iris_app/customer_input.html', {'idea': idea})

def my_ideas(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    ideas = Idea.objects.filter(submitter=user).order_by('-submission_date')

    # Also shared ideas where user is co-ideator
    shared_ideas = Idea.objects.filter(coideator__user=user).exclude(submitter=user)

    # Total points
    total_points = Reward.objects.filter(user=user).aggregate(Sum('points'))['points__sum'] or 0

    context = {
        'ideas': ideas,
        'shared_ideas': shared_ideas,
        'total_points': total_points,
        'user': user,
    }
    return render(request, 'iris_app/my_ideas.html', context)

def user_dashboard(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user

    # Stats
    total_points = Reward.objects.filter(user=user).aggregate(Sum('points'))['points__sum'] or 0
    ideas_count = Idea.objects.filter(submitter=user).count()
    challenges_participated = Idea.objects.filter(submitter=user).values('challenge').distinct().count()

    # Recent Activity (Ideas)
    recent_ideas = Idea.objects.filter(submitter=user).order_by('-submission_date')[:5]

    # Notifications (Unread)
    notifications = Notification.objects.filter(recipient=user, is_read=False).order_by('-created_at')[:5]

    # Ongoing Challenges (Live)
    active_challenges = Challenge.objects.filter(status='LIVE').order_by('end_date')[:3]

    context = {
        'user': user,
        'total_points': total_points,
        'ideas_count': ideas_count,
        'challenges_count': challenges_participated,
        'recent_ideas': recent_ideas,
        'notifications': notifications,
        'active_challenges': active_challenges,
    }
    return render(request, 'iris_app/user_dashboard.html', context)

def reports_view(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user
    return render(request, 'iris_app/reports.html')

def export_report_csv(request):
    user = get_context_user(request)
    if not user:
        return redirect('login')

    report_type = request.GET.get('report_type')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if not all([report_type, from_date, to_date]):
        messages.error(request, "Please provide all filter parameters.")
        return redirect('reports_view')

    try:
        from_dt = timezone.make_aware(datetime.datetime.strptime(from_date, '%Y-%m-%d'))
        # Set to_dt to end of the day
        to_dt = timezone.make_aware(datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(days=1))
    except (ValueError, TypeError):
        messages.error(request, "Invalid date format.")
        return redirect('reports_view')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{from_date}_to_{to_date}.csv"'
    writer = csv.writer(response)

    if report_type == 'challenges':
        headers = ['Title', 'Status', 'Start Date', 'End Date', 'Created By', 'Target Audience', 'Visibility']
        writer.writerow(headers)
        queryset = Challenge.objects.filter(created_at__range=(from_dt, to_dt))
        for obj in queryset:
            writer.writerow([obj.title, obj.status, obj.start_date, obj.end_date, obj.created_by.full_name if obj.created_by else 'N/A', obj.target_audience, obj.visibility])

    elif report_type == 'ideas':
        headers = ['Title', 'Submitter', 'Challenge', 'Status', 'Submission Date', 'Sharing Scope']
        writer.writerow(headers)
        queryset = Idea.objects.filter(submission_date__range=(from_dt, to_dt))
        for obj in queryset:
            writer.writerow([obj.title, obj.submitter.full_name if obj.submitter else 'N/A', obj.challenge.title if obj.challenge else 'General', obj.status, obj.submission_date, obj.sharing_scope])

    elif report_type == 'grassroot':
        headers = ['Ideator', 'Category', 'Subcategory', 'Status', 'Created At', 'Proposed Idea']
        writer.writerow(headers)
        queryset = GrassrootIdea.objects.filter(created_at__range=(from_dt, to_dt))
        for obj in queryset:
            writer.writerow([
                obj.ideator.full_name,
                obj.improvement_category.name if obj.improvement_category else 'N/A',
                obj.improvement_sub_category.name if obj.improvement_sub_category else 'N/A',
                obj.status,
                obj.created_at,
                obj.proposed_idea[:100]
            ])
    else:
        messages.error(request, "Invalid report type.")
        return redirect('reports_view')

    return response


def challenge_register(request, challenge_id):
    """Display challenge registration page"""
    user = get_context_user(request)
    if not user:
        return redirect('login')

    request.iris_user = user
    challenge = get_object_or_404(Challenge, challenge_id=challenge_id)

    # Check if registration is required - case insensitive check
    reg_required = (challenge.registration_required or '').lower()
    if reg_required != 'yes':
        messages.warning(request, "This challenge does not require registration.")
        return redirect('challenge_detail', challenge_id=challenge_id)

    context = {
        'challenge': challenge,
        'user': user,
        'participation_type': challenge.participation_type,
        'max_team_size': challenge.max_team_size or 1,
    }
    return render(request, 'iris_app/challenge_register.html', context)


def submit_registration(request, challenge_id):
    """Handle challenge registration form submission"""
    user = get_context_user(request)
    if not user:
        return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

    challenge = get_object_or_404(Challenge, challenge_id=challenge_id)

    try:
        participation_mode = request.POST.get('participation_mode')  # 'Individual' or 'Team'
        team_name = request.POST.get('team_name') if participation_mode == 'Team' else None
        team_lead_name = request.POST.get('team_lead_name') if participation_mode == 'Team' else None

        # Get team members from request
        team_member_emails = request.POST.getlist('team_member_emails[]') if participation_mode == 'Team' else []

        # Validate participation mode against challenge settings
        participation_type = (challenge.participation_type or '').lower()
        if participation_type == 'individual' and participation_mode != 'Individual':
            return JsonResponse({'status': 'error', 'message': 'This challenge only accepts individual submissions'}, status=400)
        elif participation_type == 'team' and participation_mode != 'Team':
            return JsonResponse({'status': 'error', 'message': 'This challenge only accepts team submissions'}, status=400)

        # Validate team size if team
        if participation_mode == 'Team':
            team_size = len(team_member_emails) + 1  # +1 for the current user
            if team_size > challenge.max_team_size:
                return JsonResponse({'status': 'error', 'message': f'Team size exceeds maximum ({challenge.max_team_size})'}, status=400)

            if not team_name:
                return JsonResponse({'status': 'error', 'message': 'Team name is required'}, status=400)

        #Create a registration record (for now, we'll store it in Idea with participation mode)
        # This is more of a meta-data tracking; actual submission happens during idea submission
        # For now, we just validate and return success

        messages.success(request, f"Registration successful! You are now registered for {challenge.title}")
        return JsonResponse({'status': 'success', 'message': 'Registration successful', 'redirect_url': reverse('submit_idea', args=[challenge_id])})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
