import json
import logging
from pathlib import Path
from typing import List
from datetime import datetime
import pandas as pd
from ..extractors.event_extractor import TimelineEvent

logger = logging.getLogger(__name__)

class OutputGenerator:
    """Generates output files in various formats (Markdown, JSON, Excel)."""

    def __init__(self, config):
        self.config = config

    def save_as_markdown(self, events: List[TimelineEvent], path: Path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write("# Legal Document Timeline\n\n")
            f.write("| Date | Event Type | Description | Source File |\n")
            f.write("|------|------------|-------------|-------------|\n")
            for event in events:
                desc = event.description.replace('\n', ' ').replace('|', '\|')[:100]
                f.write(f"| {event.date} | {event.event_type} | {desc}... | {event.source_file} |\n")
        logger.info(f"Markdown report saved to {path}")

    def save_as_json(self, events: List[TimelineEvent], path: Path):
        events_dict = [event.__dict__ for event in events]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(events_dict, f, indent=2)
        logger.info(f"JSON output saved to {path}")

    def save_as_excel(self, events: List[TimelineEvent], path: Path):
        df = pd.DataFrame([event.__dict__ for event in events])
        df.to_excel(path, index=False, engine='openpyxl')
        logger.info(f"Excel report saved to {path}")

    def save_summary(self, **kwargs):
        path = kwargs['output_path']
        with open(path, 'w', encoding='utf-8') as f:
            f.write("# Processing Summary\n\n")
            f.write(f"* **Files Processed:** {kwargs['files_processed']}\n")
            f.write(f"* **Events Extracted:** {kwargs['events_extracted']}\n")
            f.write(f"* **Total Time:** {kwargs['processing_time']:.2f} seconds\n")
        logger.info(f"Summary saved to {path}")