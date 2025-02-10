from django.shortcuts import get_object_or_404
from scheduler.models import (
    Event,
    Attendee,
    SpecificDateAvailability,
    DayOfWeekAvailability,
    EventDayOfWeek,
    EventTypeChoices,
)
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from collections import Counter
from datetime import datetime
import pytz


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


def create_specific_date_availability(attendee: Attendee, start_time, end_time):
    if end_time <= start_time:
        raise ValueError("End time must be after start time.")

    availability = SpecificDateAvailability.objects.create(
        attendee=attendee,
        start_time=start_time,
        end_time=end_time
        )

    return availability

def get_existing_specific_date_availability(attendee: Attendee, start_time, end_time):
    return SpecificDateAvailability.objects.filter(
        attendee=attendee,
        start_time=start_time,
        end_time=end_time
        ).first()

def get_existing_days_of_week_availability(attendee: Attendee, day, start_hour):
    return DayOfWeekAvailability.objects.filter(
        attendee=attendee,
        start_hour=start_hour,
        event_day_of_week__day=day,
        event_day_of_week__event=attendee.event,
        ).first()

def get_jwt_token(attendee):
    refresh = RefreshToken.for_user(attendee)
    refresh['name'] = attendee.name
    access_token = refresh.access_token
    expiry_timestamp = access_token["exp"]
    expiry_datetime = datetime.fromtimestamp(expiry_timestamp, tz=pytz.UTC)
    return {
        'refresh': str(refresh),
        'access': str(access_token),
        'access_expires': expiry_datetime.isoformat(),
    }

def get_attendee_availabilitiy_list(attendee):
    event = attendee.event
    if event.event_type == EventTypeChoices.SPECIFIC_DATES:
        attendee_availabilities = SpecificDateAvailability.objects.filter(attendee=attendee)
        return [{"id": avail.id, "start_time": avail.start_time, "end_time": avail.end_time}
                for avail in attendee_availabilities]
    elif event.event_type == EventTypeChoices.DAYS_OF_WEEK:
        attendee_availabilities = DayOfWeekAvailability.objects.filter(attendee=attendee).prefetch_related('event_day_of_week')
        return [{"id": avail.id, "day": avail.event_day_of_week.get_day_label(), "start_time": avail.get_formated_start_hour()}
                for avail in attendee_availabilities]
    else:
        return []



def get_event_availabilities_list(event):
    if event.event_type == EventTypeChoices.SPECIFIC_DATES:
        all_event_availabilities =  SpecificDateAvailability.objects.filter(attendee__event=event)
        return [
                {"attendee": avail.attendee.name,
                "id": avail.id, "start_time": avail.start_time,
                "end_time": avail.end_time}
                for avail in all_event_availabilities
            ]
    elif event.event_type == EventTypeChoices.DAYS_OF_WEEK:
        all_event_availabilities = DayOfWeekAvailability.objects.filter(attendee__event=event).prefetch_related('event_day_of_week')
        return [
                {"attendee": avail.attendee.name,
                "id": avail.id, "day": avail.event_day_of_week.get_day_label(),
                "start_time": avail.get_formated_start_hour()}
                for avail in all_event_availabilities
            ]
    else:
        return []


def get_attendees_availability_count(event):
    """Returns the unique count of attendees with at least one Availability for the event."""
    if event.event_type == EventTypeChoices.SPECIFIC_DATES:
        return SpecificDateAvailability.objects.filter(
        attendee__event=event
    ).values('attendee').distinct().count()
    elif event.event_type == EventTypeChoices.DAYS_OF_WEEK:
        return DayOfWeekAvailability.objects.filter(
        attendee__event=event
    ).values('attendee').distinct().count()
    else:
        return []



def create_day_of_week_availability(event, attendee, day_number, start_hour):
    event_day_of_week = EventDayOfWeek.objects.filter(event=event, day=day_number).first()
    return DayOfWeekAvailability.objects.create(
        attendee=attendee,
        event_day_of_week=event_day_of_week,
        start_hour=start_hour
    )

def get_existing_day_availability(attendee, day_number, start_hour):
    event_day_of_week = EventDayOfWeek.objects.filter(event=attendee.event, day=day_number).last()
    return DayOfWeekAvailability.objects.filter(
        attendee=attendee,
        event_day_of_week=event_day_of_week,
        start_hour=start_hour
    ).first()


