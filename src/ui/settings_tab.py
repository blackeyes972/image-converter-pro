"""Settings tab for application configuration with theming and translation support"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QSpinBox, QComboBox, QCheckBox, QPushButton,
                             QSlider, QGridLayout, QTabWidget, QMessageBox,
                             QFileDialog, QLineEdit)
from PyQt6.QtCore import pyqtSignal, Qt
from datetime import datetime
from loguru import logger

from ..core.config import AppConfig


class SettingsTab(QWidget):
    """Application settings tab with full theming and translation support"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.parent_window = parent
        
        # Get appearance manager from parent window
        self.appearance_manager = None
        if hasattr(parent, 'appearance_manager'):
            self.appearance_manager = parent.appearance_manager
        
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
        
        # UI settings tab (enhanced with theming)
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
        """Create UI settings tab with theming and translation support"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QGridLayout(appearance_group)
        
        # Theme selection
        appearance_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        
        # Populate themes from appearance manager
        if self.appearance_manager:
            available_themes = self.appearance_manager.get_available_themes()
            # Convert to display names
            theme_display_names = []
            self.theme_mapping = {}  # Store mapping from display name to actual name
            
            for theme in available_themes:
                if theme == 'light':
                    display_name = "Light"
                elif theme == 'dark':
                    display_name = "Dark"
                elif theme == 'auto':
                    display_name = "Auto (Follow System)"
                else:
                    display_name = theme.title()
                
                theme_display_names.append(display_name)
                self.theme_mapping[display_name] = theme
            
            self.theme_combo.addItems(theme_display_names)
        else:
            # Fallback if appearance manager not available
            self.theme_combo.addItems(["Light", "Dark", "Auto (Follow System)"])
            self.theme_mapping = {
                "Light": "light",
                "Dark": "dark", 
                "Auto (Follow System)": "auto"
            }
        
        appearance_layout.addWidget(self.theme_combo, 0, 1)
        
        # Language selection
        appearance_layout.addWidget(QLabel("Language:"), 1, 0)
        self.language_combo = QComboBox()
        
        # Populate languages from appearance manager
        if self.appearance_manager:
            available_languages = self.appearance_manager.get_available_languages()
            self.language_mapping = {}  # Store mapping from display name to code
            
            for code, name in available_languages.items():
                if code == 'auto':
                    display_name = f"{name} (Auto)"
                else:
                    display_name = name
                
                self.language_combo.addItem(display_name, code)
                self.language_mapping[display_name] = code
        else:
            # Fallback if appearance manager not available
            fallback_languages = {
                'en': 'English',
                'it': 'Italiano',
                'es': 'Español',
                'fr': 'Français'
            }
            self.language_mapping = {}
            for code, name in fallback_languages.items():
                self.language_combo.addItem(name, code)
                self.language_mapping[name] = code
        
        appearance_layout.addWidget(self.language_combo, 1, 1)
        
        # Theme preview
        self.theme_preview_check = QCheckBox("Show Theme Preview")
        self.theme_preview_check.setChecked(True)
        appearance_layout.addWidget(self.theme_preview_check, 2, 0, 1, 2)
        
        # UI options
        self.show_preview_check = QCheckBox("Show Image Preview")
        appearance_layout.addWidget(self.show_preview_check, 3, 0, 1, 2)
        
        layout.addWidget(appearance_group)
        
        # Window behavior group
        behavior_group = QGroupBox("Window Behavior")
        behavior_layout = QGridLayout(behavior_group)
        
        # Window size settings
        behavior_layout.addWidget(QLabel("Default Window Width:"), 0, 0)
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(600, 2560)
        self.window_width_spin.setSuffix(" px")
        behavior_layout.addWidget(self.window_width_spin, 0, 1)
        
        behavior_layout.addWidget(QLabel("Default Window Height:"), 1, 0)
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(400, 1440)
        self.window_height_spin.setSuffix(" px")
        behavior_layout.addWidget(self.window_height_spin, 1, 1)
        
        # Behavior options
        self.auto_save_check = QCheckBox("Auto-save Settings")
        behavior_layout.addWidget(self.auto_save_check, 2, 0, 1, 2)
        
        self.remember_window_check = QCheckBox("Remember Window Position")
        behavior_layout.addWidget(self.remember_window_check, 3, 0, 1, 2)
        
        layout.addWidget(behavior_group)
        
        # Notifications group
        notifications_group = QGroupBox("Notifications")
        notifications_layout = QVBoxLayout(notifications_group)
        
        self.show_completion_check = QCheckBox("Show Completion Notifications")
        notifications_layout.addWidget(self.show_completion_check)
        
        self.show_error_check = QCheckBox("Show Error Notifications")
        notifications_layout.addWidget(self.show_error_check)
        
        self.check_updates_check = QCheckBox("Check for Updates")
        notifications_layout.addWidget(self.check_updates_check)
        
        layout.addWidget(notifications_group)
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
        
        self.enable_file_logging = QCheckBox("Enable File Logging")
        logging_layout.addWidget(self.enable_file_logging, 1, 0, 1, 2)
        
        self.log_rotation_check = QCheckBox("Enable Log Rotation")
        logging_layout.addWidget(self.log_rotation_check, 2, 0, 1, 2)
        
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
        
        self.anonymous_analytics_check = QCheckBox("Anonymous Usage Analytics")
        tracking_layout.addWidget(self.anonymous_analytics_check)
        
        layout.addWidget(tracking_group)
        
        # Performance group
        performance_group = QGroupBox("Performance")
        performance_layout = QGridLayout(performance_group)
        
        performance_layout.addWidget(QLabel("Worker Threads:"), 0, 0)
        self.worker_threads_spin = QSpinBox()
        self.worker_threads_spin.setRange(1, 16)
        self.worker_threads_spin.setValue(4)
        performance_layout.addWidget(self.worker_threads_spin, 0, 1)
        
        performance_layout.addWidget(QLabel("Memory Limit:"), 1, 0)
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(256, 8192)
        self.memory_limit_spin.setSuffix(" MB")
        self.memory_limit_spin.setValue(1024)
        performance_layout.addWidget(self.memory_limit_spin, 1, 1)
        
        self.enable_gpu_check = QCheckBox("Enable GPU Acceleration (if available)")
        performance_layout.addWidget(self.enable_gpu_check, 2, 0, 1, 2)
        
        layout.addWidget(performance_group)
        
        # Database group
        db_group = QGroupBox("Database")
        db_layout = QHBoxLayout(db_group)
        
        vacuum_btn = QPushButton("Optimize Database")
        vacuum_btn.clicked.connect(self._optimize_database)
        db_layout.addWidget(vacuum_btn)
        
        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self._backup_database)
        db_layout.addWidget(backup_btn)
        
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self._clear_history)
        db_layout.addWidget(clear_history_btn)
        
        db_layout.addStretch()
        
        layout.addWidget(db_group)
        
        # Reset section
        reset_group = QGroupBox("Reset Options")
        reset_layout = QHBoxLayout(reset_group)
        
        reset_ui_btn = QPushButton("Reset UI Settings")
        reset_ui_btn.clicked.connect(self._reset_ui_settings)
        reset_layout.addWidget(reset_ui_btn)
        
        reset_conversion_btn = QPushButton("Reset Conversion Settings")
        reset_conversion_btn.clicked.connect(self._reset_conversion_settings)
        reset_layout.addWidget(reset_conversion_btn)
        
        reset_layout.addStretch()
        
        layout.addWidget(reset_group)
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
        
        # UI settings - Theme
        if self.appearance_manager:
            current_theme = self.appearance_manager.get_current_theme()
            # Find display name for current theme
            for display_name, theme_name in self.theme_mapping.items():
                if theme_name == current_theme:
                    theme_index = self.theme_combo.findText(display_name)
                    if theme_index >= 0:
                        self.theme_combo.setCurrentIndex(theme_index)
                    break
        
        # UI settings - Language
        if self.appearance_manager:
            current_language = self.appearance_manager.get_current_language()
            # Find the right item in combo box
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == current_language:
                    self.language_combo.setCurrentIndex(i)
                    break
        
        # Window settings
        self.window_width_spin.setValue(settings.ui.window_width)
        self.window_height_spin.setValue(settings.ui.window_height)
        self.show_preview_check.setChecked(settings.ui.show_preview)
        self.auto_save_check.setChecked(settings.ui.auto_save_settings)
        
        # Notification settings (with defaults)
        self.show_completion_check.setChecked(True)  # Default enabled
        self.show_error_check.setChecked(True)       # Default enabled
        self.check_updates_check.setChecked(settings.check_updates)
        
        # Advanced settings
        log_index = self.log_level_combo.findText(settings.logging_level)
        if log_index >= 0:
            self.log_level_combo.setCurrentIndex(log_index)
        
        self.enable_sentry_check.setChecked(settings.enable_sentry)
        
        # Performance settings (defaults)
        self.enable_file_logging.setChecked(True)
        self.log_rotation_check.setChecked(True)
        self.anonymous_analytics_check.setChecked(False)  # Default disabled
        self.enable_gpu_check.setChecked(False)           # Default disabled
        self.remember_window_check.setChecked(True)       # Default enabled
        self.theme_preview_check.setChecked(True)         # Default enabled
    
    def _apply_settings(self):
        """Apply current settings"""
        try:
            # Update configuration
            self.config.update_settings(**{
                'conversion.jpeg_quality': self.jpeg_quality_slider.value(),
                'conversion.webp_quality': self.webp_quality_slider.value(),
                'conversion.png_compression': self.png_compression_slider.value(),
                'conversion.default_output_format': self.default_format_combo.currentText(),
                'conversion.max_image_size': self.max_size_spin.value(),
                'conversion.maintain_aspect_ratio': self.maintain_aspect_check.isChecked(),
                'ui.window_width': self.window_width_spin.value(),
                'ui.window_height': self.window_height_spin.value(),
                'ui.show_preview': self.show_preview_check.isChecked(),
                'ui.auto_save_settings': self.auto_save_check.isChecked(),
                'logging_level': self.log_level_combo.currentText(),
                'enable_sentry': self.enable_sentry_check.isChecked(),
                'check_updates': self.check_updates_check.isChecked()
            })
            
            # Apply theme and language through appearance manager
            if self.appearance_manager:
                # Apply theme
                selected_theme_display = self.theme_combo.currentText()
                if selected_theme_display in self.theme_mapping:
                    theme_name = self.theme_mapping[selected_theme_display]
                    success = self.appearance_manager.set_theme(theme_name)
                    if not success:
                        logger.warning(f"Failed to apply theme: {theme_name}")
                
                # Apply language
                language_code = self.language_combo.currentData()
                if language_code:
                    success = self.appearance_manager.set_language(language_code)
                    if not success:
                        logger.warning(f"Failed to apply language: {language_code}")
            
            self.settings_changed.emit()
            
            QMessageBox.information(self, "Settings", "Settings applied successfully!")
            logger.info("Settings applied by user")
            
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {e}")
    
    def _reset_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n\n"
            "This will reset:\n"
            "• Conversion settings\n"
            "• Theme and language\n"
            "• Window preferences\n"
            "• Advanced options",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset to default configuration
            from ..core.config import AppSettings
            default_settings = AppSettings()
            
            self.config._settings = default_settings
            self.config.save()
            
            # Reset appearance to defaults
            if self.appearance_manager:
                self.appearance_manager.set_theme('light')
                self.appearance_manager.set_language('en')
            
            self._load_settings()
            self.settings_changed.emit()
            
            QMessageBox.information(self, "Settings", "Settings reset to defaults!")
            logger.info("Settings reset to defaults")
    
    def _reset_ui_settings(self):
        """Reset only UI settings"""
        reply = QMessageBox.question(
            self,
            "Reset UI Settings",
            "Reset theme, language, and window settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset UI settings
            self.config.update_settings(**{
                'ui.window_width': 800,
                'ui.window_height': 600,
                'ui.theme': 'light',
                'ui.language': 'en',
                'ui.show_preview': True,
                'ui.auto_save_settings': True
            })
            
            # Apply defaults through appearance manager
            if self.appearance_manager:
                self.appearance_manager.set_theme('light')
                self.appearance_manager.set_language('en')
            
            self._load_settings()
            QMessageBox.information(self, "Reset", "UI settings reset to defaults!")
    
    def _reset_conversion_settings(self):
        """Reset only conversion settings"""
        reply = QMessageBox.question(
            self,
            "Reset Conversion Settings",
            "Reset quality, format, and processing settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset conversion settings
            self.config.update_settings(**{
                'conversion.jpeg_quality': 85,
                'conversion.webp_quality': 85,
                'conversion.png_compression': 6,
                'conversion.default_output_format': 'png',
                'conversion.max_image_size': 4096,
                'conversion.maintain_aspect_ratio': True
            })
            
            self._load_settings()
            QMessageBox.information(self, "Reset", "Conversion settings reset to defaults!")
    
    def _optimize_database(self):
        """Optimize database"""
        try:
            # Get database manager from parent
            parent_window = self.parent_window
            while parent_window and not hasattr(parent_window, 'db_manager'):
                parent_window = parent_window.parent()
            
            if parent_window and hasattr(parent_window, 'db_manager'):
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
            "Database Files (*.db)"
        )
        
        if backup_path:
            try:
                import shutil
                
                # Get database path from parent
                parent_window = self.parent_window
                while parent_window and not hasattr(parent_window, 'db_manager'):
                    parent_window = parent_window.parent()
                
                if parent_window and hasattr(parent_window, 'db_manager'):
                    shutil.copy2(parent_window.db_manager.db_path, backup_path)
                    
                    QMessageBox.information(self, "Backup", f"Database backed up to:\n{backup_path}")
                    logger.info(f"Database backed up to {backup_path}")
                else:
                    QMessageBox.warning(self, "Error", "Cannot access database manager")
                
            except Exception as e:
                logger.error(f"Error backing up database: {e}")
                QMessageBox.critical(self, "Error", f"Failed to backup database: {e}")
    
    def _clear_history(self):
        """Clear conversion history"""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all conversion history?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Get database manager from parent
                parent_window = self.parent_window
                while parent_window and not hasattr(parent_window, 'db_manager'):
                    parent_window = parent_window.parent()
                
                if parent_window and hasattr(parent_window, 'db_manager'):
                    with parent_window.db_manager.get_connection() as conn:
                        conn.execute("DELETE FROM conversion_history")
                        conn.commit()
                    
                    QMessageBox.information(self, "Clear History", "Conversion history cleared successfully!")
                    logger.info("Conversion history cleared by user")
                else:
                    QMessageBox.warning(self, "Error", "Cannot access database manager")
                
            except Exception as e:
                logger.error(f"Error clearing history: {e}")
                QMessageBox.critical(self, "Error", f"Failed to clear history: {e}")
    
    def refresh_appearance(self):
        """Refresh UI when appearance changes"""
        # This method can be called when themes change
        # Reload current settings to reflect any theme-related changes
        self._load_settings()
        self.update()  # Force widget repaint
        
        logger.debug("Settings tab appearance refreshed")
    
    def get_appearance_manager(self):
        """Get appearance manager reference"""
        return self.appearance_manager
    
    def set_appearance_manager(self, appearance_manager):
        """Set appearance manager reference"""
        self.appearance_manager = appearance_manager
        # Refresh UI to reflect new appearance options
        self._load_settings()