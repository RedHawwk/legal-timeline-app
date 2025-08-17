import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from .processors.batch_processor import BatchProcessor
from .outputs.output_generator import OutputGenerator
from .utils.config import Config
from .utils.file_handler import FileHandler

class LegalTimelineExtractor:
    """Main application class orchestrating the entire extraction process."""
    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config.load(config_path)
        logging.basicConfig(level=self.config.get('logging.level', 'INFO'),
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.batch_processor = BatchProcessor(self.config)
        self.output_generator = OutputGenerator(self.config)
        self.file_handler = FileHandler(self.config)

    async def process_directory(self, input_dir: str, output_dir: str, output_format: str, max_workers: Optional[int]) -> Dict:
        start_time = datetime.now()
        if max_workers:
            self.config.data['processing']['max_workers'] = max_workers
        
        file_paths = self.file_handler.get_files_to_process(input_dir)
        if not file_paths:
            raise ValueError(f"No processable files found in {input_dir}")

        all_events = await self.batch_processor.process_documents(file_paths)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        formats = self.config.get('output.formats', []) if output_format == 'all' else [output_format]
        if 'markdown' in formats:
            self.output_generator.save_as_markdown(all_events, output_path / 'timeline.md')
        if 'json' in formats:
            self.output_generator.save_as_json(all_events, output_path / 'timeline.json')
        if 'excel' in formats:
            self.output_generator.save_as_excel(all_events, output_path / 'timeline.xlsx')

        processing_time = (datetime.now() - start_time).total_seconds()
        summary_info = {
            'files_processed': len(file_paths),
            'events_extracted': len(all_events),
            'processing_time': processing_time,
            'output_path': output_path / 'summary.md'
        }
        self.output_generator.save_summary(**summary_info)
        return summary_info