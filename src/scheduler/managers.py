from django.contrib.auth.models import BaseUserManager


class AttendeeManager(BaseUserManager):
    def create_user(self, name, event, password=None, timezone="UTC"):
        if not name:
            raise ValueError("The Name field must be set")
        if not event:
            raise ValueError("The Event field must be set")

        attendee = self.model(name=name, event=event, timezone=timezone)
        if password:
            attendee.set_password(password)
        attendee.save(using=self._db)
        return attendee

    def create_superuser(self, name, event, password):
        attendee = self.create_user(name=name, event=event, password=password)
        attendee.is_staff = True
        attendee.is_superuser = True
        attendee.save(using=self._db)
        return attendee