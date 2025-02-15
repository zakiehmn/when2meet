from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.conf import settings
import pytz
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from scheduler.managers import AttendeeManager


class EventTypeChoices(models.IntegerChoices):
    SPECIFIC_DATES = 0, "Specific Dates"
    DAYS_OF_WEEK = 1, "Days of Week"

class Event(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50, choices=[(tz, tz) for tz in pytz.all_timezones], default="UTC")
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True)
    event_type = models.IntegerField(choices=EventTypeChoices.choices)

    def get_event_link(self):
        return f"{settings.BASE_URL}/{self.unique_id}"

    def __str__(self):
        return self.name


class EventDate(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="dates")
    date = models.DateField()

    def __str__(self):
        return f"{self.event.name} - {self.date}"

class DayOfWeekChoices(models.IntegerChoices):
    MONDAY = 0, "دوشنبه"
    TUESDAY = 1, "سه‌شنبه"
    WEDNESDAY = 2, "چهارشنبه"
    THURSDAY = 3, "پنج‌شنبه"
    FRIDAY = 4, "جمعه"
    SATURDAY = 5, "شنبه"
    SUNDAY = 6, "یکشنبه"

class EventDayOfWeek(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="days_of_week")
    day = models.IntegerField(choices=DayOfWeekChoices.choices)

    def get_day_label(self):
        return DayOfWeekChoices(self.day).label

    def __str__(self):
        return f"{self.event.name} - {DayOfWeekChoices(self.day).label}"

class Attendee(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=30)
    password = models.CharField(max_length=128, blank=True, default="")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attendees")
    timezone = models.CharField(max_length=50, choices=[(tz, tz) for tz in pytz.all_timezones], default="UTC")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = AttendeeManager()

    USERNAME_FIELD = "id"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'event'], name='unique_name_in_event')
        ]

    def validate_password(self, password):
        if self.has_usable_password():
            if not password:
                return False, "Password required."
            if not self.check_password(password):
                return False, "Incorrect password."
        return True, None

    def __str__(self):
        return self.name


class SpecificDateAvailability(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name="specific_date_availabilities")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['attendee', 'start_time'], name='unique_attendee_specific_date_time')]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    def __str__(self):
        return f"{self.attendee.name}: {self.start_time} - {self.end_time}"


class DayOfWeekAvailability(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name="day_of_week_availabilities")
    event_day_of_week = models.ForeignKey(EventDayOfWeek, on_delete=models.CASCADE, related_name="availabilities")
    start_hour = models.IntegerField(choices=[(i, f"{i}:00") for i in range(24)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['attendee', 'event_day_of_week', 'start_hour'], name='unique_attendee_day_of_week_time')
        ]

    def clean(self):
        if self.start_hour < 0 or self.start_hour > 23:
            raise ValidationError("Hour must be between 0 and 23.")

    def get_formated_start_hour(self):
        if self.start_hour < 10:
            return f"0{self.start_hour}:00"
        return f"{self.start_hour}:00"

    def __str__(self):
        start_time = f"{self.start_hour}:00"
        return f"{self.attendee.name}: {DayOfWeekChoices(self.event_day_of_week.day).label} - {start_time}"
