# src/extensions/gif_worker.py
"""
Background worker for GIF operations
"""

from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from typing import List
from loguru import logger

from .gif_processor import GifProcessor, GifCreationParams, GifOptimizationParams
from ..core.database import DatabaseManager


class GifCreationWorker(QThread):
    """Worker thread for GIF creation"""
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage
    frame_processed = pyqtSignal(int, int)  # current, total
    creation_completed = pyqtSignal(str)  # output_path
    creation_failed = pyqtSignal(str)  # error_message
    
    def __init__(
        self,
        image_paths: List[Path],
        output_path: Path,
        params: GifCreationParams,
        db_manager: DatabaseManager
    ):
        super().__init__()
        self.image_paths = image_paths
        self.output_path = output_path
        self.params = params
        self.db_manager = db_manager
        self.processor = GifProcessor()
        self._cancelled = False
    
    def cancel(self):
        """Cancel the GIF creation process"""
        self._cancelled = True
        logger.info("GIF creation cancelled by user")
    
    def run(self):
        """Run the GIF creation process"""
        if self._cancelled:
            return
        
        try:
            logger.info(f"Starting GIF creation with {len(self.image_paths)} images")
            
            # Create GIF
            record = self.processor.create_gif_from_images(
                self.image_paths,
                self.output_path,
                self.params,
                progress_callback=self.progress_updated.emit
            )
            
            # Save to database
            self.db_manager.add_conversion_record(record)
            
            self.creation_completed.emit(str(self.output_path))
            logger.info("GIF creation completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"GIF creation failed: {error_msg}")
            self.creation_failed.emit(error_msg)


class GifOptimizationWorker(QThread):
    """Worker thread for GIF optimization"""
    
    # Signals
    progress_updated = pyqtSignal(int)
    optimization_completed = pyqtSignal(str, int)  # output_path, size_reduction_percent
    optimization_failed = pyqtSignal(str)
    
    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        params: GifOptimizationParams,
        db_manager: DatabaseManager
    ):
        super().__init__()
        self.source_path = source_path
        self.target_path = target_path
        self.params = params
        self.db_manager = db_manager
        self.processor = GifProcessor()
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        if self._cancelled:
            return
        
        try:
            original_size = self.source_path.stat().st_size
            
            record = self.processor.optimize_gif(
                self.source_path,
                self.target_path,
                self.params,
                progress_callback=self.progress_updated.emit
            )
            
            self.db_manager.add_conversion_record(record)
            
            # Calculate size reduction
            new_size = self.target_path.stat().st_size
            reduction_percent = int((1 - new_size / original_size) * 100)
            
            self.optimization_completed.emit(str(self.target_path), reduction_percent)
            
        except Exception as e:
            self.optimization_failed.emit(str(e))


