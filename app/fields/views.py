import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Field, FieldUpdate, UserProfile
from django.db.models import Count, Q


# ─── Auth Views ───────────────────────────────────────────────

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username   = request.POST.get('username')
        email      = request.POST.get('email', '')
        password1  = request.POST.get('password1')
        password2  = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name  = request.POST.get('last_name', '')
        role       = request.POST.get('role', 'agent')

        # Validations
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            UserProfile.objects.create(user=user, role=role)
            login(request, user)
            messages.success(request, f'Welcome to SmartSeason, {user.first_name or user.username}!')
            return redirect('dashboard')

    return render(request, 'registration/signup.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Dashboard ────────────────────────────────────────────────

@login_required
def dashboard(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if profile.is_admin:
        fields = Field.objects.all().select_related('assigned_agent')
    else:
        fields = Field.objects.filter(
            assigned_agent=request.user
        ).select_related('assigned_agent')

    # Status breakdown
    active = [f for f in fields if f.computed_status == 'active']
    at_risk = [f for f in fields if f.computed_status == 'at_risk']
    completed = [f for f in fields if f.computed_status == 'completed']

    # Stage breakdown
    stage_counts = {
        'planted': fields.filter(current_stage='planted').count(),
        'growing': fields.filter(current_stage='growing').count(),
        'ready': fields.filter(current_stage='ready').count(),
        'harvested': fields.filter(current_stage='harvested').count(),
    }

    # Recent updates (admin sees all, agent sees own)
    if profile.is_admin:
        recent_updates = FieldUpdate.objects.all().select_related(
            'field', 'updated_by'
        )[:10]
    else:
        recent_updates = FieldUpdate.objects.filter(
            field__assigned_agent=request.user
        ).select_related('field', 'updated_by')[:10]

    # inside dashboard view, replace the context block with:
    # Crop type breakdown for chart
    crop_counts = fields.values('crop_type').annotate(count=Count('id')).order_by('-count')
    crop_data = json.dumps({
        'labels': [c['crop_type'].capitalize() for c in crop_counts],
        'values': [c['count'] for c in crop_counts],
    })
    agent_performance = None
    if profile.is_admin:
        agents = User.objects.filter(profile__role='agent')
        agent_performance = []
        for agent in agents:
            agent_fields = Field.objects.filter(assigned_agent=agent)
            agent_performance.append({
                'agent': agent,
                'total': agent_fields.count(),
                'active': len([f for f in agent_fields if f.computed_status == 'active']),
                'at_risk': len([f for f in agent_fields if f.computed_status == 'at_risk']),
                'completed': len([f for f in agent_fields if f.computed_status == 'completed']),
            })

    context = {
        'profile': profile,
        'fields': fields,
        'total_fields': fields.count(),
        'active_count': len(active),
        'at_risk_count': len(at_risk),
        'completed_count': len(completed),
        'stage_counts': stage_counts,
        'recent_updates': recent_updates,
        'crop_data': crop_data,  
        'agent_performance': agent_performance, # ← new
    }
    return render(request, 'fields/dashboard.html', context)


# ─── Field Views ──────────────────────────────────────────────

@login_required
def field_list(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.is_admin:
        fields = Field.objects.all().select_related('assigned_agent')
    else:
        fields = Field.objects.filter(assigned_agent=request.user)

    # Search & filter
    search = request.GET.get('search', '')
    stage_filter = request.GET.get('stage', '')
    status_filter = request.GET.get('status', '')

    if search:
        fields = fields.filter(
            Q(name__icontains=search) | Q(crop_type__icontains=search) | Q(location__icontains=search)
        )
    if stage_filter:
        fields = fields.filter(current_stage=stage_filter)
    if status_filter:
        fields = [f for f in fields if f.computed_status == status_filter]

    context = {
        'profile': profile,
        'fields': fields,
        'search': search,
        'stage_filter': stage_filter,
        'status_filter': status_filter,
    }
    return render(request, 'fields/field_list.html', context)


@login_required
def field_detail(request, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    field = get_object_or_404(Field, pk=pk)

    # Agents can only view their assigned fields
    if profile.is_agent and field.assigned_agent != request.user:
        messages.error(request, 'You do not have access to this field.')
        return redirect('field_list')

    updates = field.updates.select_related('updated_by').all()
    context = {
        'profile': profile,
        'field': field,
        'updates': updates,
    }
    return render(request, 'fields/field_detail.html', context)


@login_required
def field_create(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin:
        messages.error(request, 'Only admins can create fields.')
        return redirect('dashboard')

    agents = User.objects.filter(profile__role='agent')

    if request.method == 'POST':
        name = request.POST.get('name')
        crop_type = request.POST.get('crop_type')
        planting_date = request.POST.get('planting_date')
        current_stage = request.POST.get('current_stage')
        location = request.POST.get('location', '')
        size_acres = request.POST.get('size_acres') or None
        assigned_agent_id = request.POST.get('assigned_agent') or None

        field = Field.objects.create(
            name=name,
            crop_type=crop_type,
            planting_date=planting_date,
            current_stage=current_stage,
            location=location,
            size_acres=size_acres,
            assigned_agent_id=assigned_agent_id,
            created_by=request.user,
        )
        messages.success(request, f'Field "{field.name}" created successfully!')
        return redirect('field_detail', pk=field.pk)

    context = {
        'profile': profile,
        'agents': agents,
        'crop_choices': Field.CROP_CHOICES,
        'stage_choices': Field.STAGE_CHOICES,
    }
    return render(request, 'fields/field_form.html', context)


@login_required
def field_edit(request, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    field = get_object_or_404(Field, pk=pk)

    if not profile.is_admin:
        messages.error(request, 'Only admins can edit fields.')
        return redirect('dashboard')

    agents = User.objects.filter(profile__role='agent')

    if request.method == 'POST':
        field.name = request.POST.get('name')
        field.crop_type = request.POST.get('crop_type')
        field.planting_date = request.POST.get('planting_date')
        field.current_stage = request.POST.get('current_stage')
        field.location = request.POST.get('location', '')
        field.size_acres = request.POST.get('size_acres') or None
        field.assigned_agent_id = request.POST.get('assigned_agent') or None
        field.save()
        messages.success(request, f'Field "{field.name}" updated successfully!')
        return redirect('field_detail', pk=field.pk)

    context = {
        'profile': profile,
        'field': field,
        'agents': agents,
        'crop_choices': Field.CROP_CHOICES,
        'stage_choices': Field.STAGE_CHOICES,
    }
    return render(request, 'fields/field_form.html', context)


@login_required
def field_delete(request, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    field = get_object_or_404(Field, pk=pk)

    if not profile.is_admin:
        messages.error(request, 'Only admins can delete fields.')
        return redirect('dashboard')

    if request.method == 'POST':
        field_name = field.name
        field.delete()
        messages.success(request, f'Field "{field_name}" deleted.')
        return redirect('field_list')

    return render(request, 'fields/field_confirm_delete.html', {
        'profile': profile,
        'field': field
    })


# ─── Field Update View ────────────────────────────────────────

@login_required
def field_update(request, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    field = get_object_or_404(Field, pk=pk)

    # Only assigned agent or admin can post updates
    if profile.is_agent and field.assigned_agent != request.user:
        messages.error(request, 'You are not assigned to this field.')
        return redirect('field_list')

    if request.method == 'POST':
        stage = request.POST.get('stage')
        notes = request.POST.get('notes', '')

        # Create the update log
        FieldUpdate.objects.create(
            field=field,
            updated_by=request.user,
            stage=stage,
            notes=notes,
        )

        # Update the field's current stage
        field.current_stage = stage
        field.save()

        messages.success(request, f'Field "{field.name}" updated to stage: {stage}.')
        return redirect('field_detail', pk=field.pk)

    context = {
        'profile': profile,
        'field': field,
        'stage_choices': Field.STAGE_CHOICES,
    }
    return render(request, 'fields/field_update.html', context)


# ─── Agent Management (Admin only) ───────────────────────────

@login_required
def agent_list(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin:
        return redirect('dashboard')

    agents = User.objects.filter(profile__role='agent').prefetch_related('assigned_fields')
    context = {
        'profile': profile,
        'agents': agents,
    }
    return render(request, 'fields/agent_list.html', context)


@login_required
def agent_create(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        role = request.POST.get('role', 'agent')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            UserProfile.objects.create(user=user, role=role)
            messages.success(request, f'User "{username}" created successfully!')
            return redirect('agent_list')

    context = {'profile': profile}
    return render(request, 'fields/agent_form.html', context)

# ─── REST API Endpoints ───────────────────────────────────────

@require_GET
def api_fields(request):
    """
    GET /api/fields/
    Returns all fields (admin) or assigned fields (agent).
    Requires login.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    profile = get_object_or_404(UserProfile, user=request.user)

    if profile.is_admin:
        fields = Field.objects.all().select_related('assigned_agent')
    else:
        fields = Field.objects.filter(
            assigned_agent=request.user
        ).select_related('assigned_agent')

    data = []
    for field in fields:
        data.append({
            'id': field.pk,
            'name': field.name,
            'crop_type': field.crop_type,
            'planting_date': str(field.planting_date),
            'current_stage': field.current_stage,
            'status': field.computed_status,
            'location': field.location,
            'size_acres': float(field.size_acres) if field.size_acres else None,
            'days_since_planting': field.days_since_planting,
            'assigned_agent': field.assigned_agent.username if field.assigned_agent else None,
            'created_at': field.created_at.isoformat(),
        })

    return JsonResponse({
        'count': len(data),
        'fields': data,
    })


@require_GET
def api_field_detail(request, pk):
    """
    GET /api/fields/<id>/
    Returns a single field with its update history.
    Requires login.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    profile = get_object_or_404(UserProfile, user=request.user)
    field   = get_object_or_404(Field, pk=pk)

    if profile.is_agent and field.assigned_agent != request.user:
        return JsonResponse({'error': 'Access denied.'}, status=403)

    updates = []
    for u in field.updates.select_related('updated_by').all():
        updates.append({
            'id': u.pk,
            'stage': u.stage,
            'notes': u.notes,
            'updated_by': u.updated_by.username if u.updated_by else None,
            'created_at': u.created_at.isoformat(),
        })

    return JsonResponse({
        'id': field.pk,
        'name': field.name,
        'crop_type': field.crop_type,
        'planting_date': str(field.planting_date),
        'current_stage': field.current_stage,
        'status': field.computed_status,
        'location': field.location,
        'size_acres': float(field.size_acres) if field.size_acres else None,
        'days_since_planting': field.days_since_planting,
        'assigned_agent': field.assigned_agent.username if field.assigned_agent else None,
        'created_at': field.created_at.isoformat(),
        'updates': updates,
    })


@require_GET
def api_dashboard(request):
    """
    GET /api/dashboard/
    Returns dashboard summary stats.
    Requires login.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    profile = get_object_or_404(UserProfile, user=request.user)

    if profile.is_admin:
        fields = Field.objects.all()
    else:
        fields = Field.objects.filter(assigned_agent=request.user)

    fields_list = list(fields)

    return JsonResponse({
        'user': request.user.username,
        'role': profile.role,
        'summary': {
            'total_fields': len(fields_list),
            'active': len([f for f in fields_list if f.computed_status == 'active']),
            'at_risk': len([f for f in fields_list if f.computed_status == 'at_risk']),
            'completed': len([f for f in fields_list if f.computed_status == 'completed']),
        },
        'stages': {
            'planted':   fields.filter(current_stage='planted').count(),
            'growing':   fields.filter(current_stage='growing').count(),
            'ready':     fields.filter(current_stage='ready').count(),
            'harvested': fields.filter(current_stage='harvested').count(),
        }
    })