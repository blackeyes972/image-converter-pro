"""Main application window"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QMenuBar,
    QStatusBar,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import QTimer, QDateTime, Qt
from PyQt6.QtGui import QAction, QIcon
from loguru import logger

from ..core.config import AppConfig
from ..core.database import DatabaseManager
from .conversion_tab import ConversionTab
from .history_tab import HistoryTab
from .settings_tab import SettingsTab


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, config: AppConfig, db_manager: DatabaseManager):
        super().__init__()
        self.config = config
        self.db_manager = db_manager

        self.setWindowTitle("Image Converter Pro v3.0")
        self.setMinimumSize(800, 600)

        # Apply saved window settings
        self._apply_window_settings()

        # Setup UI
        self._create_menus()
        self._create_status_bar()
        self._create_central_widget()

        logger.info("Main window initialized")

    def _apply_window_settings(self):
        """Apply saved window settings"""
        ui_settings = self.config.settings.ui

        self.resize(ui_settings.window_width, ui_settings.window_height)

        if ui_settings.window_x is not None and ui_settings.window_y is not None:
            self.move(ui_settings.window_x, ui_settings.window_y)

    def _create_menus(self):
        """Create application menus"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_status_bar(self):
        """Create status bar with clock"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        self.status_bar.addPermanentWidget(separator)

        # Clock label
        self.clock_label = QLabel()
        self.status_bar.addPermanentWidget(self.clock_label)

        # Update clock every second
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        """Update status bar clock"""
        current_time = QDateTime.currentDateTime().toString("dd/MM/yyyy hh:mm:ss")
        self.clock_label.setText(current_time)

    def _create_central_widget(self):
        """Create central widget with tabs"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Add tabs
        self.conversion_tab = ConversionTab(self.config, self.db_manager, self)
        self.history_tab = HistoryTab(self.db_manager, self)
        self.settings_tab = SettingsTab(self.config, self)

        self.tab_widget.addTab(self.conversion_tab, "Convert")
        self.tab_widget.addTab(self.history_tab, "History")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        # Connect signals
        self.conversion_tab.status_message.connect(self.status_label.setText)
        self.settings_tab.settings_changed.connect(self._on_settings_changed)

    def _show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "About Image Converter Pro",
            """
            <h2>Image Converter Pro v3.0</h2>
            <p>Professional image conversion application built with PyQt6</p>
            <p><b>Features:</b></p>
            <ul>
                <li>Batch image conversion</li>
                <li>Multiple format support</li>
                <li>Image resizing and optimization</li>
                <li>Conversion history tracking</li>
                <li>Enterprise-grade logging</li>
            </ul>
            <p><b>© 2025 Alessandro Castaldi</b></p>
            """,
        )

    def _on_settings_changed(self):
        """Handle settings changes"""
        logger.info("Settings changed, applying updates")
        # Apply any immediate settings changes here

    def closeEvent(self, event):
        """Handle window close event"""
        # Save window position and size
        geometry = self.geometry()
        self.config.update_settings(
            **{
                "ui.window_width": geometry.width(),
                "ui.window_height": geometry.height(),
                "ui.window_x": geometry.x(),
                "ui.window_y": geometry.y(),
            }
        )

        logger.info("Application closing")
        event.accept()
