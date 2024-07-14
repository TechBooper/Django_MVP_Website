# myapp/models.py
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint

class Ticket(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Review(models.Model):
    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    headline = models.CharField(max_length=128)
    body = models.CharField(max_length=8192, blank=True)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review for {self.ticket.title} by {self.user.username}'



class UserFollows(models.Model):
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='following', on_delete=models.CASCADE)
    followed_user = models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='followers', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'followed_user'], name='unique_user_follow')
        ]
        app_label = 'myapp'
        verbose_name = 'User Follow'
        verbose_name_plural = 'User Follows'

    def __str__(self):
        return f'{self.user.username} follows {self.followed_user.username}'

