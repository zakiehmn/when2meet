from django.urls import path
from scheduler.views import CreateEventView

urlpatterns = [
    path('create/', CreateEventView.as_view(), name='create-event')
]