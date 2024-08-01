from itertools import chain
from django.db.models import CharField, Value
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import (
    TicketForm,
    ReviewForm,
    ReviewRequestForm,
    FollowForm,
)
from .models import Ticket, Review, UserFollows, ReviewRequest, UserBlock
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect


def dashboard(request):
    """
    Display all tickets and reviews created by the logged-in user on their dashboard.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered dashboard page with user's tickets and reviews.
    """
    tickets = Ticket.objects.filter(user=request.user)
    reviews = Review.objects.filter(user=request.user)
    context = {
        "tickets": tickets,
        "reviews": reviews,
    }
    return render(request, "dashboard.html", context)


@login_required
def dashboard_view(request):
    """
    Display the dashboard with user's followers, following, tickets, and reviews.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered dashboard page with user's followers, following, tickets, and reviews.
    """
    user = request.user
    followers = user.followers.all()
    following = user.following.all()
    tickets = Ticket.objects.filter(user=user)
    reviews = Review.objects.filter(user=user)
    return render(
        request,
        "dashboard.html",
        {
            "followers": followers,
            "following": following,
            "tickets": tickets,
            "reviews": reviews,
        },
    )


@login_required
def feed(request):
    """
    Display a feed of tickets and reviews from users the current user follows, excluding blocked users' content.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered feed page with combined tickets and reviews sorted by creation time.
    """
    following_users = [follow.followed_user for follow in request.user.following.all()]
    blocked_users = [block.blocked for block in UserBlock.objects.filter(blocker=request.user)]

    tickets = Ticket.objects.filter(user__in=following_users).exclude(user__in=blocked_users).annotate(content_type=Value('TICKET', CharField()))
    reviews = Review.objects.filter(user__in=following_users).exclude(user__in=blocked_users).annotate(content_type=Value('REVIEW', CharField()))

    combined = sorted(
        list(tickets) + list(reviews), key=lambda x: x.time_created, reverse=True
    )

    return render(request, 'feed.html', context={'posts': combined, 'media_url': settings.MEDIA_URL})

def signup(request):
    """
    Handle user signup process using Django's UserCreationForm.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered signup page with user creation form, or redirects to feed upon successful signup.
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in immediately after signup
            return redirect("myapp:feed")
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})


@login_required
def create_ticket(request):
    """
    Handle the creation of a new ticket by the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered create ticket page with ticket form, or redirects to feed upon successful creation.
    """
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user  # Set the user to the currently logged-in user
            ticket.save()
            messages.success(request, "Ticket created successfully.")
            return redirect("myapp:feed")
    else:
        form = TicketForm()
    return render(request, "create_ticket.html", {"form": form})


@login_required
def create_review(request, ticket_id):
    """
    Handle the creation of a new review for a specific ticket.

    Args:
        request (HttpRequest): The HTTP request object.
        ticket_id (int): The ID of the ticket to review.

    Returns:
        HttpResponse: Rendered create review page with review form, or redirects to feed upon successful creation.
    """
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.ticket = ticket  # Link the review to the specified ticket
            review.user = request.user
            review.save()
            return redirect("myapp:feed")
    else:
        form = ReviewForm()
    return render(request, "create_review.html", {"form": form, "ticket": ticket})


@login_required
def create_ticket_review(request):
    """
    Handle the creation of a new ticket and review together by the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered create ticket and review page with combined form, or redirects to feed upon successful creation.
    """
    if request.method == "POST":
        ticket_form = TicketForm(request.POST, request.FILES)
        review_form = ReviewForm(request.POST)
        if ticket_form.is_valid() and review_form.is_valid():
            ticket = ticket_form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            review = review_form.save(commit=False)
            review.ticket = ticket
            review.user = request.user
            review.save()
            messages.success(request, "Ticket and Review created successfully.")
            return redirect("myapp:feed")
    else:
        ticket_form = TicketForm()
        review_form = ReviewForm()
    return render(
        request,
        "create_ticket_review.html",
        {"ticket_form": ticket_form, "review_form": review_form},
    )


@login_required
def follow_user(request):
    """
    Handle the process of following another user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered follow user page or error message if the user does not exist.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        try:
            user_to_follow = User.objects.get(username=username)
            if user_to_follow != request.user:
                UserFollows.objects.get_or_create(
                    user=request.user, followed_user=user_to_follow
                )
        except ObjectDoesNotExist:
            return render(request, "follow_user.html", {"error": "User does not exist"})
    return render(request, "follow_user.html")


@login_required
def manage_follows(request):
    """
    Manage the users the logged-in user is following and their followers.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered manage follows page with followers and following lists, and follow/unfollow form.
    """
    user = request.user
    followers = user.followers.all()
    following = user.following.all()
    if request.method == "POST":
        form = FollowForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            target_user = get_object_or_404(
                User, username=form.cleaned_data["username"]
            )
            if action == "follow":
                UserFollows.objects.get_or_create(user=user, followed_user=target_user)
            elif action == "unfollow":
                UserFollows.objects.filter(
                    user=user, followed_user=target_user
                ).delete()
            return redirect("myapp:manage_follows")
    else:
        form = FollowForm()

    return render(
        request,
        "manage_follows.html",
        {"followers": followers, "following": following, "form": form},
    )


@login_required
def followed_users(request):
    """
    Display the list of users the current user is following.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered followed users page with the list of followed users.
    """
    follows = UserFollows.objects.filter(user=request.user)
    return render(request, "followed_users.html", {"follows": follows})


def index(request):
    """
    Render the base template for the application.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered base template.
    """
    return render(request, "base.html")


@login_required
def add_ticket(request):
    """
    Handle the creation of a new ticket using a form.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered add ticket page with ticket form, or success message upon successful creation.
    """
    return handle_create_form(
        request, TicketForm, "add_ticket.html", "Ticket created successfully."
    )


@login_required
def edit_ticket(request, ticket_id):
    """
    Handle the editing of an existing ticket.

    Args:
        request (HttpRequest): The HTTP request object.
        ticket_id (int): The ID of the ticket to edit.

    Returns:
        HttpResponse: Rendered edit ticket page with ticket form, or redirects to dashboard upon successful edit.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == "POST":
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("myapp:dashboard"))
    else:
        form = TicketForm(instance=ticket)
    return render(request, "edit_ticket.html", {"form": form, "ticket": ticket})


@login_required
def delete_ticket(request, ticket_id):
    """
    Handle the deletion of an existing ticket by the user who created it.

    Args:
        request (HttpRequest): The HTTP request object.
        ticket_id (int): The ID of the ticket to delete.

    Returns:
        HttpResponse: Redirects to dashboard upon successful deletion, or rendered delete ticket page.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    
    if request.method == "POST":
        ticket.delete()
        return redirect(reverse("myapp:dashboard"))
    return render(request, "delete_ticket.html", {"ticket": ticket})


@login_required
def add_review(request):
    """
    Handle the creation of a new review using a form.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered add review page with review form, or success message upon successful creation.
    """
    return handle_create_form(
        request, ReviewForm, "add_review.html", "Review created successfully."
    )


@login_required
def request_review(request):
    """
    Handle requesting a review from another user for a specific ticket.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered request review page with review request form, or redirects to dashboard upon successful request.
    """
    if request.method == "POST":
        form = ReviewRequestForm(request.POST)
        if form.is_valid():
            requested_username = form.cleaned_data["requested_user"]
            requested_user = get_object_or_404(User, username=requested_username)
            review_request = ReviewRequest(
                requester=request.user,
                requested_user=requested_user,
                ticket=form.cleaned_data["ticket"],
            )
            review_request.save()
            return redirect("myapp:dashboard")
    else:
        form = ReviewRequestForm()

    return render(request, "request_review.html", {"form": form})


def edit_review(request, review_id):
    """
    Handle the editing of an existing review.

    Args:
        request (HttpRequest): The HTTP request object.
        review_id (int): The ID of the review to edit.

    Returns:
        HttpResponse: Rendered edit review page with review form, or redirects to dashboard upon successful edit.
    """
    review = get_object_or_404(Review, id=review_id)
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("myapp:dashboard"))
    else:
        form = ReviewForm(instance=review)
    return render(request, "edit_review.html", {"form": form, "review": review})


@login_required
@permission_required("myapp.delete_review", raise_exception=True)
def delete_review(request, review_id):
    """
    Handle the deletion of an existing review by the user who created it.

    Args:
        request (HttpRequest): The HTTP request object.
        review_id (int): The ID of the review to delete.

    Returns:
        HttpResponse: Redirects to dashboard upon successful deletion, or rendered delete review page.
    """
    review = get_object_or_404(Review, id=review_id, user=request.user)
    if request.method == "POST":
        review.delete()
        return redirect(reverse("myapp:dashboard"))
    return render(request, "delete_review.html", {"review": review})


def handle_create_form(request, form_class, template_name, success_message):
    """
    Handle form submission for creating a new instance of a given model.

    Args:
        request (HttpRequest): The HTTP request object.
        form_class (ModelForm): The form class to use for creating the instance.
        template_name (str): The template to render.
        success_message (str): The success message to display upon successful creation.

    Returns:
        HttpResponse: Rendered template with form, or redirects to feed upon successful creation.
    """
    if not request.user.has_perm("can_create_" + form_class._meta.model_name):
        messages.error(request, "You do not have permission to create.")
        return redirect("myapp:feed")
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            messages.success(request, success_message)
            return redirect("myapp:feed")
    else:
        form = form_class()
    return render(request, template_name, {"form": form})


def handle_edit_form(
    request, instance_id, model_class, form_class, template_name, success_message
):
    """
    Handle form submission for editing an existing instance of a given model.

    Args:
        request (HttpRequest): The HTTP request object.
        instance_id (int): The ID of the instance to edit.
        model_class (Model): The model class of the instance.
        form_class (ModelForm): The form class to use for editing the instance.
        template_name (str): The template to render.
        success_message (str): The success message to display upon successful edit.

    Returns:
        HttpResponse: Rendered template with form, or redirects to feed upon successful edit.
    """
    instance = get_object_or_404(model_class, pk=instance_id, user=request.user)
    if not request.user.has_perm("can_edit_" + model_class._meta.model_name):
        messages.error(request, "You do not have permission to edit.")
        return redirect("myapp:feed")
    if request.method == "POST":
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect("myapp:feed")
    else:
        form = form_class(instance=instance)
    return render(request, template_name, {"form": form, "instance": instance})


@login_required
def confirm_delete_review(request, review_id):
    """
    Display a confirmation page for deleting a review and handle the deletion.

    Args:
        request (HttpRequest): The HTTP request object.
        review_id (int): The ID of the review to delete.

    Returns:
        HttpResponse: Redirects to the feed upon successful deletion, or renders the confirmation page.
    """
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == "POST":
        review.delete()
        messages.success(request, "Review deleted successfully.")
        return redirect('myapp:feed')

    return render(request, "confirm_delete_review.html", {"review": review})

def handle_delete(request, instance_id, model_class, success_message):
    """
    Handle the deletion of an existing instance of a given model.

    Args:
        request (HttpRequest): The HTTP request object.
        instance_id (int): The ID of the instance to delete.
        model_class (Model): The model class of the instance.
        success_message (str): The success message to display upon successful deletion.

    Returns:
        HttpResponse: Redirects to feed upon successful deletion, or rendered base template.
    """
    instance = get_object_or_404(model_class, pk=instance_id, user=request.user)
    if not request.user.has_perm("can_delete_" + model_class._meta.model_name):
        messages.error(request, "You do not have permission to delete.")
        return redirect("myapp:feed")
    if request.method == "POST":
        instance.delete()
        messages.success(request, success_message)
        return redirect("myapp:feed")
    return render(request, "base.html", {"instance": instance})

@login_required
def block_user(request, user_id):
    """
    Block a user by adding them to the block list of the current user.

    Args:
        request (HttpRequest): The HTTP request object.
        user_id (int): The ID of the user to block.

    Returns:
        HttpResponse: Redirects back to the previous page or a specified URL.
    """
    user_to_block = get_object_or_404(User, id=user_id)

    if user_to_block == request.user:
        messages.error(request, "You cannot block yourself.")
        return redirect('myapp:dashboard')

    block, created = UserBlock.objects.get_or_create(blocker=request.user, blocked=user_to_block)

    if created:
        messages.success(request, f"You have blocked {user_to_block.username}.")
    else:
        messages.info(request, f"{user_to_block.username} is already blocked.")

    return redirect('myapp:dashboard')

@login_required
def manage_blocks(request):
    """
    Display a list of users blocked by the current user and provide options to block or unblock them.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered manage blocks page with a list of blocked users and a block form.
    """
    blocked_users = UserBlock.objects.filter(blocker=request.user).select_related('blocked')
    
    if request.method == "POST":
        if "block_user" in request.POST:
            username = request.POST.get("username")
            try:
                user_to_block = User.objects.get(username=username)
                if user_to_block == request.user:
                    messages.error(request, "You cannot block yourself.")
                else:
                    UserBlock.objects.get_or_create(blocker=request.user, blocked=user_to_block)
                    messages.success(request, f"You have blocked {user_to_block.username}.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
        
        elif "unblock_user" in request.POST:
            unblock_user_id = request.POST.get("unblock_user_id")
            try:
                user_to_unblock = User.objects.get(pk=unblock_user_id)
                UserBlock.objects.filter(blocker=request.user, blocked=user_to_unblock).delete()
                messages.success(request, f"You have unblocked {user_to_unblock.username}.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
        
        return redirect('myapp:manage_blocks')

    return render(request, "manage_blocks.html", {"blocked_users": blocked_users})

def is_blocked(blocker, blocked):
    """
    Check if a user has blocked another user.

    Args:
        blocker (User): The user who might have blocked another user.
        blocked (User): The user who might be blocked.

    Returns:
        bool: True if blocked, False otherwise.
    """
    return UserBlock.objects.filter(blocker=blocker, blocked=blocked).exists()

@login_required
@require_POST
def unfollow_user(request, user_id):
    """
    Handle the process of unfollowing a user.

    Args:
        request (HttpRequest): The HTTP request object.
        user_id (int): The ID of the user to unfollow.

    Returns:
        HttpResponse: Redirects to feed upon successful unfollowing, or error message if not following the user.
    """
    user_to_unfollow = get_object_or_404(User, id=user_id)
    if not UserFollows.objects.filter(
        user=request.user, followed_user=user_to_unfollow
    ).exists():
        messages.error(request, "You are not following this user.")
        return redirect("myapp:feed")
    UserFollows.objects.filter(
        user=request.user, followed_user=user_to_unfollow
    ).delete()
    messages.success(request, f"You have unfollowed {user_to_unfollow.username}.")
    return redirect("myapp:feed")


def custom_logout(request):
    """
    Handle the logout process for a user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Redirects to login page upon successful logout.
    """
    logout(request)
    return redirect("login")
