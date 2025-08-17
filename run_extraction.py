import sys
import asyncio
import argparse
from pathlib import Path
from src.main import LegalTimelineExtractor

def main():
    parser = argparse.ArgumentParser(description='Extract chronological timelines from legal documents.')
    parser.add_argument('input_dir', help='Directory containing documents to process.')
    parser.add_argument('--output', '-o', default='./data/output', help='Directory to save results.')
    parser.add_argument('--config', '-c', default='config.yaml', help='Path to configuration file.')
    parser.add_argument('--workers', '-w', type=int, help='Override number of worker processes.')
    parser.add_argument('--format', '-f', choices=['markdown', 'json', 'excel', 'all'], default='all', help='Output format.')
    
    args = parser.parse_args()
    if not Path(args.input_dir).exists():
        print(f"Error: Input directory not found: {args.input_dir}", file=sys.stderr)
        sys.exit(1)
        
    try:
        extractor = LegalTimelineExtractor(config_path=args.config)
        print(f"🔍 Starting extraction from '{args.input_dir}'...")
        results = asyncio.run(extractor.process_directory(
            input_dir=args.input_dir,
            output_dir=args.output,
            output_format=args.format,
            max_workers=args.workers
        ))
        print("\n✅ Extraction Complete!")
        print(f"📊 Files Processed: {results['files_processed']}")
        print(f"📅 Events Found: {results['events_extracted']}")
        print(f"⏱️  Total Time: {results['processing_time']:.2f}s")
        print(f"📂 Results saved in '{args.output}'")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()