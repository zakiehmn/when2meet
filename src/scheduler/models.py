from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.conf import settings
import pytz
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from scheduler.managers import AttendeeManager



class Event(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50, choices=[(tz, tz) for tz in pytz.all_timezones], default="UTC")
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True)

    def get_event_link(self):
        return f"{settings.BASE_URL}/{self.unique_id}"

    def __str__(self):
        return self.name


class EventDate(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="dates")
    date = models.DateField()

    def __str__(self):
        return f"{self.event.name} - {self.date}"


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


    def __str__(self):
        return self.name


class Availability(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name="availability_times")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['attendee', 'start_time'], name='unique_attendee_start_time')]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    def __str__(self):
        return f"{self.attendee.name}: {self.start_time} - {self.end_time}"