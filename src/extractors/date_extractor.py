import re
import logging
from typing import List, Tuple, Optional
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

class LegalDateExtractor:
    """Extracts and normalizes dates from text using regex and dateutil."""

    def __init__(self, config=None):
        self.config = config or {}
        # A set of robust regex patterns to find dates
        self.date_patterns = [
            r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\,\s+\d{4})\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?\,?\s+\d{4})\b',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
        ]
        if self.config.get('extraction.date_patterns.include_bengali_calendar', False):
            self.date_patterns.append(r'\b((?:Pous|Asadh)\s+\d{4}\s+B\.S\.)\b')

        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.date_patterns]

    def extract_dates_from_text(self, text: str) -> List[Tuple[str, int, int]]:
        """Finds all date-like strings in the text and returns them with their positions."""
        found_dates = []
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                date_str = match.group(0)
                normalized_date = self.normalize_date(date_str)
                if normalized_date:
                    found_dates.append((normalized_date, match.start(), match.end()))
        
        # Remove duplicates based on position
        unique_dates = list({d[1]: d for d in found_dates}.values())
        unique_dates.sort(key=lambda x: x[1]) # Sort by appearance
        return unique_dates

    def normalize_date(self, date_str: str) -> Optional[str]:
        """Converts a found date string into a standard 'Month Day, Year' format."""
        try:
            # Handle special cases like Bengali calendar
            if "B.S." in date_str:
                return f"Bengali Calendar Date ({date_str.strip()})"
                
            # Use the powerful dateutil parser
            dt = date_parser.parse(date_str, fuzzy=True)
            return dt.strftime('%B %d, %Y')
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse date '{date_str}': {e}")
            return None