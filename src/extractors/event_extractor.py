import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import spacy

logger = logging.getLogger(__name__)

@dataclass
class TimelineEvent:
    """Represents a single timeline event extracted from a document."""
    date: str
    event_type: str
    description: str
    context: str
    confidence_score: float
    source_file: str
    entities: Dict[str, List[str]]

class LegalEventExtractor:
    """Extracts and classifies legal events from document context."""

    def __init__(self, config=None):
        self.config = config or {}
        try:
            self.nlp = spacy.load(self.config.get("nlp.model", "en_core_web_sm"))
        except OSError:
            logger.error(f"spaCy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None

        # Simplified patterns for event classification
        self.event_patterns = {
            "Lease Agreement": [r'\b(lease|leased|lessor|lessee|patta)\b'],
            "Court Filing": [r'\b(filed|suit|petition|appeal|case no)\b'],
            "Decree/Judgment": [r'\b(judgment|decree|order|ruling|court held)\b'],
            "Contract Execution": [r'\b(executed|signed|agreement|deed|contract)\b'],
            "Property Sale": [r'\b(sold|sale|purchase|bought|deed of sale)\b'],
            "Compromise/Settlement": [r'\b(compromise|settlement|settled|rafanama)\b'],
            "Registration": [r'\b(registered|registration|sub-registrar)\b'],
        }
        self.compiled_patterns = {
            event_type: [re.compile(p, re.IGNORECASE) for p in patterns]
            for event_type, patterns in self.event_patterns.items()
        }

    def extract_context_around_date(self, text: str, date_info: tuple, window: int) -> str:
        """Extracts a window of text around a date's position."""
        _, start_pos, end_pos = date_info
        context_start = max(0, start_pos - (window // 2))
        context_end = min(len(text), end_pos + (window // 2))
        return text[context_start:context_end]

    def classify_event_type(self, context: str) -> str:
        """Classifies the event type based on keywords in the context."""
        scores = {event_type: 0 for event_type in self.event_patterns}
        for event_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(context):
                    scores[event_type] += 1
        
        max_score = max(scores.values())
        if max_score > 0:
            # Return the event type with the highest score
            return max(scores, key=scores.get)
        
        return "General Legal Event"

    def extract_entities(self, context: str) -> Dict[str, List[str]]:
        """Extracts named entities (people, organizations, etc.) from the context."""
        if not self.nlp:
            return {}
        doc = self.nlp(context)
        entities = {"PERSON": [], "ORG": [], "GPE": [], "MONEY": []}
        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text.strip())
        
        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))
        return entities

    def calculate_confidence_score(self, event_type: str, context: str) -> float:
        """Calculates a confidence score based on context clues."""
        score = 0.5  # Base score
        if event_type != "General Legal Event":
            score += 0.2
        if len(context) > 200: # Longer context is more reliable
            score += 0.1
        
        # Add score for presence of legal jargon
        legal_jargon = ['plaintiff', 'defendant', 'decree', 'suit', 'hereinafter']
        if any(term in context.lower() for term in legal_jargon):
            score += 0.15

        return min(1.0, score)

    def generate_event_description(self, context: str) -> str:
        """Generates a simple, clean one-sentence description."""
        # Find the sentence containing the most relevant keywords
        sentences = re.split(r'(?<=[.!?])\s+', context.replace("\n", " "))
        # A simple heuristic: choose the middle sentence or the longest one.
        # A more advanced method would be needed for higher accuracy.
        if not sentences:
            return "No description available."
        
        # Clean up and return the most relevant sentence (e.g., the first one with substance)
        for sent in sentences:
            if len(sent) > 20:
                return sent.strip()
        return sentences[0].strip()