from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Job
from .serializers import JobCreateSerializer, JobResponseSerializer, JobStatusSerializer
from .tasks import process_guideline_job

@extend_schema(
    request=JobCreateSerializer,
    responses={201: JobResponseSerializer},
    description="Create a new guideline processing job"
)
@api_view(['POST'])
def create_job(request):
    """
    Create a new guideline ingest job.
    Returns an event_id that can be used to check job status.
    """
    serializer = JobCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Create job record
        job = Job.objects.create(
            input_text=serializer.validated_data['input_text']
        )
        
        # Queue the processing task
        process_guideline_job.delay(str(job.event_id))
        
        # Return event_id immediately
        response_serializer = JobResponseSerializer(job)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    responses={200: JobStatusSerializer, 404: None},
    description="Get job status and results by event_id"
)
@api_view(['GET'])
def get_job_status(request, event_id):
    """
    Get the status and results of a job by event_id.
    """
    try:
        job = Job.objects.get(event_id=event_id)
        serializer = JobStatusSerializer(job)
        return Response(serializer.data)
    except Job.DoesNotExist:
        return Response(
            {'error': 'Job not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )