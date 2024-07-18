from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path("oauth/kakao", views.get_kakao_auth_url),
    path("oauth/kakao/redirect", views.kakao_redirect),
]
