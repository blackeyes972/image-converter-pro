"""Worker threads for background processing"""

from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from typing import List
from loguru import logger

from .image_processor import ImageProcessor, ConversionParams
from .database import DatabaseManager


class ConversionWorker(QThread):
    """Worker thread for image conversions"""

    # Signals
    progress_updated = pyqtSignal(int, int)  # current, total
    file_completed = pyqtSignal(str)  # filename
    file_failed = pyqtSignal(str, str)  # filename, error
    all_completed = pyqtSignal(int)  # total processed

    def __init__(
        self,
        files: List[Path],
        output_dir: Path,
        params: ConversionParams,
        db_manager: DatabaseManager,
    ):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.params = params
        self.db_manager = db_manager
        self.processor = ImageProcessor()
        self._cancelled = False

    def cancel(self):
        """Cancel the conversion process"""
        self._cancelled = True
        logger.info("Conversion process cancelled by user")

    def run(self):
        """Run the conversion process"""
        logger.info(f"Starting batch conversion of {len(self.files)} files")
        completed = 0

        for i, source_path in enumerate(self.files):
            if self._cancelled:
                break

            try:
                # Generate target path
                target_filename = f"{source_path.stem}.{self.params.target_format}"
                target_path = self.output_dir / target_filename

                # Convert image
                record = self.processor.convert_image(source_path, target_path, self.params)

                # Save to database
                self.db_manager.add_conversion_record(record)

                completed += 1
                self.file_completed.emit(str(source_path))
                self.progress_updated.emit(i + 1, len(self.files))

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to convert {source_path}: {error_msg}")
                self.file_failed.emit(str(source_path), error_msg)

        self.all_completed.emit(completed)
        logger.info(f"Batch conversion completed: {completed}/{len(self.files)} files")
