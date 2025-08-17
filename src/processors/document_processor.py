import logging
from typing import List
from pathlib import Path
# Import everything
from ..utils.file_handler import FileHandler
from ..extractors.event_extractor import LegalEventExtractor, TimelineEvent
from ..extractors.date_extractor import LegalDateExtractor
from ..extractors.llm_extractor import LlmEventExtractor

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes documents with a hybrid approach: local first, LLM as fallback."""

    def __init__(self, config):
        self.config = config
        # Initialize BOTH extractor types
        self.local_event_extractor = LegalEventExtractor(config)
        self.local_date_extractor = LegalDateExtractor(config)
        self.llm_extractor = LlmEventExtractor(config)
        self.file_handler = FileHandler(config) # <-- ADD THIS LINE

        # Get settings from config.yaml
        self.context_window = self.config.get('processing.context_window', 500)
        # We need a threshold to decide when to use the LLM
        self.confidence_threshold = self.config.get('processing.llm_fallback_threshold', 0.8)

    async def process_document(self, file_path: str) -> List[TimelineEvent]:
        # ... (the rest of the file remains the same) ...
        logger.info(f"Processing with Hybrid-Safety-Net: {file_path}")
        content = self.file_handler.read_file_content(file_path)
        if not content or not content.strip():
            return []

        # --- STEP 1: First pass with the fast, local extractor ---
        dates = self.local_date_extractor.extract_dates_from_text(content)
        high_confidence_events = []
        needs_llm_review = False

        if not dates:
            needs_llm_review = True
        else:
            for date_info in dates:
                context = self.local_event_extractor.extract_context_around_date(
                    content, date_info, self.context_window
                )
                event_type = self.local_event_extractor.classify_event_type(context)
                confidence = self.local_event_extractor.calculate_confidence_score(event_type, context)

                if confidence >= self.confidence_threshold:
                    # If confidence is high, accept the locally extracted event
                    high_confidence_events.append(TimelineEvent(
                        date=date_info[0],
                        event_type=event_type,
                        description=self.local_event_extractor.generate_event_description(context),
                        context=context,
                        confidence_score=confidence,
                        source_file=Path(file_path).name,
                        entities=self.local_event_extractor.extract_entities(context)
                    ))
                else:
                    # If ANY event has low confidence, the whole document needs a deeper look
                    needs_llm_review = True
                    break # No need to check other dates

        # --- STEP 2: If needed, run the second pass with the LLM ---
        if needs_llm_review:
            logger.info(f"Low confidence or no events found. Sending to LLM for review: {file_path}")
            # The LLM re-processes the ENTIRE document for best context
            llm_events = self.llm_extractor.extract_events(content, Path(file_path).name)
            return llm_events # Return the superior LLM results

        logger.info(f"Extracted {len(high_confidence_events)} events locally from {Path(file_path).name}")
        return high_confidence_events