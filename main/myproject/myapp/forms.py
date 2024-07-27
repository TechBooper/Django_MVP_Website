from django import forms
from .models import Ticket, Review
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):
    """Form for user registration."""

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        for fieldname in ["username", "password1", "password2"]:
            self.fields[fieldname].widget.attrs.update({"class": "form-control"})


class TicketForm(forms.ModelForm):
    """Form for creating and editing tickets."""

    class Meta:
        model = Ticket
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
        }


class ReviewForm(forms.ModelForm):
    """Form for creating and editing reviews."""

    class Meta:
        model = Review
        fields = ["rating", "headline", "body"]
        widgets = {
            "rating": forms.NumberInput(attrs={"class": "form-control"}),
            "headline": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control"}),
        }


class ReviewRequestForm(forms.Form):
    """Form for requesting a review from another user."""

    requested_user = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"placeholder": "Enter username", "class": "form-control"}
        ),
    )
    ticket = forms.ModelChoiceField(
        queryset=Ticket.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class FollowUserForm(forms.Form):
    """Form for following a user."""

    username = forms.CharField(
        max_length=170,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter a username to follow"}
        ),
    )


class FollowForm(forms.Form):
    """Form for managing follow and unfollow actions."""

    username = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    action = forms.ChoiceField(
        choices=[("follow", "Follow"), ("unfollow", "Unfollow")],
        widget=forms.HiddenInput(),
        initial="follow",
    )


class CombinedTicketReviewForm(forms.Form):
    """Form for creating a ticket and a review together."""

    title = forms.CharField(
        max_length=200, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control"})
    )
    rating = forms.IntegerField(
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    headline = forms.CharField(
        max_length=200, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    body = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control"}))
