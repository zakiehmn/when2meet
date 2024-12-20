from django.db import models
from django.core.exceptions import ValidationError
import pytz

class Event(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50, choices=[(tz, tz) for tz in pytz.all_timezones], default="UTC")

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("Start date must be before end date.")
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    def __str__(self):
        return self.name


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