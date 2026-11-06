
from django.urls import path
from django.views.generic.base import RedirectView
from django.templatetags.static import static

from . import views

urlpatterns = [
    # path('favicon.ico', RedirectView.as_view(url=static('favicon.ico'))),
    path("", views.create_message, name="create_message"),
    path("latest/", views.latest_message, name="latest_message"),
    path("history/", views.message_history, name="message_history"),
]
