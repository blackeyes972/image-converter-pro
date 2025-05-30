# src/extensions/gif_tab.py
"""
GIF Tab for the main application
Extends UI without modifying existing tabs
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QSpinBox, QCheckBox, QComboBox, QProgressBar,
    QTextEdit, QFileDialog, QMessageBox, QGridLayout,
    QTabWidget, QListWidget, QListWidgetItem, QSlider
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QIcon
from pathlib import Path
from typing import List
from loguru import logger

from .gif_processor import GifCreationParams, GifOptimizationParams
from .gif_worker import GifCreationWorker, GifOptimizationWorker
from ..core.database import DatabaseManager


class GifTab(QWidget):
    """Tab for GIF operations"""
    
    status_message = pyqtSignal(str)
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.creation_worker = None
        self.optimization_worker = None
        self.selected_images = []
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the GIF tab UI"""
        layout = QVBoxLayout(self)
        
        # Create sub-tabs for different GIF operations
        gif_tabs = QTabWidget()
        layout.addWidget(gif_tabs)
        
        # Tab 1: Create GIF from images
        creation_tab = self._create_gif_creation_tab()
        gif_tabs.addTab(creation_tab, "Create GIF")
        
        # Tab 2: Optimize existing GIF
        optimization_tab = self._create_gif_optimization_tab()
        gif_tabs.addTab(optimization_tab, "Optimize GIF")
        
        # Tab 3: Extract frames from GIF
        extraction_tab = self._create_frame_extraction_tab()
        gif_tabs.addTab(extraction_tab, "Extract Frames")
    
    def _create_gif_creation_tab(self) -> QWidget:
        """Create GIF creation interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Image selection group
        selection_group = QGroupBox("Image Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        # Buttons for image selection
        button_layout = QHBoxLayout()
        
        self.add_images_btn = QPushButton("Add Images")
        self.add_images_btn.clicked.connect(self._add_images)
        button_layout.addWidget(self.add_images_btn)
        
        self.clear_images_btn = QPushButton("Clear All")
        self.clear_images_btn.clicked.connect(self._clear_images)
        button_layout.addWidget(self.clear_images_btn)
        
        button_layout.addStretch()
        selection_layout.addLayout(button_layout)
        
        # Image list
        self.image_list = QListWidget()
        self.image_list.setMaximumHeight(150)
        selection_layout.addWidget(self.image_list)
        
        layout.addWidget(selection_group)
        
        # GIF settings group
        settings_group = QGroupBox("GIF Settings")
        settings_layout = QGridLayout(settings_group)
        
        # Frame duration
        settings_layout.addWidget(QLabel("Frame Duration:"), 0, 0)
        self.frame_duration_spin = QSpinBox()
        self.frame_duration_spin.setRange(100, 5000)
        self.frame_duration_spin.setValue(500)
        self.frame_duration_spin.setSuffix(" ms")
        settings_layout.addWidget(self.frame_duration_spin, 0, 1)
        
        # Loop count
        settings_layout.addWidget(QLabel("Loop Count:"), 0, 2)
        self.loop_count_spin = QSpinBox()
        self.loop_count_spin.setRange(0, 999)
        self.loop_count_spin.setValue(0)
        self.loop_count_spin.setSpecialValueText("Infinite")
        settings_layout.addWidget(self.loop_count_spin, 0, 3)
        
        # Quality
        settings_layout.addWidget(QLabel("Quality:"), 1, 0)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(85)
        self.quality_spin.setSuffix("%")
        settings_layout.addWidget(self.quality_spin, 1, 1)
        
        # Resize options
        settings_layout.addWidget(QLabel("Resize Width:"), 1, 2)
        self.gif_width_spin = QSpinBox()
        self.gif_width_spin.setRange(0, 4096)
        self.gif_width_spin.setSpecialValueText("Original")
        settings_layout.addWidget(self.gif_width_spin, 1, 3)
        
        settings_layout.addWidget(QLabel("Resize Height:"), 2, 0)
        self.gif_height_spin = QSpinBox()
        self.gif_height_spin.setRange(0, 4096)
        self.gif_height_spin.setSpecialValueText("Original")
        settings_layout.addWidget(self.gif_height_spin, 2, 1)
        
        # Options
        self.gif_maintain_aspect = QCheckBox("Maintain Aspect Ratio")
        self.gif_maintain_aspect.setChecked(True)
        settings_layout.addWidget(self.gif_maintain_aspect, 2, 2, 1, 2)
        
        self.gif_optimize = QCheckBox("Optimize File Size")
        self.gif_optimize.setChecked(True)
        settings_layout.addWidget(self.gif_optimize, 3, 0, 1, 2)
        
        layout.addWidget(settings_group)
        
        # Create button
        self.create_gif_btn = QPushButton("Create GIF")
        self.create_gif_btn.clicked.connect(self._create_gif)
        self.create_gif_btn.setEnabled(False)
        layout.addWidget(self.create_gif_btn)
        
        # Progress bar
        self.gif_progress_bar = QProgressBar()
        self.gif_progress_bar.setVisible(False)
        layout.addWidget(self.gif_progress_bar)
        
        return widget
    
    def _create_gif_optimization_tab(self) -> QWidget:
        """Create GIF optimization interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # File selection
        file_group = QGroupBox("GIF File")
        file_layout = QHBoxLayout(file_group)
        
        self.gif_file_label = QLabel("No file selected")
        file_layout.addWidget(self.gif_file_label)
        
        self.select_gif_btn = QPushButton("Select GIF")
        self.select_gif_btn.clicked.connect(self._select_gif_file)
        file_layout.addWidget(self.select_gif_btn)
        
        layout.addWidget(file_group)
        
        # Optimization settings
        opt_group = QGroupBox("Optimization Settings")
        opt_layout = QGridLayout(opt_group)
        
        # Color reduction
        self.reduce_colors_check = QCheckBox("Reduce Colors")
        self.reduce_colors_check.setChecked(True)
        opt_layout.addWidget(self.reduce_colors_check, 0, 0)
        
        opt_layout.addWidget(QLabel("Max Colors:"), 0, 1)
        self.max_colors_spin = QSpinBox()
        self.max_colors_spin.setRange(2, 256)
        self.max_colors_spin.setValue(256)
        opt_layout.addWidget(self.max_colors_spin, 0, 2)
        
        # Dithering
        self.dither_check = QCheckBox("Use Dithering")
        self.dither_check.setChecked(True)
        opt_layout.addWidget(self.dither_check, 1, 0)
        
        # Transparency
        self.transparency_check = QCheckBox("Preserve Transparency")
        self.transparency_check.setChecked(True)
        opt_layout.addWidget(self.transparency_check, 1, 1, 1, 2)
        
        layout.addWidget(opt_group)
        
        # Optimize button
        self.optimize_gif_btn = QPushButton("Optimize GIF")
        self.optimize_gif_btn.clicked.connect(self._optimize_gif)
        self.optimize_gif_btn.setEnabled(False)
        layout.addWidget(self.optimize_gif_btn)
        
        # Progress and results
        self.opt_progress_bar = QProgressBar()
        self.opt_progress_bar.setVisible(False)
        layout.addWidget(self.opt_progress_bar)
        
        layout.addStretch()
        return widget
    
    def _create_frame_extraction_tab(self) -> QWidget:
        """Create frame extraction interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # File selection
        extract_file_group = QGroupBox("Source GIF")
        extract_file_layout = QHBoxLayout(extract_file_group)
        
        self.extract_gif_label = QLabel("No file selected")
        extract_file_layout.addWidget(self.extract_gif_label)
        
        self.select_extract_gif_btn = QPushButton("Select GIF")
        self.select_extract_gif_btn.clicked.connect(self._select_gif_for_extraction)
        extract_file_layout.addWidget(self.select_extract_gif_btn)
        
        layout.addWidget(extract_file_group)
        
        # Extraction settings
        extract_settings_group = QGroupBox("Extraction Settings")
        extract_settings_layout = QGridLayout(extract_settings_group)
        
        extract_settings_layout.addWidget(QLabel("Frame Format:"), 0, 0)
        self.frame_format_combo = QComboBox()
        self.frame_format_combo.addItems(["PNG", "JPG", "WEBP"])
        extract_settings_layout.addWidget(self.frame_format_combo, 0, 1)
        
        layout.addWidget(extract_settings_group)
        
        # Extract button
        self.extract_frames_btn = QPushButton("Extract Frames")
        self.extract_frames_btn.clicked.connect(self._extract_frames)
        self.extract_frames_btn.setEnabled(False)
        layout.addWidget(self.extract_frames_btn)
        
        layout.addStretch()
        return widget
    
    def _add_images(self):
        """Add images for GIF creation"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images for GIF",
            "",
            "Image Files (*.jpg *.jpeg *.png *.webp *.bmp)"
        )
        
        if files:
            for file_path in files:
                if Path(file_path) not in self.selected_images:
                    self.selected_images.append(Path(file_path))
                    
                    # Add to list widget
                    item = QListWidgetItem(Path(file_path).name)
                    item.setData(Qt.ItemDataRole.UserRole, file_path)
                    self.image_list.addItem(item)
            
            self.create_gif_btn.setEnabled(len(self.selected_images) >= 2)
            self.status_message.emit(f"Selected {len(self.selected_images)} images for GIF")
    
    def _clear_images(self):
        """Clear selected images"""
        self.selected_images.clear()
        self.image_list.clear()
        self.create_gif_btn.setEnabled(False)
        self.status_message.emit("Cleared image selection")
    
    def _get_gif_creation_params(self) -> GifCreationParams:
        """Get GIF creation parameters from UI"""
        return GifCreationParams(
            frame_duration=self.frame_duration_spin.value(),
            loop_count=self.loop_count_spin.value(),
            optimize=self.gif_optimize.isChecked(),
            quality=self.quality_spin.value(),
            resize_width=self.gif_width_spin.value() if self.gif_width_spin.value() > 0 else None,
            resize_height=self.gif_height_spin.value() if self.gif_height_spin.value() > 0 else None,
            maintain_aspect=self.gif_maintain_aspect.isChecked()
        )
    
    def _create_gif(self):
        """Start GIF creation process"""
        if len(self.selected_images) < 2:
            QMessageBox.warning(self, "Warning", "Select at least 2 images to create a GIF!")
            return
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save GIF As",
            "animation.gif",
            "GIF Files (*.gif)"
        )
        
        if not output_path:
            return
        
        params = self._get_gif_creation_params()
        
        # Start creation worker
        self.creation_worker = GifCreationWorker(
            self.selected_images,
            Path(output_path),
            params,
            self.db_manager
        )
        
        # Connect signals
        self.creation_worker.progress_updated.connect(self.gif_progress_bar.setValue)
        self.creation_worker.creation_completed.connect(self._gif_creation_completed)
        self.creation_worker.creation_failed.connect(self._gif_creation_failed)
        
        # UI updates
        self.gif_progress_bar.setVisible(True)
        self.gif_progress_bar.setValue(0)
        self.create_gif_btn.setEnabled(False)
        
        self.status_message.emit("Creating GIF...")
        self.creation_worker.start()
    
    def _gif_creation_completed(self, output_path: str):
        """Handle completed GIF creation"""
        self.gif_progress_bar.setVisible(False)
        self.create_gif_btn.setEnabled(True)
        
        self.status_message.emit("GIF created successfully!")
        
        QMessageBox.information(
            self,
            "GIF Created",
            f"GIF created successfully!\n\nSaved to: {Path(output_path).name}"
        )
    
    def _gif_creation_failed(self, error_message: str):
        """Handle failed GIF creation"""
        self.gif_progress_bar.setVisible(False)
        self.create_gif_btn.setEnabled(True)
        
        self.status_message.emit("GIF creation failed")
        
        QMessageBox.critical(
            self,
            "GIF Creation Failed",
            f"Failed to create GIF:\n\n{error_message}"
        )
    
    def _select_gif_file(self):
        """Select GIF file for optimization"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select GIF File",
            "",
            "GIF Files (*.gif)"
        )
        
        if file_path:
            self.gif_file_path = Path(file_path)
            self.gif_file_label.setText(self.gif_file_path.name)
            self.optimize_gif_btn.setEnabled(True)
    
    def _optimize_gif(self):
        """Start GIF optimization"""
        if not hasattr(self, 'gif_file_path'):
            return
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Optimized GIF As",
            f"optimized_{self.gif_file_path.name}",
            "GIF Files (*.gif)"
        )
        
        if not output_path:
            return
        
        params = GifOptimizationParams(
            reduce_colors=self.reduce_colors_check.isChecked(),
            max_colors=self.max_colors_spin.value(),
            dither=self.dither_check.isChecked(),
            transparency=self.transparency_check.isChecked()
        )
        
        # Start optimization worker
        self.optimization_worker = GifOptimizationWorker(
            self.gif_file_path,
            Path(output_path),
            params,
            self.db_manager
        )
        
        self.optimization_worker.progress_updated.connect(self.opt_progress_bar.setValue)
        self.optimization_worker.optimization_completed.connect(self._optimization_completed)
        self.optimization_worker.optimization_failed.connect(self._optimization_failed)
        
        self.opt_progress_bar.setVisible(True)
        self.optimize_gif_btn.setEnabled(False)
        
        self.status_message.emit("Optimizing GIF...")
        self.optimization_worker.start()
    
    def _optimization_completed(self, output_path: str, reduction_percent: int):
        """Handle completed optimization"""
        self.opt_progress_bar.setVisible(False)
        self.optimize_gif_btn.setEnabled(True)
        
        self.status_message.emit(f"GIF optimized: {reduction_percent}% size reduction")
        
        QMessageBox.information(
            self,
            "Optimization Complete",
            f"GIF optimized successfully!\n\n"
            f"Size reduction: {reduction_percent}%\n"
            f"Saved to: {Path(output_path).name}"
        )
    
    def _optimization_failed(self, error_message: str):
        """Handle failed optimization"""
        self.opt_progress_bar.setVisible(False)
        self.optimize_gif_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Optimization Failed", f"Failed to optimize GIF:\n\n{error_message}")
    
    def _select_gif_for_extraction(self):
        """Select GIF file for frame extraction"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select GIF File",
            "",
            "GIF Files (*.gif)"
        )
        
        if file_path:
            self.extract_gif_path = Path(file_path)
            self.extract_gif_label.setText(self.extract_gif_path.name)
            self.extract_frames_btn.setEnabled(True)
    
    def _extract_frames(self):
        """Extract frames from GIF"""
        if not hasattr(self, 'extract_gif_path'):
            return
        
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory for Frames"
        )
        
        if not output_dir:
            return
        
        try:
            from .gif_processor import GifProcessor
            
            processor = GifProcessor()
            frame_format = self.frame_format_combo.currentText().lower()
            
            frames = processor.extract_gif_frames(
                self.extract_gif_path,
                Path(output_dir),
                frame_format
            )
            
            QMessageBox.information(
                self,
                "Extraction Complete",
                f"Extracted {len(frames)} frames to:\n{output_dir}"
            )
            
            self.status_message.emit(f"Extracted {len(frames)} frames from GIF")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Extraction Failed",
                f"Failed to extract frames:\n\n{str(e)}"
            )


