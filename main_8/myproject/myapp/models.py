from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint


class Ticket(models.Model):
    """
    Model representing a ticket.

    Attributes:
        title (str): The title of the ticket.
        description (str): The detailed description of the ticket.
        user (User): The user who created the ticket.
        image (ImageField): An optional image associated with the ticket.
        time_created (datetime): The date and time when the ticket was created.
    """

    title = models.CharField(max_length=128)
    description = models.TextField(max_length=2048, blank=True)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="tickets/", null=True, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Review(models.Model):
    """
    Model representing a review for a ticket.

    Attributes:
        ticket (Ticket): The ticket that the review is associated with.
        rating (int): The rating given by the user, ranging from 0 to 5.
        headline (str): The headline of the review.
        body (str): The detailed body of the review.
        user (User): The user who wrote the review.
        time_created (datetime): The date and time when the review was created.
    """

    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    headline = models.CharField(max_length=128)
    body = models.TextField(max_length=8192, blank=True)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.ticket.title} by {self.user.username}"


class ReviewRequest(models.Model):
    """
    Model representing a request for a review of a ticket.

    Attributes:
        requester (User): The user who made the review request.
        requested_user (User): The user who is requested to write the review.
        ticket (Ticket): The ticket for which the review is requested.
        time_created (datetime): The date and time when the review request was created.
    """

    requester = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requests_made",
    )
    requested_user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requests_received",
    )
    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review request from {self.requester.username} to {self.requested_user.username} for {self.ticket.title}"


class UserFollows(models.Model):
    """
    Model representing a user's following relationship with another user.

    Attributes:
        user (User): The user who is following another user.
        followed_user (User): The user who is being followed.
    """

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, related_name="following", on_delete=models.CASCADE
    )
    followed_user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, related_name="followers", on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "followed_user"], name="unique_user_follow"
            )
        ]
        app_label = "myapp"
        verbose_name = "User Follow"
        verbose_name_plural = "User Follows"

    def __str__(self):
        return f"{self.user.username} follows {self.followed_user.username}"
