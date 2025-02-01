from django.urls import path
from scheduler.views import CreateEventView, EventOptionView

urlpatterns = [
    path('create/', CreateEventView.as_view(), name='create-event'),
    path('event-options/', EventOptionView.as_view(), name='event-options'),
]