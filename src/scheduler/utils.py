from django.shortcuts import get_object_or_404
from scheduler.models import Event, Attendee


def get_event_by_unique_id(unique_id):
    return  get_object_or_404(Event, unique_id=unique_id)

def get_attendee_by_event_and_name(event, name):
    return Attendee.objects.filter(event=event, name=name).first()

def create_attendee(event: Event, name, password=None, timezone='Iran'):
    return Attendee.objects.create(event=event, name=name, password=password, timezone=timezone)