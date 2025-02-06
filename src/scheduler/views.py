from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from scheduler.serializers import EventSerializer, AttendeeSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from scheduler.authentication import CustomJWTAuthentication
from datetime import datetime
import pytz

from scheduler.utils import(
    get_event_by_unique_id,
    get_attendee_by_event_and_name,
    create_attendee,
    get_attendee_by_id,
    create_avalibility,
    get_existing_availability,
    get_jwt_token,
    get_attendee_availability,
    get_event_availabilities,
    get_availabilities_by_start_time,
)



class EventView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]


    def get_authenticators(self):
        if self.request.method == "POST":
            return []
        return super().get_authenticators()

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return super().get_permissions()

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            event = serializer.save()
            return Response({
                'message': 'Event created successfully!',
                'event_link': event.get_event_link()
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, unique_id):
        event = get_event_by_unique_id(unique_id)
        if not event:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        time_zones = pytz.all_timezones

        attendee = request.user
        attendee_availabilities = []

        if attendee:
            attendee_availabilities = get_attendee_availability(attendee)

        all_event_availabilities = get_event_availabilities(event)

        return Response({
            "timezone_options": time_zones,
            "attendee_timezone": attendee.timezone if attendee else None,
            "attendee_availabilities": [
                {"id": avail.id, "start_time": avail.start_time, "end_time": avail.end_time}
                for avail in attendee_availabilities
            ],
            "all_event_availabilities": [
                {"attendee": avail.attendee.name, "id": avail.id, "start_time": avail.start_time, "end_time": avail.end_time}
                for avail in all_event_availabilities
            ]
        })





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
    authentication_classes = [CustomJWTAuthentication]

    def post(self, request, unique_id):
        event = get_event_by_unique_id(unique_id)
        if not event:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get('name')
        password = request.data.get('password')
        timezone = request.data.get('timezone', event.timezone)

        attendee = get_attendee_by_event_and_name(event, name)
        is_new = False

        if attendee:
            if password:
                if not attendee.check_password(password):
                    return Response({"error": "Incorrect password."}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                if attendee.has_usable_password():
                    return Response({"error": "Password required."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            attendee = create_attendee(event, name, password, timezone)
            is_new = True

        tokens = get_jwt_token(attendee)
        serializer = AttendeeSerializer(attendee)

        return Response({
            "message": "Sign up successful!" if is_new else "Login successful!",
            "attendee": serializer.data,
            **tokens,
        }, status=status.HTTP_201_CREATED if is_new else status.HTTP_200_OK)



class AttendeeAvailabilityView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, unique_id):
        attendee = request.user
        event = get_event_by_unique_id(unique_id)

        if attendee.event != event:
            return Response({"error": "You are not authorized to modify availability for this event."},
                             status=status.HTTP_403_FORBIDDEN)


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

        existing_availability = get_existing_availability(attendee, start_time, end_time)
        if existing_availability:
            existing_availability.delete()
            return Response({"message": "availability successfully removed."}, status=status.HTTP_200_OK)

        availability = create_avalibility(attendee, start_time, end_time)

        return Response({
            "message": "Availability successfully added.",
            "availability": {
                "id": availability.id,
                "start_time": availability.start_time,
                "end_time": availability.end_time
            }
        }, status=status.HTTP_201_CREATED)

    def get(self, request, unique_id):
        time_str = request.query_params.get('time')
        if not time_str:
            return Response({"error": "The 'time' query parameter  is required."}, status=status.HTTP_400_BAD_REQUEST)

        query_time = parse_datetime(time_str)
        if not query_time:
            return Response({"error": "Invalid time format. Please use ISO 8601 format."}, status=status.HTTP_400_BAD_REQUEST)

        if query_time.tzinfo is None:
            query_time = pytz.UTC.localize(query_time)

        event = get_event_by_unique_id(unique_id)
        if not event:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        availabilities = get_availabilities_by_start_time(event, query_time)

        attendees = [{"name": avail.attendee.name} for avail in availabilities]

        return Response({
            "available_attendees": attendees
        }, status=status.HTTP_200_OK)

