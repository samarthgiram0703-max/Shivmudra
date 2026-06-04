from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from .models import Event
from .forms import EventForm, UserRegistrationForm
from django.utils import timezone
from datetime import datetime

# --- Authentication Views ---

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Shivmudra Events, {user.first_name or user.username}!")
            return redirect('event_list')
        else:
            messages.error(request, "Registration failed. Please check the errors below.")
    else:
        form = UserRegistrationForm()
    return render(request, 'base/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect('event_list')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'base/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')


# --- Event Management Views ---

@login_required
def event_list(request):
    # Fetch all events owned by the user
    all_events = Event.objects.filter(user=request.user)
    
    # Calculate Dashboard Statistics before filters are applied
    stats = {
        'total_events': all_events.count(),
        'completed_events': all_events.filter(status='COMPLETED').count(),
        'pending_events': all_events.filter(status='PENDING').count(),
        'cancelled_events': all_events.filter(status='CANCELLED').count(),
        'total_advanced': all_events.aggregate(Sum('advanced_rs'))['advanced_rs__sum'] or 0.0,
        'total_pending': all_events.aggregate(Sum('pending_rs'))['pending_rs__sum'] or 0.0,
        'total_revenue': all_events.aggregate(Sum('total_rs'))['total_rs__sum'] or 0.0,
    }

    context = {
        'stats': stats,
    }
    
    return render(request, 'base/event_list.html', context)


@login_required
def all_events(request):
    # Fetch all events owned by the user
    all_events = Event.objects.filter(user=request.user)
    
    # Apply Advanced Search and Filters
    events = all_events
    
    # Text Search (Name and Location)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        events = events.filter(
            Q(name__icontains=search_query) | 
            Q(location__icontains=search_query)
        )
        
    # Status Filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        events = events.filter(status=status_filter)
        
    # Date Range Filter
    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            # Make timezone aware if settings.USE_TZ is True
            start_date = timezone.make_aware(start_date)
            events = events.filter(scheduled_date__gte=start_date)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            # Set to end of the day (23:59:59)
            end_date = end_date.replace(hour=23, minute=59, second=59)
            end_date = timezone.make_aware(end_date)
            events = events.filter(scheduled_date__lte=end_date)
        except ValueError:
            pass

    # Sorting
    sort_by = request.GET.get('sort_by', '-scheduled_date').strip()
    allowed_sort_fields = [
        'name', '-name', 
        'scheduled_date', '-scheduled_date', 
        'total_rs', '-total_rs',
        'status', '-status'
    ]
    if sort_by in allowed_sort_fields:
        events = events.order_by(sort_by)
    else:
        events = events.order_by('-scheduled_date')

    context = {
        'events': events,
        # Preserve filter states in form fields
        'search_query': search_query,
        'status_filter': status_filter,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'sort_by': sort_by,
    }
    
    return render(request, 'base/all_events.html', context)


@login_required
def event_detail(request, pk):
    # Verify the event exists and belongs to the current user
    event = get_object_or_404(Event, pk=pk, user=request.user)
    return render(request, 'base/event_detail.html', {'event': event})


@login_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save()
            messages.success(request, f"Event '{event.name}' has been created successfully!")
            return redirect('event_list')
        else:
            messages.error(request, "Failed to create event. Please correct the errors.")
    else:
        form = EventForm()
    return render(request, 'base/event_form.html', {'form': form, 'title': 'Add New Event'})


@login_required
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk, user=request.user)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, f"Event '{event.name}' has been updated successfully!")
            return redirect('event_detail', pk=event.pk)
        else:
            messages.error(request, "Failed to update event. Please correct the errors.")
    else:
        # Prepopulate with the localized datetime for input type="datetime-local"
        form = EventForm(instance=event)
    return render(request, 'base/event_form.html', {'form': form, 'title': 'Edit Event', 'event': event})


@login_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk, user=request.user)
    if request.method == 'POST':
        event_name = event.name
        event.delete()
        messages.success(request, f"Event '{event_name}' was successfully deleted.")
        return redirect('event_list')
    return render(request, 'base/event_confirm_delete.html', {'event': event})


@login_required
def mark_as_paid(request, pk):
    event = get_object_or_404(Event, pk=pk, user=request.user)
    if request.method == 'POST':
        # Add pending to advanced, set pending to 0
        event.advanced_rs += event.pending_rs
        event.pending_rs = 0
        event.save()
        messages.success(request, f"Event '{event.name}' has been marked as fully paid!")
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('event_detail', pk=pk)


from django.http import JsonResponse

@login_required
def event_update_status(request, pk):
    event = get_object_or_404(Event, pk=pk, user=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Event.STATUS_CHOICES):
            event.status = new_status
            event.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': f"Status of '{event.name}' updated to {event.get_status_display()}!"
                })
            messages.success(request, f"Status of event '{event.name}' updated to {event.get_status_display()}!")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': "Invalid status choice."
                }, status=400)
            messages.error(request, "Invalid status choice.")
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('event_list')

