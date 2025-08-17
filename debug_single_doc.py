import sys
import asyncio
from pathlib import Path
from src.utils.config import Config
from src.processors.document_processor import DocumentProcessor

async def debug_single(file_path: str):
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return
        
    print(f"--- Debugging: {file_path} ---")
    config = Config.load("config.yaml")
    processor = DocumentProcessor(config)
    events = await processor.process_document(file_path)
    
    if not events:
        print("No events were extracted.")
        return
        
    print(f"Found {len(events)} events:\n")
    for i, event in enumerate(events, 1):
        print(f"--- Event {i} ---")
        print(f"  Date:       {event.date}")
        print(f"  Type:       {event.event_type}")
        print(f"  Confidence: {event.confidence_score:.2f}")
        print(f"  Description: {event.description}")
        print(f"  Entities:   {event.entities}")
        print("-" * 20)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_single_doc.py <path_to_document>")
        sys.exit(1)
    asyncio.run(debug_single(sys.argv[1]))