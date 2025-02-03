from django.shortcuts import get_object_or_404
from scheduler.models import Event, Attendee, Availability


def get_event_by_unique_id(unique_id):
    return  get_object_or_404(Event, unique_id=unique_id)

def get_attendee_by_event_and_name(event, name):
    return Attendee.objects.filter(event=event, name=name).first()

def create_attendee(event: Event, name, password=None, timezone="UTC"):
    return Attendee.objects.create(event=event, name=name, password=password, timezone=timezone)

def get_attendee_by_id(event: Event, attendee_id):
    return get_object_or_404(Attendee, id=attendee_id, event=event)

def create_avalibility(attendee: Attendee, start_time, end_time):
    if end_time <= start_time:
        raise ValueError("End time must be after start time.")

    availibility = Availability.objects.create(
        attendee=attendee,
        start_time=start_time,
        end_time=end_time
        )

    return availibility

def get_existing_availibility(attendee: Attendee, start_time, end_time):
    return Availability.objects.filter(
        attendee=attendee,
        start_time=start_time,
        end_time=end_time
        ).first()

