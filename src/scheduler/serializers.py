from rest_framework import serializers
from scheduler.models import Event, EventDate


class EventDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventDate
        fields  = ['date']


class EventSerializer(serializers.ModelSerializer):
    dates = EventDateSerializer(many=True)

    class Meta:
        model = Event
        fields = ['id', 'name', 'start_time', 'end_time', 'timezone', 'dates']

    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Start time must be before the end time.")
        return data

    def create(self, validated_data):
        dates_data = validated_data.pop('dates')
        event = Event.objects.create(**validated_data)
        for date in dates_data:
            EventDate.objects.create(event=event, **date)
        return event




