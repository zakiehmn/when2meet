from django.urls import path
from scheduler.views import (
    EventView,
    EventOptionView,
    SignInEventView,
    AttendeeAvailabilityView,
)

urlpatterns = [
    path('create/', EventView.as_view(), name='create-event'),
    path('options/', EventOptionView.as_view(), name='event-options'),
    path('<uuid:unique_id>/signin/', SignInEventView.as_view(), name='sign-in'),
    path('<uuid:unique_id>/availability/', AttendeeAvailabilityView.as_view(), name='attendee_availability'),
    path('<uuid:unique_id>/', EventView.as_view(), name='create-event'),
]