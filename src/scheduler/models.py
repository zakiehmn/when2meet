from django.db import models
from django.core.exceptions import ValidationError
import pytz
import uuid

class Event(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50, choices=[(tz, tz) for tz in pytz.all_timezones], default="UTC")
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True)

    def get_event_link(self):
        return f"http://127.0.0.1:8000/{self.unique_id}"

    def __str__(self):
        return self.name


class EventDate(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="dates")
    date = models.DateField()

    def __str__(self):
        return f"{self.event.name} - {self.date}"


class Attendee(models.Model):
    name = models.CharField(max_length=30)
    password = models.CharField(max_length=128, null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attendees")
    timezone = models.CharField(max_length=50, choices=[(tz, tz) for tz in pytz.all_timezones], default="UTC")

    def __str__(self):
        return self.name


class Availability(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name="availability_times")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    def __str__(self):
        return f"{self.attendee.name}: {self.start_time} - {self.end_time}"