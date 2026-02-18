from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import csv
from .models import (
    Challenge, Idea, IrisUser, UserRole, ChallengePanel, ChallengeMentor, Role,
    ReviewParameter, ChallengeReviewParameter, Reward, IdeaDetail, CoIdeator, IdeaDocument,
    ImprovementCategory, ImprovementSubCategory, GrassrootIdea, GrassrootEvaluation, EmployeeDetail,
    Notification, UserLoginLog, IrisClusterIbgIbu
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
                return redirect('challenge_list')
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

    # Role definitions
    is_mentor = UserRole.objects.filter(user=user, role__role_name='Mentor').exists()
    is_challenge_owner = UserRole.objects.filter(user=user, role__role_name='Challenge Owner').exists()

    # Apply Role-based Base Visibility First
    if is_mentor:
        challenges = challenges.filter(challengepanel__challengementor__mentor=user).distinct()
    elif is_challenge_owner:
        # Owners see everything they created + all LIVE challenges
        challenges = challenges.filter(models.Q(created_by=user) | models.Q(status='LIVE')).distinct()
    else:
        # Regular users/Ideators only see LIVE
        challenges = challenges.filter(status='LIVE')

    # Apply Status Filter from URL
    if status_filter == 'active':
        challenges = challenges.filter(status='LIVE')
    elif status_filter == 'draft':
        challenges = challenges.filter(status='DRAFT')
    elif status_filter == 'past':
        challenges = challenges.filter(status='COMPLETED')
    elif status_filter == 'all':
        # 'all' just respects the base visibility (e.g. owners see their drafts + live)
        pass
        
    # Apply Search Query
    if query:
        challenges = challenges.filter(models.Q(title__icontains=query) | models.Q(keywords__icontains=query))
        
    featured_challenge = Challenge.objects.filter(is_featured=True).first()
    
    context = {
        'featured_challenge': featured_challenge,
        'challenges': challenges,
        'current_filter': status_filter,
        'query': query,
    }
    return render(request, 'iris_app/index.html', context)

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

    context = {
        'challenge': challenge,
        'review_params': challenge.review_parameters.all(),
        'is_mentor': is_mentor,
        'is_owner': is_owner,
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
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    ibus = IrisClusterIbgIbu.objects.filter(
        models.Q(function_lg_desc__icontains=query) & models.Q(function_type='IBU')
    ).values_list('function_lg_desc', flat=True).distinct()[:20]
    
    return JsonResponse({'results': [{'id': name, 'text': name} for name in ibus]})

@transaction.atomic
def post_challenge(request):
    user = get_context_user(request)
    if not user or not user.is_challenge_owner:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Access denied.'})
        messages.error(request, "Access denied. Only Challenge Owners can post challenges.")
        return redirect('challenge_list')
    
    request.iris_user = user
    review_parameters = ReviewParameter.objects.filter(is_active=True)

    if request.method == 'POST':
        # Step 1 & 2 & 4 Core Data
        title = request.POST.get('title')
        description = request.POST.get('description')
        ibu_name = request.POST.get('ibu_name')
        keywords = request.POST.get('keywords')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        target_audience = request.POST.get('target_audience')
        visibility = request.POST.get('visibility')
        expected_outcome = request.POST.get('expected_outcome')
        round1_eval_criteria = request.POST.get('round1_eval_criteria')
        num_rounds = request.POST.get('num_rounds', '1')
        
        # Files
        challenge_icon = request.FILES.get('challenge_icon')
        challenge_doc = request.FILES.get('challenge_document')

        try:
            # Parse dates
            start_date = timezone.make_aware(datetime.datetime.strptime(start_date_str, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.datetime.strptime(end_date_str, '%Y-%m-%d'))
            
            # Create Challenge
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
                challenge_icon=challenge_icon,
                challenge_document=challenge_doc,
                created_by=user,
                status='LIVE' 
            )

            # Step 3: Review Parameters
            param_names = request.POST.getlist('param_names[]')
            param_weights = request.POST.getlist('param_weights[]')
            
            for name, weight in zip(param_names, param_weights):
                if name and weight:
                    # Find or create general parameter
                    param_obj, _ = ReviewParameter.objects.get_or_create(
                        parameter_name=name,
                        defaults={'description': f'Evaluation based on {name}'}
                    )
                    ChallengeReviewParameter.objects.create(
                        challenge=challenge,
                        parameter=param_obj,
                        weightage=int(weight)
                    )

            # Step 3: Panels & Mentors
            panel_names = request.POST.getlist('panel_names[]')
            panel_rounds = request.POST.getlist('panel_rounds[]')
            panel_descriptions = request.POST.getlist('panel_descriptions[]')
            
            for i in range(len(panel_names)):
                panel = ChallengePanel.objects.create(
                    challenge=challenge,
                    panel_name=panel_names[i],
                    description=panel_descriptions[i],
                    round_number=int(panel_rounds[i])
                )
                
                # Mentors for this specific panel
                mentor_ids = request.POST.getlist(f'panel_mentors[{i}][]')
                for m_id in mentor_ids:
                    mentor_user = IrisUser.objects.get(user_id=m_id)
                    ChallengeMentor.objects.create(panel=panel, mentor=mentor_user)

            return JsonResponse({'status': 'success', 'challenge_id': str(challenge.challenge_id)})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Also fetch all challenge owners to be potential mentors/reviewers
    challenge_owners = IrisUser.objects.filter(userrole__role__role_name='Challenge Owner').distinct()

    return render(request, 'iris_app/post_challenge.html', {
        'review_parameters': review_parameters,
        'challenge_owners': challenge_owners
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

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        keywords = request.POST.get('keywords')
        is_confidential = request.POST.get('is_confidential') == 'on'
        sharing_scope = request.POST.get('sharing_scope', 'NONE')
        
        # IdeaDetail fields
        problem_statement = request.POST.get('problem_statement')
        proposed_solution = request.POST.get('proposed_solution')
        business_value_monetary = request.POST.get('business_value_monetary')
        business_value_non_monetary = request.POST.get('business_value_non_monetary')
        assumptions = request.POST.get('assumptions')
        risks = request.POST.get('risks')
        innovation_type = request.POST.get('innovation_type')
        
        # 1. Create Idea
        idea = Idea.objects.create(
            title=title,
            submitter=user,
            challenge=challenge,
            status='SUBMITTED',
            is_confidential=is_confidential,
            sharing_scope=sharing_scope
        )
        
        # 2. Create IdeaDetail
        IdeaDetail.objects.create(
            idea=idea,
            problem_statement=problem_statement,
            proposed_solution=proposed_solution,
            business_value_monetary=business_value_monetary,
            business_value_non_monetary=business_value_non_monetary,
            assumptions=assumptions,
            risks=risks,
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

        return redirect('my_ideas')

    # For search (AJAX-like) - can be separate but keep simple for now
    context = {
        'challenge': challenge,
        'user': user,
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
