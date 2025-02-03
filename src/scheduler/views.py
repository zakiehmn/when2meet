from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from scheduler.serializers import EventSerializer, AttendeeSerializer
from datetime import datetime, timedelta
from scheduler.models import Event
import pytz

from scheduler.utils import(
    get_event_by_unique_id,
    get_attendee_by_event_and_name,
    create_attendee,
    get_attendee_by_id,
    create_avalibility,
    get_existing_availibility,
)



class CreateEventView(APIView):
    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            event = serializer.save()
            return Response({
                'message': 'Event created successfully!',
                'event_link': event.get_event_link()
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventOptionView(APIView):
    def get(self, request):
        # TODO
        time_slots = [f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'}" for hour in range(24)]
        time_zones = pytz.all_timezones
        return Response({
                "date_options": ["specific_dates", "days_of_week"],
                "time_options": {
                    "no_earlier_than": time_slots,
                    "no_later_than": time_slots
                },
                "time_zones": time_zones
            })


class SignInEventView(APIView):
    def post(self, request, unique_id):
        event = get_event_by_unique_id(unique_id)
        name = request.data.get('name')
        password = request.data.get('password', None)
        timezone = request.data.get('timezone', event.timezone)
        attendee = get_attendee_by_event_and_name(event, name)

        if attendee:
            if attendee.password and attendee.password != password:
                return Response({"error": "Incorrect password."
                                 }, status=status.HTTP_401_UNAUTHORIZED)
            serializer = AttendeeSerializer(attendee)
            return Response({"message": "Login successful!",
                             "attendee": serializer.data
                             }, status=status.HTTP_200_OK)

        new_attendee = create_attendee(event, name, password, timezone)
        serializer = AttendeeSerializer(new_attendee)
        return Response({"message": "Sign up successful!",
                         "attendee": serializer.data
                         }, status=status.HTTP_201_CREATED)


class AttendeeAvailibilityView(APIView):
    def post(self, request, unique_id, attendee_id):
        event = get_event_by_unique_id(unique_id)
        attendee = get_attendee_by_id(event, attendee_id)

        start_time_str = request.data.get("start_time")
        end_time_str = request.data.get("end_time")

        if not start_time_str or not end_time_str:
            return Response({"error": "Start time and end time are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return Response({"error": "Invalid date format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)."})

        if end_time <= start_time:
            return Response({"error": "End time must be after start time."},
                             status=status.HTTP_400_BAD_REQUEST)

        existing_availibility = get_existing_availibility(attendee, start_time, end_time)
        if existing_availibility:
            existing_availibility.delete()
            return Response({"message": "Availibility successfully removed."}, status=status.HTTP_200_OK)

        availibility = create_avalibility(attendee, start_time, end_time)

        return Response({
            "message": "Availability successfully added.",
            "availibility": {
                "id": availibility.id,
                "start_time": availibility.start_time,
                "end_time": availibility.end_time
            }
        }, status=status.HTTP_201_CREATED)








