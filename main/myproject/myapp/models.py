from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint


class Ticket(models.Model):
    """Model for tickets."""

    title = models.CharField(max_length=128)
    description = models.TextField(max_length=2048, blank=True)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(null=True, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Review(models.Model):
    """Model for reviews."""

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
    """Model for review requests."""

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
    ticket = models.ForeignKey(to="Ticket", on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review request from {self.requester.username} to {self.requested_user.username} for {self.ticket.title}"


class UserFollows(models.Model):
    """Model for user follows."""

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
