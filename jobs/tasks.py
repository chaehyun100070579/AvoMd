from celery import shared_task
from django.conf import settings
from .models import Job
import openai
import json
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_guideline_job(job_id):
    """
    Process a guideline job through a two-step GPT chain:
    1. Summarize the input text
    2. Generate a checklist based on the summary
    """
    try:
        job = Job.objects.get(event_id=job_id)
        job.status = 'processing'
        job.save()
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Step 1: Summarize the guideline text
        summary_prompt = f"""
        Please provide a concise summary of the following guideline document. 
        Focus on the key points, main requirements, and important procedures.
        
        Text to summarize:
        {job.input_text}
        """
        
        summary_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        summary = summary_response.choices[0].message.content.strip()
        job.summary = summary
        job.save()
        
        # Step 2: Generate checklist based on summary
        checklist_prompt = f"""
        Based on the following summary of a guideline document, create a practical checklist 
        that someone could use to ensure compliance with the guidelines. 
        Return the checklist as a JSON array of strings, where each string is a checklist item.
        
        Summary:
        {summary}
        
        Please respond with only the JSON array, no additional text.
        """
        
        checklist_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": checklist_prompt}],
            max_tokens=800,
            temperature=0.3
        )
        
        checklist_text = checklist_response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            checklist = json.loads(checklist_text)
            if not isinstance(checklist, list):
                raise ValueError("Checklist must be a list")
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse checklist JSON: {e}")
            # Fallback: create a simple list from the response
            checklist = [item.strip('- ').strip() for item in checklist_text.split('\n') if item.strip()]
        
        job.checklist = checklist
        job.status = 'completed'
        job.save()
        
        logger.info(f"Successfully processed job {job_id}")
        
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        try:
            job = Job.objects.get(event_id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
        except Job.DoesNotExist:
            pass