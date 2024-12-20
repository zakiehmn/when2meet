from rest_framework import serializers
from scheduler.models import Event

class EventSerializer(serializers.ModelSerializer):
    class meta:
        model = Event
        fields = ['id', 'name', 'start_date', 'end_date', 'start_time', 'end_time', 'timezone']

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date must be before or equal to the end date.")
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Start time must be before the end time.")
        return data


