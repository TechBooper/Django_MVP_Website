from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import TicketForm, ReviewForm, CombinedTicketReviewForm
from .models import Ticket, Review, UserFollows
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect



def dashboard(request):
    tickets = Ticket.objects.filter(user=request.user)
    reviews = Review.objects.filter(user=request.user)
    context = {
        'tickets': tickets,
        'reviews': reviews,
    }
    return render(request, 'dashboard.html', context)

@login_required
def feed(request):
    following_users = [follow.followed_user for follow in request.user.following.all()]
    tickets = Ticket.objects.filter(user__in=following_users).order_by('-time_created')
    reviews = Review.objects.filter(user__in=following_users).order_by('-time_created')
    combined = sorted(
        list(tickets) + list(reviews),
        key=lambda x: x.time_created,
        reverse=True
    )
    return render(request, 'feed.html', {'combined': combined})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('myapp:feed')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, 'Ticket created successfully.')
            return redirect('myapp:feed')
    else:
        form = TicketForm()
    return render(request, 'create_ticket.html', {'form': form})

@login_required
def create_review(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.ticket = ticket
            review.user = request.user
            review.save()
            return redirect('myapp:feed')
    else:
        form = ReviewForm()
    return render(request, 'create_review.html', {'form': form, 'post': ticket})

@login_required
def create_ticket_review(request):
    if request.method == 'POST':
        form = CombinedTicketReviewForm(request.POST)
        if form.is_valid():
            ticket = Ticket(
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                user=request.user
            )
            ticket.save()
            review = Review(
                rating=form.cleaned_data['rating'],
                headline=form.cleaned_data['headline'],
                body=form.cleaned_data['body'],
                ticket=ticket,
                user=request.user
            )
            review.save()
            messages.success(request, 'Ticket and Review created successfully.')
            return redirect('myapp:feed')
    else:
        form = CombinedTicketReviewForm()
    return render(request, 'create_ticket_review.html', {'form': form})

@login_required
def follow_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user_to_follow = User.objects.get(username=username)
            if user_to_follow != request.user:
                UserFollows.objects.get_or_create(user=request.user, followed_user=user_to_follow)
        except ObjectDoesNotExist:
            return render(request, 'follow_user.html', {'error': 'User does not exist'})
    return render(request, 'follow_user.html')

@login_required
def followed_users(request):
    follows = UserFollows.objects.filter(user=request.user)
    return render(request, 'followed_users.html', {'follows': follows})

def index(request):
    return render(request, 'base.html')

@login_required
def add_ticket(request):
    return handle_create_form(request, TicketForm, 'add_ticket.html', 'Ticket created successfully.')

@login_required
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('myapp:dashboard'))
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'edit_ticket.html', {'form': form, 'ticket': ticket})

@login_required
@require_POST
@permission_required('myapp.delete_ticket', raise_exception=True)
def delete_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    if request.method == 'POST':
        ticket.delete()
        return redirect(reverse('myapp:dashboard'))
    return render(request, 'delete_ticket.html', {'ticket': ticket})

@login_required
def add_review(request):
    return handle_create_form(request, ReviewForm, 'add_review.html', 'Review created successfully.')

def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('myapp:dashboard'))
    else:
        form = ReviewForm(instance=review)
    return render(request, 'edit_review.html', {'form': form, 'review': review})

@login_required
@permission_required('myapp.delete_review', raise_exception=True)
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    if request.method == 'POST':
        review.delete()
        return redirect(reverse('myapp:dashboard'))
    return render(request, 'delete_review.html', {'review': review})

def handle_create_form(request, form_class, template_name, success_message):
    if not request.user.has_perm('can_create_' + form_class._meta.model_name):
        messages.error(request, 'You do not have permission to create this object.')
        return redirect('myapp:feed')
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            messages.success(request, success_message)
            return redirect('myapp:feed')
    else:
        form = form_class()
    return render(request, template_name, {'form': form})

def handle_edit_form(request, instance_id, model_class, form_class, template_name, success_message):
    instance = get_object_or_404(model_class, pk=instance_id, user=request.user)
    if not request.user.has_perm('can_edit_' + model_class._meta.model_name):
        messages.error(request, 'You do not have permission to edit this object.')
        return redirect('myapp:feed')
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect('myapp:feed')
    else:
        form = form_class(instance=instance)
    return render(request, template_name, {'form': form, 'instance': instance})

def handle_delete(request, instance_id, model_class, success_message):
    instance = get_object_or_404(model_class, pk=instance_id, user=request.user)
    if not request.user.has_perm('can_delete_' + model_class._meta.model_name):
        messages.error(request, 'You do not have permission to delete this object.')
        return redirect('myapp:feed')
    if request.method == 'POST':
        instance.delete()
        messages.success(request, success_message)
        return redirect('myapp:feed')
    return render(request, 'base.html', {'instance': instance})

@login_required
@require_POST
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)
    if not UserFollows.objects.filter(user=request.user, followed_user=user_to_unfollow).exists():
        messages.error(request, 'You are not following this user.')
        return redirect('myapp:feed')
    UserFollows.objects.filter(user=request.user, followed_user=user_to_unfollow).delete()
    messages.success(request, f'You have unfollowed {user_to_unfollow.username}.')
    return redirect('myapp:feed')

def custom_logout(request):
    logout(request)
    return redirect('login')
