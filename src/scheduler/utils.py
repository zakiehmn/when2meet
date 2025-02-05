from django.shortcuts import get_object_or_404
from scheduler.models import Event, Attendee, Availability
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken


def get_event_by_unique_id(unique_id):
    return  get_object_or_404(Event, unique_id=unique_id)

def get_attendee_by_event_and_name(event: Event, name: str):
    return Attendee.objects.filter(event=event, name=name).first()

def create_attendee(event: Event, name: str, password="", timezone="UTC"):
    attendee =  Attendee.objects.create(event=event, name=name, timezone=timezone)
    if password:
        attendee.set_password(password)
    else:
        attendee.set_unusable_password()
    attendee.save()
    return attendee


def get_attendee_by_id(event: Event, attendee_id):
    return get_object_or_404(Attendee, id=attendee_id, event=event)

def create_avalibility(attendee: Attendee, start_time, end_time):
    if end_time <= start_time:
        raise ValueError("End time must be after start time.")

    availability = Availability.objects.create(
        attendee=attendee,
        start_time=start_time,
        end_time=end_time
        )

    return availability

def get_existing_availability(attendee: Attendee, start_time, end_time):
    return Availability.objects.filter(
        attendee=attendee,
        start_time=start_time,
        end_time=end_time
        ).first()

def get_jwt_token(attendee):
    refresh = RefreshToken.for_user(attendee)
    refresh['name'] = attendee.name
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_attendee_availability(attendee):
    return Availability.objects.filter(attendee=attendee)

def get_event_availabilities(event):
    return Availability.objects.filter(attendee__event=event)

def get_availabilities_by_start_time(event, query_time):
    availabilities = Availability.objects.filter(
        attendee__event=event,
        start_time=query_time
    ).select_related('attendee')
    return availabilities