from django.urls import path
from scheduler.views import CreateEventView, EventOptionView, SignInEventView

urlpatterns = [
    path('create/', CreateEventView.as_view(), name='create-event'),
    path('event-options/', EventOptionView.as_view(), name='event-options'),
    path('<uuid:unique_id>/signin/', SignInEventView.as_view(), name='sign-in'),
]