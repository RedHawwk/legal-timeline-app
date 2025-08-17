import os
from pathlib import Path
from typing import List
import logging
import docx
import PyPDF2

logger = logging.getLogger(__name__)

class FileHandler:
    """Handle file operations like finding, filtering, and reading content."""

    def __init__(self, config):
        self.config = config
        self.supported_extensions = config.get('input.extensions', ['.txt'])
        self.max_file_size = config.get('input.max_file_size_mb', 50) * 1024 * 1024

    def get_files_to_process(self, directory: str) -> List[str]:
        """Get a list of all processable files from a directory, recursively."""
        file_paths = []
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.supported_extensions:
                    try:
                        if file_path.stat().st_size <= self.max_file_size:
                            file_paths.append(str(file_path))
                        else:
                            logger.warning(f"Skipping large file: {file_path}")
                    except OSError as e:
                        logger.error(f"Cannot access file {file_path}: {e}")
        return file_paths

    def read_file_content(self, file_path_str: str) -> str:
        """Read content from a file based on its extension."""
        file_path = Path(file_path_str)
        suffix = file_path.suffix.lower()
        try:
            if suffix == '.txt':
                return self._read_txt(file_path)
            elif suffix in ['.doc', '.docx']:
                return self._read_docx(file_path)
            elif suffix == '.pdf':
                return self._read_pdf(file_path)
            else:
                logger.warning(f"Unsupported file type: {suffix}")
                return ""
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return ""

    def _read_txt(self, file_path: Path) -> str:
        encoding = self.config.get('input.encoding', 'utf-8')
        return file_path.read_text(encoding=encoding, errors='ignore')

    def _read_docx(self, file_path: Path) -> str:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def _read_pdf(self, file_path: Path) -> str:
        text = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)