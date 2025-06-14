from rest_framework import serializers
from .models import Job

class JobCreateSerializer(serializers.Serializer):
    input_text = serializers.CharField(max_length=10000)
    
class JobResponseSerializer(serializers.ModelSerializer):
    event_id = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = Job
        fields = ['event_id']

class JobStatusSerializer(serializers.ModelSerializer):
    result = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = ['event_id', 'status', 'result', 'created_at', 'updated_at']
    
    def get_result(self, obj):
        if obj.status == 'completed':
            return {
                'summary': obj.summary,
                'checklist': obj.checklist
            }
        elif obj.status == 'failed':
            return {
                'error': obj.error_message
            }
        return None