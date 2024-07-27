from django import forms
from .models import Ticket, Review
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):
    """
    Form for user registration, extending the default UserCreationForm.

    Adds an email field to the default fields in UserCreationForm.

    Fields:
        - username: The user's chosen username.
        - email: Required email field with custom styling.
        - password1: The user's chosen password.
        - password2: Confirmation of the user's chosen password.
    """

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        """
        Customize widget attributes for form fields to add CSS classes for styling.

        Ensures that the username, password1, and password2 fields have a consistent appearance.
        """
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        for fieldname in ["username", "password1", "password2"]:
            self.fields[fieldname].widget.attrs.update({"class": "form-control"})


class TicketForm(forms.ModelForm):
    """
    Form for creating and editing tickets.

    This form is linked to the Ticket model and includes fields for the title and description of the ticket.

    Meta:
        model: Specifies that this form is for the Ticket model.
        fields: Specifies the fields to include in the form - 'title' and 'description'.
        widgets: Adds CSS classes to form fields for styling.
    """

    class Meta:
        model = Ticket
        fields = ["title", "description", "image"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
        }


class ReviewForm(forms.ModelForm):
    """
    Form for creating and editing reviews.

    This form is linked to the Review model and includes fields for the rating, headline, and body of the review.

    Meta:
        model: Specifies that this form is for the Review model.
        fields: Specifies the fields to include in the form - 'rating', 'headline', and 'body'.
        widgets: Adds CSS classes to form fields for styling.
    """

    RATING_CHOICES = [
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    ]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES, widget=forms.RadioSelect(attrs={"class": "star"})
    )

    class Meta:
        model = Review
        fields = ["rating", "headline", "body"]
        widgets = {
            "headline": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control"}),
        }


class ReviewRequestForm(forms.Form):
    """
    Form for requesting a review from another user.

    Allows users to specify another user and a ticket for which they want to request a review.

    Fields:
        - requested_user: The username of the user from whom the review is requested.
        - ticket: The ticket for which the review is requested.
    """

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
    """
    Form for following a user.

    Allows users to enter the username of the user they want to follow.

    Fields:
        - username: The username of the user to follow.
    """

    username = forms.CharField(
        max_length=170,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter a username to follow"}
        ),
    )


class FollowForm(forms.Form):
    """
    Form for managing follow and unfollow actions.

    Allows users to specify a username and an action (follow or unfollow) to manage their follows.

    Fields:
        - username: The username of the user to follow or unfollow.
        - action: Hidden field to specify the action (follow or unfollow).
    """

    username = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    action = forms.ChoiceField(
        choices=[("follow", "Follow"), ("unfollow", "Unfollow")],
        widget=forms.HiddenInput(),
        initial="follow",
    )


class CombinedTicketReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    ]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES, widget=forms.RadioSelect(attrs={"class": "star"})
    )
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control-file"}),
    )

    class Meta:
        model = Ticket
        fields = [
            "title",
            "description",
            "image",
            "rating",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
            "headline": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        ticket = super().save(commit=False)
        review = Review(
            rating=self.cleaned_data["rating"],
            headline=self.cleaned_data["headline"],
            body=self.cleaned_data["body"],
            ticket=ticket,
            user=ticket.user,
        )
        if commit:
            ticket.save()
            review.save()
        return ticket, review
