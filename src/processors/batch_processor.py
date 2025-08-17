import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from typing import List
from tqdm import tqdm
from ..extractors.event_extractor import TimelineEvent
from .document_processor import DocumentProcessor
from datetime import datetime

logger = logging.getLogger(__name__)

def process_single_document_wrapper(config, file_path):
    """Wrapper function to be run in a separate process."""
    processor = DocumentProcessor(config)
    return asyncio.run(processor.process_document(file_path))

class BatchProcessor:
    """Processes multiple documents in parallel using a process pool."""

    def __init__(self, config):
        self.config = config
        self.max_workers = config.get('processing.max_workers', 4)

    async def process_documents(self, file_paths: List[str]) -> List[TimelineEvent]:
        all_events = []
        # Use ProcessPoolExecutor for CPU-bound NLP tasks to bypass GIL
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            loop = asyncio.get_running_loop()
            tasks = [
                loop.run_in_executor(executor, process_single_document_wrapper, self.config, fp)
                for fp in file_paths
            ]
            
            with tqdm(total=len(file_paths), desc="Processing Documents") as pbar:
                for future in asyncio.as_completed(tasks):
                    result = await future
                    all_events.extend(result)
                    pbar.update(1)

        if self.config.get('output.sort_chronologically', True):
            all_events.sort(key=lambda e: self._get_sortable_date(e.date))
        
        return all_events

    def _get_sortable_date(self, date_str: str):
        from dateutil.parser import parse
        try:
            return parse(date_str, fuzzy=True)
        except (ValueError, TypeError):
            # Fallback for non-standard or unparseable dates
            return datetime.min