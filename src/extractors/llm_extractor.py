import os
import json
import logging
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from .event_extractor import TimelineEvent # We'll reuse the same data structure

logger = logging.getLogger(__name__)

class LlmEventExtractor:
    """Extracts timeline events using the Gemini LLM."""

    def __init__(self, config=None):
        self.config = config or {}
        load_dotenv() # Load environment variables from .env file
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file or environment variables.")
        
        genai.configure(api_key=api_key)
        
        # We use gemini-1.5-flash because it's fast and cost-effective for this task
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini LLM Extractor initialized.")

    def generate_prompt(self, text: str) -> str:
        """Creates a detailed, structured prompt for the LLM."""
        
        event_types = self.config.get('extraction.event_types', [])
        
        return f"""
        Analyze the following legal document text. Your task is to act as a meticulous legal analyst and extract a chronological timeline of all significant events.

        **Instructions:**
        1. Identify every event that has a specific date associated with it.
        2. For each event, you MUST provide the following three pieces of information:
           - `date`: The full, normalized date of the event (e.g., "March 11, 1921").
           - `event_type`: Classify the event using one of these exact types: {', '.join(event_types)}.
           - `description`: A concise, neutral, one-sentence summary of what happened.

        3. Return your findings as a single, valid JSON array of objects. Each object in the array represents one event.
        4. Do NOT include any explanations, comments, or text outside of the JSON array.

        **Example JSON Output Format:**
        [
          {{
            "date": "March 11, 1921",
            "event_type": "Lease Agreement",
            "description": "A lease deed was executed between Kumar Krishna Prasad Singh and The Bengal Coal Company Limited."
          }},
          {{
            "date": "January 15, 1929",
            "event_type": "Court Filing",
            "description": "Civil Suit No. 45/1929 was filed in the District Court of Hooghly regarding royalty payments."
          }}
        ]

        ---
        **Document Text to Analyze:**
        ---
        {text}
        """

    def extract_events(self, text: str, source_file: str) -> List[TimelineEvent]:
        """Sends text to the Gemini API and parses the structured response."""
        
        prompt = self.generate_prompt(text)
        
        try:
            response = self.model.generate_content(prompt)
            
            # Clean the response to ensure it's valid JSON
            json_text = response.text.strip().lstrip("```json").rstrip("```")
            extracted_data = json.loads(json_text)
            
            # Convert the raw JSON into our project's TimelineEvent objects
            timeline_events = []
            for item in extracted_data:
                timeline_events.append(
                    TimelineEvent(
                        date=item.get("date", "Unknown Date"),
                        event_type=item.get("event_type", "General Legal Event"),
                        description=item.get("description", "No description provided."),
                        source_file=source_file,
                        context=text,  # The full text can serve as context
                        confidence_score=0.95, # Assign a high confidence score for LLM extractions
                        entities={} # Entity extraction can be a separate LLM call or post-processing step
                    )
                )
            return timeline_events
            
        except Exception as e:
            logger.error(f"Error during Gemini API call or JSON parsing for {source_file}: {e}")
            return []