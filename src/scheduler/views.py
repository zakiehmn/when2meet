from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from scheduler.serializers import EventSerializer, AttendeeSerializer, EventDayOfWeekSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from scheduler.authentication import CustomJWTAuthentication
from datetime import datetime
import pytz

from scheduler.utils import(
    get_event_by_unique_id,
    get_attendee_by_event_and_name,
    create_attendee,
    create_specific_date_availability,
    get_existing_specific_date_availability,
    get_jwt_token,
    get_attendee_availabilitiy_list,
    get_event_availabilities_list,
    get_attendees_availability_count,
    create_day_of_week_availability,
    get_existing_day_availability,
    get_existing_days_of_week_availability,
)



class EventView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]


    def get_authenticators(self):
        if self.request.method == "POST":
            return []
        return super().get_authenticators()

    def get_permissions(self):

        return [AllowAny()]

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

        event_serializer = EventSerializer(event)
        time_zones = pytz.all_timezones

        attendee = request.user
        attendee_availabilities = []

        if request.user.is_authenticated:
            attendee = request.user
            attendee_availabilities = get_attendee_availabilitiy_list(attendee)
            attendee_timezone = attendee.timezone if attendee.timezone else "Asia/Tehran"
        else:
            attendee_availabilities = []
            attendee_timezone = "Asia/Tehran"

        all_event_availabilities = get_event_availabilities_list(event)


        response_data = {
            "event": event_serializer.data,
            "attendees_with_availability_count": get_attendees_availability_count(event),
            "timezone_options": time_zones,
            "attendee_timezone": attendee_timezone,
            "attendee_availabilities": attendee_availabilities,
            "all_event_availabilities": all_event_availabilities,
        }
        return Response(response_data, status=status.HTTP_200_OK)






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

        if attendee:
            valid, error = attendee.validate_password(password)
            if not valid:
                return Response({"error": error}, status=status.HTTP_401_UNAUTHORIZED)
            message = "Login successful!"
            status_code = status.HTTP_200_OK
        else:
            attendee = create_attendee(event, name, password, timezone)
            message = "Sign up successful!"
            status_code = status.HTTP_201_CREATED

        tokens = get_jwt_token(attendee)
        serializer = AttendeeSerializer(attendee)

        return Response({
            "message": message,
            "attendee": serializer.data,
            **tokens,
        }, status=status_code)


class SpecificDateAvailabilityView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, unique_id):
        attendee = request.user
        event = get_event_by_unique_id(unique_id)

        if not event:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        if attendee.event != event:
            return Response(
                {"error": "You are not authorized to modify availability for this event."},
                status=status.HTTP_403_FORBIDDEN
            )

        start_time_str = request.data.get("start_time")
        end_time_str = request.data.get("end_time")

        if not start_time_str or not end_time_str:
            return Response(
                {"error": "Start time and end time are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if end_time <= start_time:
            return Response(
                {"error": "End time must be after start time."},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_availability = get_existing_specific_date_availability(attendee, start_time, end_time)
        if existing_availability:
            avail = existing_availability
            message = "Availability already exists."
            status_code = status.HTTP_200_OK
        else:
            avail = create_specific_date_availability(attendee, start_time, end_time)
            message = "Availability successfully added."
            status_code = status.HTTP_201_CREATED

        response_data = {
            "message": message,
            "availability": {
                "id": avail.id,
                "start_time": avail.start_time,
                "end_time": avail.end_time
            }
        }

        return Response(response_data, status=status_code)

    def delete(self, request, unique_id):
        attendee = request.user
        event = get_event_by_unique_id(unique_id)

        if not event:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        if attendee.event != event:
            return Response(
                {"error": "You are not authorized to modify availability for this event."},
                status=status.HTTP_403_FORBIDDEN
            )

        start_time_str = request.data.get("start_time")
        end_time_str = request.data.get("end_time")

        if not start_time_str or not end_time_str:
            return Response(
                {"error": "Start time and end time are required for deletion."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use ISO 8601 format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_availability = get_existing_specific_date_availability(attendee, start_time, end_time)
        if not existing_availability:
            return Response(
                {"error": "No matching availability found."},
                status=status.HTTP_404_NOT_FOUND
            )

        existing_availability.delete()
        return Response(
            {"message": "Availability successfully removed."},
            status=status.HTTP_200_OK
        )

class DayOfWeekAvailabilityView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    DAY_MAPPING = {
    "دوشنبه": 0,
    "سه‌شنبه": 1,
    "چهارشنبه": 2,
    "پنج‌شنبه": 3,
    "جمعه": 4,
    "شنبه": 5,
    "یکشنبه": 6
    }

    def post(self, request, unique_id):
        attendee = request.user
        event = get_event_by_unique_id(unique_id)

        if not event:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        if attendee.event != event:
            return Response(
                {"error": "You are not authorized to modify availability for this event."},
                status=status.HTTP_403_FORBIDDEN
            )

        day_name = request.data.get("day")
        start_time_str = request.data.get("start_time")

        if not day_name or not start_time_str:
            return Response(
                {"error": "Day and start time are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        day_number = self.DAY_MAPPING.get(day_name)
        if day_number is None:
            return Response(
                {"error": "Invalid day name. Use Persian days (e.g., 'جمعه')."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_hour = int(start_time_str.split(":")[0])
        except ValueError:
            return Response({"error": "Invalid start time format. Use 'HH:MM'."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not (0 <= start_hour <= 23):
            return Response({"error": "Start hour must be between 0 and 23."},
                            status=status.HTTP_400_BAD_REQUEST)

        existing_availability = get_existing_day_availability(attendee, day_number, start_hour)

        if existing_availability:
            avail = existing_availability
            message = "Availability already exists."
            status_code = status.HTTP_200_OK
        else:
            avail = create_day_of_week_availability(event, attendee, day_number, start_hour)
            message = "Availability successfully added."
            status_code = status.HTTP_201_CREATED

        serializer = EventDayOfWeekSerializer(avail.event_day_of_week)

        response_data = {
            "message": message,
            "availability": {
                "id": avail.id,
                "day_of_week": serializer.data,
                "start_hour": avail.get_formated_start_hour()
            }
        }

        return Response(response_data, status=status_code)

    def delete(self, request, unique_id):
        attendee = request.user
        event = get_event_by_unique_id(unique_id)

        if not event:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        if attendee.event != event:
            return Response(
                {"error": "You are not authorized to modify availability for this event."},
                status=status.HTTP_403_FORBIDDEN
            )
        start_hour = request.data.get('start_time')
        if start_hour is None:
            return Response(
                {"error": "Start time is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        day_name = request.data.get('day')
        if day_name is None:
            return Response(
                {"error": "Day is required."},
                status=status.HTTP_400_BAD_REQUEST
            )


        start_hour = start_hour.split(':')[0]
        try:
            start_hour = int(start_hour)
        except ValueError:
            return Response(
                {"error": "Invalid start time."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not (0 <= start_hour <= 23):
            return Response({"error": "Start hour must be between 0 and 23."},
                            status=status.HTTP_400_BAD_REQUEST)

        day_number = self.DAY_MAPPING.get(day_name)
        if day_number is None:
            return Response(
                {"error": "Invalid day name. Use Persian days (e.g., 'جمعه')."},
                status=status.HTTP_400_BAD_REQUEST
            )


        existing_availability = get_existing_days_of_week_availability(attendee, day_number, start_hour)
        if not existing_availability:
            return Response(
                {"error": "No matching availability found."},
                status=status.HTTP_404_NOT_FOUND
            )

        existing_availability.delete()
        return Response(
            {"message": "Availability successfully removed."},
            status=status.HTTP_200_OK
        )
