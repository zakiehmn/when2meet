from rest_framework import serializers
from scheduler.models import (
    Event,
    EventDate,
    Attendee,
    SpecificDateAvailability,
    EventDayOfWeek,
    DayOfWeekChoices,
    EventTypeChoices,
)


class EventDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventDate
        fields  = ['date']

class EventDayOfWeekSerializer(serializers.ModelSerializer):
    day_label = serializers.SerializerMethodField()

    class Meta:
        model = EventDayOfWeek
        fields = ['day', 'day_label']

    def get_day_label(self, obj):
        return DayOfWeekChoices(obj.day).label

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'day' in data:
            day_label = data['day']
            try:
                day_value = {label: value for value, label in DayOfWeekChoices.choices}[day_label]
                data['day'] = day_value
            except KeyError:
                raise serializers.ValidationError({"day": f"'{day_label}' is not a valid choice."})
        return super().to_internal_value(data)


class EventSerializer(serializers.ModelSerializer):
    dates = EventDateSerializer(many=True, required=False)
    days_of_week = EventDayOfWeekSerializer(many=True, required=False)

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'start_time', 'end_time', 'timezone',
            'event_type', 'dates', 'days_of_week'
        ]

    def get_event_type_label(self, obj):
        return EventTypeChoices(obj.event_type).label

    def to_internal_value(self, data):
        if isinstance(data, dict):
            event_type_label = data.get('event_type')
            if event_type_label:
                try:
                    event_type_value = {label: value for value, label in EventTypeChoices.choices}[event_type_label]
                    data['event_type'] = event_type_value
                except KeyError:
                    raise serializers.ValidationError({"event_type": f"'{event_type_label}' is not a valid choice."})

        return super().to_internal_value(data)


    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Start time must be before the end time.")
        event_type = data.get('event_type', EventTypeChoices.SPECIFIC_DATES)
        print(event_type)
        dates = data.get('dates', [])
        days = data.get('days_of_week', [])
        if event_type == EventTypeChoices.SPECIFIC_DATES and days:
            raise serializers.ValidationError("For events with Specific Dates, days_of_week must not be provided.")
        if event_type == EventTypeChoices.DAYS_OF_WEEK and dates:
            raise serializers.ValidationError("For events with Days of Week, dates must not be provided.")
        return data

    def create(self, validated_data):
        dates_data = validated_data.pop('dates', [])
        days_data = validated_data.pop('days_of_week', [])
        event = Event.objects.create(**validated_data)
        for date_data in dates_data:
            EventDate.objects.create(event=event, **date_data)
        for day_data in days_data:
            e = EventDayOfWeek.objects.create(event=event, **day_data)
            print(e)
        return event


class AvailibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificDateAvailability
        fields = ['start_time', 'end_time']


class AttendeeSerializer(serializers.ModelSerializer):
    availibility_times = AvailibilitySerializer(many=True, read_only=True)
    class Meta:
        model = Attendee
        fields = ['id', 'name', 'availibility_times']

class EventDayOfWeekSerializer(serializers.ModelSerializer):
    day_label = serializers.SerializerMethodField()

    class Meta:
        model = EventDayOfWeek
        fields = ['day', 'day_label']

    def get_day_label(self, obj):
        return obj.get_day_display()

