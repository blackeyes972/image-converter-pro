"""Settings tab for application configuration"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QPushButton,
    QSlider,
    QGridLayout,
    QTabWidget,
    QMessageBox,
    QFileDialog,
    QLineEdit,
)
from PyQt6.QtCore import pyqtSignal, Qt
from datetime import datetime
from loguru import logger

from ..core.config import AppConfig


class SettingsTab(QWidget):
    """Application settings tab"""

    settings_changed = pyqtSignal()

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config

        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """Create the settings UI"""
        layout = QVBoxLayout(self)

        # Create sub-tabs
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Conversion settings tab
        conversion_tab = self._create_conversion_settings()
        tab_widget.addTab(conversion_tab, "Conversion")

        # UI settings tab
        ui_tab = self._create_ui_settings()
        tab_widget.addTab(ui_tab, "Interface")

        # Advanced settings tab
        advanced_tab = self._create_advanced_settings()
        tab_widget.addTab(advanced_tab, "Advanced")

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_defaults)
        button_layout.addWidget(reset_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)

    def _create_conversion_settings(self) -> QWidget:
        """Create conversion settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Quality settings group
        quality_group = QGroupBox("Quality Settings")
        quality_layout = QGridLayout(quality_group)

        # JPEG quality
        quality_layout.addWidget(QLabel("JPEG Quality:"), 0, 0)
        self.jpeg_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.jpeg_quality_slider.setRange(1, 100)
        self.jpeg_quality_slider.valueChanged.connect(
            lambda v: self.jpeg_quality_label.setText(f"{v}%")
        )
        quality_layout.addWidget(self.jpeg_quality_slider, 0, 1)
        self.jpeg_quality_label = QLabel("85%")
        quality_layout.addWidget(self.jpeg_quality_label, 0, 2)

        # WebP quality
        quality_layout.addWidget(QLabel("WebP Quality:"), 1, 0)
        self.webp_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.webp_quality_slider.setRange(1, 100)
        self.webp_quality_slider.valueChanged.connect(
            lambda v: self.webp_quality_label.setText(f"{v}%")
        )
        quality_layout.addWidget(self.webp_quality_slider, 1, 1)
        self.webp_quality_label = QLabel("85%")
        quality_layout.addWidget(self.webp_quality_label, 1, 2)

        # PNG compression
        quality_layout.addWidget(QLabel("PNG Compression:"), 2, 0)
        self.png_compression_slider = QSlider(Qt.Orientation.Horizontal)
        self.png_compression_slider.setRange(0, 9)
        self.png_compression_slider.valueChanged.connect(
            lambda v: self.png_compression_label.setText(str(v))
        )
        quality_layout.addWidget(self.png_compression_slider, 2, 1)
        self.png_compression_label = QLabel("6")
        quality_layout.addWidget(self.png_compression_label, 2, 2)

        layout.addWidget(quality_group)

        # Default settings group
        defaults_group = QGroupBox("Default Settings")
        defaults_layout = QGridLayout(defaults_group)

        defaults_layout.addWidget(QLabel("Default Output Format:"), 0, 0)
        self.default_format_combo = QComboBox()
        self.default_format_combo.addItems(["png", "jpg", "webp", "ico"])
        defaults_layout.addWidget(self.default_format_combo, 0, 1)

        defaults_layout.addWidget(QLabel("Max Image Size:"), 1, 0)
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(256, 16384)
        self.max_size_spin.setSuffix(" px")
        defaults_layout.addWidget(self.max_size_spin, 1, 1)

        self.maintain_aspect_check = QCheckBox("Maintain Aspect Ratio by Default")
        defaults_layout.addWidget(self.maintain_aspect_check, 2, 0, 1, 2)

        layout.addWidget(defaults_group)
        layout.addStretch()

        return widget

    def _create_ui_settings(self) -> QWidget:
        """Create UI settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QGridLayout(appearance_group)

        appearance_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        appearance_layout.addWidget(self.theme_combo, 0, 1)

        appearance_layout.addWidget(QLabel("Language:"), 1, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Italiano", "Español", "Français"])
        appearance_layout.addWidget(self.language_combo, 1, 1)

        self.show_preview_check = QCheckBox("Show Image Preview")
        appearance_layout.addWidget(self.show_preview_check, 2, 0, 1, 2)

        layout.addWidget(appearance_group)

        # Behavior group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)

        self.auto_save_check = QCheckBox("Auto-save Settings")
        behavior_layout.addWidget(self.auto_save_check)

        self.check_updates_check = QCheckBox("Check for Updates")
        behavior_layout.addWidget(self.check_updates_check)

        layout.addWidget(behavior_group)
        layout.addStretch()

        return widget

    def _create_advanced_settings(self) -> QWidget:
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Logging group
        logging_group = QGroupBox("Logging")
        logging_layout = QGridLayout(logging_group)

        logging_layout.addWidget(QLabel("Log Level:"), 0, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        logging_layout.addWidget(self.log_level_combo, 0, 1)

        layout.addWidget(logging_group)

        # Error tracking group
        tracking_group = QGroupBox("Error Tracking")
        tracking_layout = QVBoxLayout(tracking_group)

        self.enable_sentry_check = QCheckBox("Enable Error Tracking (Sentry)")
        tracking_layout.addWidget(self.enable_sentry_check)

        sentry_layout = QHBoxLayout()
        sentry_layout.addWidget(QLabel("Sentry DSN:"))
        self.sentry_dsn_edit = QLineEdit()
        self.sentry_dsn_edit.setPlaceholderText("https://your-dsn@sentry.io/project-id")
        sentry_layout.addWidget(self.sentry_dsn_edit)
        tracking_layout.addLayout(sentry_layout)

        layout.addWidget(tracking_group)

        # Database group
        db_group = QGroupBox("Database")
        db_layout = QHBoxLayout(db_group)

        vacuum_btn = QPushButton("Optimize Database")
        vacuum_btn.clicked.connect(self._optimize_database)
        db_layout.addWidget(vacuum_btn)

        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self._backup_database)
        db_layout.addWidget(backup_btn)

        db_layout.addStretch()

        layout.addWidget(db_group)
        layout.addStretch()

        return widget

    def _load_settings(self):
        """Load current settings into UI"""
        settings = self.config.settings

        # Conversion settings
        self.jpeg_quality_slider.setValue(settings.conversion.jpeg_quality)
        self.webp_quality_slider.setValue(settings.conversion.webp_quality)
        self.png_compression_slider.setValue(settings.conversion.png_compression)
        self.max_size_spin.setValue(settings.conversion.max_image_size)
        self.maintain_aspect_check.setChecked(settings.conversion.maintain_aspect_ratio)

        # Set default format
        format_index = self.default_format_combo.findText(settings.conversion.default_output_format)
        if format_index >= 0:
            self.default_format_combo.setCurrentIndex(format_index)

        # UI settings
        theme_index = self.theme_combo.findText(settings.ui.theme.title())
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)

        self.show_preview_check.setChecked(settings.ui.show_preview)
        self.auto_save_check.setChecked(settings.ui.auto_save_settings)

        # Advanced settings
        log_index = self.log_level_combo.findText(settings.logging_level)
        if log_index >= 0:
            self.log_level_combo.setCurrentIndex(log_index)

        self.enable_sentry_check.setChecked(settings.enable_sentry)
        self.check_updates_check.setChecked(settings.check_updates)

    def _apply_settings(self):
        """Apply current settings"""
        try:
            # Update configuration
            self.config.update_settings(
                **{
                    "conversion.jpeg_quality": self.jpeg_quality_slider.value(),
                    "conversion.webp_quality": self.webp_quality_slider.value(),
                    "conversion.png_compression": self.png_compression_slider.value(),
                    "conversion.default_output_format": self.default_format_combo.currentText(),
                    "conversion.max_image_size": self.max_size_spin.value(),
                    "conversion.maintain_aspect_ratio": self.maintain_aspect_check.isChecked(),
                    "ui.theme": self.theme_combo.currentText().lower(),
                    "ui.show_preview": self.show_preview_check.isChecked(),
                    "ui.auto_save_settings": self.auto_save_check.isChecked(),
                    "logging_level": self.log_level_combo.currentText(),
                    "enable_sentry": self.enable_sentry_check.isChecked(),
                    "check_updates": self.check_updates_check.isChecked(),
                }
            )

            self.settings_changed.emit()

            QMessageBox.information(self, "Settings", "Settings applied successfully!")
            logger.info("Settings applied by user")

        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {e}")

    def _reset_defaults(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Reset to default configuration
            from ..core.config import AppSettings

            default_settings = AppSettings()

            self.config._settings = default_settings
            self.config.save()

            self._load_settings()
            self.settings_changed.emit()

            QMessageBox.information(self, "Settings", "Settings reset to defaults!")
            logger.info("Settings reset to defaults")

    def _optimize_database(self):
        """Optimize database"""
        try:
            # Need database manager reference from parent
            parent_window = self.parent()
            while parent_window and not hasattr(parent_window, "db_manager"):
                parent_window = parent_window.parent()

            if parent_window and hasattr(parent_window, "db_manager"):
                with parent_window.db_manager.get_connection() as conn:
                    conn.execute("VACUUM")
                    conn.commit()

                QMessageBox.information(self, "Database", "Database optimized successfully!")
                logger.info("Database optimized")
            else:
                QMessageBox.warning(self, "Error", "Cannot access database manager")

        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            QMessageBox.critical(self, "Error", f"Failed to optimize database: {e}")

    def _backup_database(self):
        """Backup database"""
        backup_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Database Backup",
            f"image_converter_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "Database Files (*.db)",
        )

        if backup_path:
            try:
                import shutil

                # Get database path from parent
                parent_window = self.parent()
                while parent_window and not hasattr(parent_window, "db_manager"):
                    parent_window = parent_window.parent()

                if parent_window and hasattr(parent_window, "db_manager"):
                    shutil.copy2(parent_window.db_manager.db_path, backup_path)

                    QMessageBox.information(
                        self, "Backup", f"Database backed up to:\n{backup_path}"
                    )
                    logger.info(f"Database backed up to {backup_path}")
                else:
                    QMessageBox.warning(self, "Error", "Cannot access database manager")

            except Exception as e:
                logger.error(f"Error backing up database: {e}")
                QMessageBox.critical(self, "Error", f"Failed to backup database: {e}")
