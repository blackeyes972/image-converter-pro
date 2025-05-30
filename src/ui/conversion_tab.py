"""Conversion tab UI"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QComboBox,
    QLabel,
    QSpinBox,
    QCheckBox,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QGridLayout,
)
from PyQt6.QtCore import pyqtSignal, Qt
from pathlib import Path
from typing import List
from loguru import logger

from ..core.config import AppConfig
from ..core.database import DatabaseManager
from ..core.image_processor import ConversionParams
from ..core.worker import ConversionWorker


class ConversionTab(QWidget):
    """Image conversion tab"""

    status_message = pyqtSignal(str)

    def __init__(self, config: AppConfig, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.db_manager = db_manager
        self.conversion_worker = None

        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """Create the conversion UI"""
        layout = QVBoxLayout(self)

        # Conversion settings group
        settings_group = QGroupBox("Conversion Settings")
        settings_layout = QGridLayout(settings_group)

        # Target format
        settings_layout.addWidget(QLabel("Target Format:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "WEBP", "ICO"])
        settings_layout.addWidget(self.format_combo, 0, 1)

        # Quality
        settings_layout.addWidget(QLabel("Quality:"), 0, 2)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(85)
        settings_layout.addWidget(self.quality_spin, 0, 3)

        # Resize options
        settings_layout.addWidget(QLabel("Resize Width:"), 1, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(0, 8192)
        self.width_spin.setSpecialValueText("Original")
        settings_layout.addWidget(self.width_spin, 1, 1)

        settings_layout.addWidget(QLabel("Resize Height:"), 1, 2)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(0, 8192)
        self.height_spin.setSpecialValueText("Original")
        settings_layout.addWidget(self.height_spin, 1, 3)

        # Maintain aspect ratio
        self.aspect_checkbox = QCheckBox("Maintain Aspect Ratio")
        self.aspect_checkbox.setChecked(True)
        settings_layout.addWidget(self.aspect_checkbox, 2, 0, 1, 2)

        layout.addWidget(settings_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.single_btn = QPushButton("Convert Single File")
        self.single_btn.clicked.connect(self._convert_single)
        button_layout.addWidget(self.single_btn)

        self.batch_btn = QPushButton("Batch Convert")
        self.batch_btn.clicked.connect(self._convert_batch)
        button_layout.addWidget(self.batch_btn)

        layout.addLayout(button_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Log output
        log_group = QGroupBox("Conversion Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def _load_settings(self):
        """Load settings from configuration"""
        conv_settings = self.config.settings.conversion

        # Set format
        format_index = self.format_combo.findText(conv_settings.default_output_format.upper())
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)

        # Set quality
        self.quality_spin.setValue(conv_settings.jpeg_quality)

        # Set aspect ratio
        self.aspect_checkbox.setChecked(conv_settings.maintain_aspect_ratio)

    def _get_conversion_params(self) -> ConversionParams:
        """Get current conversion parameters"""
        return ConversionParams(
            target_format=self.format_combo.currentText().lower(),
            quality=self.quality_spin.value(),
            resize_width=self.width_spin.value() if self.width_spin.value() > 0 else None,
            resize_height=self.height_spin.value() if self.height_spin.value() > 0 else None,
            maintain_aspect=self.aspect_checkbox.isChecked(),
        )

    def _convert_single(self):
        """Convert single file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image File",
            "",
            "Image Files (*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.gif)",
        )

        if not file_path:
            return

        output_dir, _ = QFileDialog.getSaveFileName(
            self,
            "Save Converted Image",
            f"{Path(file_path).stem}.{self.format_combo.currentText().lower()}",
            f"{self.format_combo.currentText()} Files (*.{self.format_combo.currentText().lower()})",
        )

        if not output_dir:
            return

        self._start_conversion([Path(file_path)], Path(output_dir).parent)

    def _convert_batch(self):
        """Convert multiple files"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",
            "Image Files (*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.gif)",
        )

        if not files:
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")

        if not output_dir:
            return

        self._start_conversion([Path(f) for f in files], Path(output_dir))

    def _start_conversion(self, files: List[Path], output_dir: Path):
        """Start conversion process"""
        if self.conversion_worker and self.conversion_worker.isRunning():
            QMessageBox.warning(self, "Warning", "Conversion already in progress!")
            return

        params = self._get_conversion_params()

        self.conversion_worker = ConversionWorker(files, output_dir, params, self.db_manager)
        self.conversion_worker.progress_updated.connect(self._update_progress)
        self.conversion_worker.file_completed.connect(self._file_completed)
        self.conversion_worker.file_failed.connect(self._file_failed)
        self.conversion_worker.all_completed.connect(self._conversion_finished)

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(files))
        self.progress_bar.setValue(0)

        self.single_btn.setEnabled(False)
        self.batch_btn.setEnabled(False)

        self.log_text.clear()
        self.log_text.append(f"Starting conversion of {len(files)} files...")

        self.status_message.emit("Converting images...")
        self.conversion_worker.start()

    def _update_progress(self, current: int, total: int):
        """Update progress bar"""
        self.progress_bar.setValue(current)
        self.status_message.emit(f"Converting {current}/{total} files...")

    def _file_completed(self, filename: str):
        """Handle completed file"""
        self.log_text.append(f"✓ Converted: {Path(filename).name}")

    def _file_failed(self, filename: str, error: str):
        """Handle failed file"""
        self.log_text.append(f"✗ Failed: {Path(filename).name} - {error}")

    def _conversion_finished(self, completed: int):
        """Handle conversion completion"""
        self.progress_bar.setVisible(False)
        self.single_btn.setEnabled(True)
        self.batch_btn.setEnabled(True)

        self.status_message.emit(f"Conversion completed: {completed} files")
        self.log_text.append(f"\nConversion completed: {completed} files processed")

        # Show completion message
        QMessageBox.information(
            self, "Conversion Complete", f"Successfully converted {completed} files!"
        )
