# myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from myapp import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("myapp.urls")),
    path("", views.index, name="base"),
    path(
        "accounts/", include("django.contrib.auth.urls")
    ),  # Include built-in auth URLs
]
