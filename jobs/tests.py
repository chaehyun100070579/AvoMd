from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
from .models import Job
from .tasks import process_guideline_job

class JobModelTest(TestCase):
    def test_job_creation(self):
        """Test that a job can be created with default values"""
        job = Job.objects.create(input_text="Test guideline text")
        self.assertIsNotNone(job.event_id)
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.input_text, "Test guideline text")

class JobAPITest(APITestCase):
    def test_create_job(self):
        """Test job creation endpoint"""
        url = reverse('create_job')
        data = {'input_text': 'This is a test guideline document.'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('event_id', response.data)
        
        # Verify job was created in database
        job = Job.objects.get(event_id=response.data['event_id'])
        self.assertEqual(job.input_text, 'This is a test guideline document.')
        self.assertEqual(job.status, 'pending')

    def test_create_job_invalid_data(self):
        """Test job creation with invalid data"""
        url = reverse('create_job')
        data = {}  # Missing input_text
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_job_status(self):
        """Test job status retrieval"""
        # Create a job
        job = Job.objects.create(
            input_text="Test text",
            status='completed',
            summary="Test summary",
            checklist=["Item 1", "Item 2"]
        )
        
        url = reverse('get_job_status', kwargs={'event_id': job.event_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['event_id'], str(job.event_id))
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('result', response.data)
        self.assertEqual(response.data['result']['summary'], "Test summary")

    def test_get_job_status_not_found(self):
        """Test job status retrieval for non-existent job"""
        from uuid import uuid4
        fake_id = uuid4()
        url = reverse('get_job_status', kwargs={'event_id': fake_id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class JobTaskTest(TestCase):
    @patch('jobs.tasks.openai.OpenAI')
    def test_process_guideline_job_success(self, mock_openai):
        """Test successful job processing"""
        # Create a job
        job = Job.objects.create(input_text="Test guideline text")
        
        # Mock OpenAI responses
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock summary response
        mock_summary_response = MagicMock()
        mock_summary_response.choices[0].message.content = "This is a test summary"
        
        # Mock checklist response
        mock_checklist_response = MagicMock()
        mock_checklist_response.choices[0].message.content = '["Check item 1", "Check item 2"]'
        
        mock_client.chat.completions.create.side_effect = [
            mock_summary_response,
            mock_checklist_response
        ]
        
        # Run the task
        process_guideline_job(str(job.event_id))
        
        # Verify job was updated
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.summary, "This is a test summary")
        self.assertEqual(job.checklist, ["Check item 1", "Check item 2"])

    @patch('jobs.tasks.openai.OpenAI')
    def test_process_guideline_job_failure(self, mock_openai):
        """Test job processing with API failure"""
        # Create a job
        job = Job.objects.create(input_text="Test guideline text")
        
        # Mock OpenAI to raise an exception
        mock_openai.side_effect = Exception("API Error")
        
        # Run the task
        process_guideline_job(str(job.event_id))
        
        # Verify job was marked as failed
        job.refresh_from_db()
        self.assertEqual(job.status, 'failed')
        self.assertIsNotNone(job.error_message)

    def test_process_guideline_job_nonexistent(self):
        """Test processing non-existent job"""
        from uuid import uuid4
        fake_id = str(uuid4())
        
        # This should not raise an exception
        process_guideline_job(fake_id)