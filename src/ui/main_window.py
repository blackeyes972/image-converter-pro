"""Main application window with theme and translation support"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTabWidget, QMenuBar, QStatusBar, QLabel, QFrame)
from PyQt6.QtCore import QTimer, QDateTime, Qt
from PyQt6.QtGui import QAction, QIcon
from loguru import logger

from ..core.config import AppConfig
from ..core.database import DatabaseManager
from .conversion_tab import ConversionTab
from .history_tab import HistoryTab
from .settings_tab import SettingsTab


class MainWindow(QMainWindow):
    """Main application window with appearance management"""
    
    def __init__(self, config: AppConfig, db_manager: DatabaseManager):
        super().__init__()
        self.config = config
        self.db_manager = db_manager
        
        # Initialize appearance manager first (before UI creation)
        self._initialize_appearance_manager()
        
        self.setWindowTitle("Image Converter Pro v3.0")
        self.setMinimumSize(800, 600)
        
        # Apply saved window settings
        self._apply_window_settings()
        
        # Setup UI
        self._create_menus()
        self._create_status_bar()
        self._create_central_widget()
        
        # Initialize appearance after UI is created
        self._finalize_appearance_setup()
        
        logger.info("Main window initialized with appearance management")
    
    def _initialize_appearance_manager(self):
        """Initialize appearance manager before UI creation"""
        try:
            from .appearance_manager import AppearanceManager
            self.appearance_manager = AppearanceManager(self.config)
            logger.info("Appearance manager initialized")
        except ImportError as e:
            logger.warning(f"Appearance manager not available: {e}")
            self.appearance_manager = None
        except Exception as e:
            logger.error(f"Error initializing appearance manager: {e}")
            self.appearance_manager = None
    
    def _finalize_appearance_setup(self):
        """Finalize appearance setup after UI is created"""
        if self.appearance_manager:
            try:
                # Initialize with saved settings
                self.appearance_manager.initialize()
                
                # Connect appearance changes
                self.appearance_manager.appearance_changed.connect(self._on_appearance_changed)
                
                logger.info("Appearance system fully initialized")
            except Exception as e:
                logger.error(f"Error finalizing appearance setup: {e}")
    
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
        
        # View menu (for appearance options)
        view_menu = menubar.addMenu("&View")
        
        # Theme submenu
        if self.appearance_manager:
            theme_menu = view_menu.addMenu("&Theme")
            
            themes = self.appearance_manager.get_available_themes()
            for theme_name in themes:
                theme_action = QAction(theme_name.title(), self)
                theme_action.triggered.connect(lambda checked, t=theme_name: self._change_theme(t))
                theme_menu.addAction(theme_action)
            
            # Language submenu
            language_menu = view_menu.addMenu("&Language")
            
            languages = self.appearance_manager.get_available_languages()
            for lang_code, lang_name in languages.items():
                lang_action = QAction(lang_name, self)
                lang_action.triggered.connect(lambda checked, code=lang_code: self._change_language(code))
                language_menu.addAction(lang_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(lambda: self._switch_to_settings_tab())
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
        
        # Theme indicator (optional)
        if self.appearance_manager:
            self.theme_indicator = QLabel()
            self.status_bar.addPermanentWidget(self.theme_indicator)
            self._update_theme_indicator()
            
            # Another separator
            separator2 = QFrame()
            separator2.setFrameShape(QFrame.Shape.VLine)
            self.status_bar.addPermanentWidget(separator2)
        
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
    
    def _update_theme_indicator(self):
        """Update theme indicator in status bar"""
        if self.appearance_manager:
            current_theme = self.appearance_manager.get_current_theme()
            current_lang = self.appearance_manager.get_current_language()
            lang_display = self.appearance_manager.get_available_languages().get(current_lang, current_lang)
            
            self.theme_indicator.setText(f"{current_theme.title()} | {lang_display}")
    
    def _create_central_widget(self):
        """Create central widget with tabs"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add core tabs
        self.conversion_tab = ConversionTab(self.config, self.db_manager, self)
        self.history_tab = HistoryTab(self.db_manager, self)
        self.settings_tab = SettingsTab(self.config, self)
        
        self.tab_widget.addTab(self.conversion_tab, "Convert")
        self.tab_widget.addTab(self.history_tab, "History")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Connect core tab signals
        self.conversion_tab.status_message.connect(self.status_label.setText)
        self.settings_tab.settings_changed.connect(self._on_settings_changed)
        
        # ===============================================
        # EXTENSION LOADING - GIF SUPPORT
        # ===============================================
        
        # Load extensions
        try:
            from ..extensions.extension_manager import ExtensionManager
            self.extension_manager = ExtensionManager(self.config, self.db_manager)
            
            # Load GIF extension
            gif_tab = self.extension_manager.load_gif_extension(self.tab_widget)
            if gif_tab:
                # Connect GIF tab signals to main window
                gif_tab.status_message.connect(self.status_label.setText)
                logger.info("GIF extension integrated successfully")
                
                # Update menu to reflect GIF capability
                self._update_menus_for_extensions()
            else:
                logger.warning("GIF extension failed to load")
                
        except ImportError:
            logger.info("Extensions module not available - running with core features only")
            self.extension_manager = None
        except Exception as e:
            logger.error(f"Error loading extensions: {e}")
            logger.info("Continuing with core features only")
            self.extension_manager = None
    
    def _update_menus_for_extensions(self):
        """Update menus when extensions are loaded"""
        try:
            # Add GIF-specific menu items if extension is loaded
            if hasattr(self, 'extension_manager') and self.extension_manager and self.extension_manager.get_extension('gif'):
                # Find Tools menu
                tools_menu = None
                for action in self.menuBar().actions():
                    if action.text() == "&Tools":
                        tools_menu = action.menu()
                        break
                
                if tools_menu:
                    # Add separator
                    tools_menu.addSeparator()
                    
                    # Add GIF-specific actions
                    gif_action = QAction("&GIF Tools", self)
                    gif_action.setShortcut("Ctrl+G")
                    gif_action.triggered.connect(self._switch_to_gif_tab)
                    tools_menu.addAction(gif_action)
                    
                    logger.debug("Added GIF menu items")
                    
        except Exception as e:
            logger.error(f"Error updating menus for extensions: {e}")
    
    def _switch_to_gif_tab(self):
        """Switch to GIF tab via menu action"""
        try:
            # Find GIF tab by looking for tab with "GIF" in title
            for i in range(self.tab_widget.count()):
                if "GIF" in self.tab_widget.tabText(i):
                    self.tab_widget.setCurrentIndex(i)
                    self.status_label.setText("Switched to GIF Tools")
                    break
        except Exception as e:
            logger.error(f"Error switching to GIF tab: {e}")
    
    def _switch_to_settings_tab(self):
        """Switch to settings tab via menu action"""
        try:
            # Find settings tab
            for i in range(self.tab_widget.count()):
                if "Settings" in self.tab_widget.tabText(i):
                    self.tab_widget.setCurrentIndex(i)
                    self.status_label.setText("Switched to Settings")
                    break
        except Exception as e:
            logger.error(f"Error switching to settings tab: {e}")
    
    def _change_theme(self, theme_name: str):
        """Change theme via menu action"""
        if self.appearance_manager:
            success = self.appearance_manager.set_theme(theme_name)
            if success:
                self.status_label.setText(f"Applied {theme_name.title()} theme")
            else:
                self.status_label.setText(f"Failed to apply {theme_name} theme")
    
    def _change_language(self, language_code: str):
        """Change language via menu action"""
        if self.appearance_manager:
            success = self.appearance_manager.set_language(language_code)
            if success:
                lang_name = self.appearance_manager.get_available_languages().get(language_code, language_code)
                self.status_label.setText(f"Applied {lang_name} language")
            else:
                self.status_label.setText(f"Failed to apply language")
    
    def _show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Check if extensions are loaded for about dialog
        extensions_info = ""
        if hasattr(self, 'extension_manager') and self.extension_manager:
            loaded_extensions = self.extension_manager.list_extensions()
            if loaded_extensions:
                extension_names = list(loaded_extensions.keys())
                extensions_info = f"<li>Extensions: {', '.join(extension_names).upper()}</li>"
        
        # Check appearance features
        appearance_info = ""
        if self.appearance_manager:
            themes = len(self.appearance_manager.get_available_themes())
            languages = len(self.appearance_manager.get_available_languages())
            appearance_info = f"<li>Themes: {themes} available</li><li>Languages: {languages} supported</li>"
        
        QMessageBox.about(
            self,
            "About Image Converter Pro",
            f"""
            <h2>Image Converter Pro v3.0</h2>
            <p>Professional image conversion application built with PyQt6</p>
            <p><b>Features:</b></p>
            <ul>
                <li>Batch image conversion</li>
                <li>Multiple format support</li>
                <li>Image resizing and optimization</li>
                <li>Conversion history tracking</li>
                <li>Enterprise-grade logging</li>
                {appearance_info}
                {extensions_info}
            </ul>
            <p><b>© 2025 Alessandro Castaldi</b></p>
            """
        )
    
    def _on_settings_changed(self):
        """Handle settings changes"""
        logger.info("Settings changed, applying updates")
        
        # Refresh appearance if settings changed
        if self.appearance_manager:
            try:
                # Re-apply current settings in case they changed
                self.appearance_manager.initialize()
                logger.debug("Appearance refreshed after settings change")
            except Exception as e:
                logger.error(f"Error refreshing appearance after settings change: {e}")
        
        # Notify extensions of settings changes if they exist
        try:
            if hasattr(self, 'extension_manager') and self.extension_manager:
                # Extensions can react to settings changes if needed
                # This is a hook for future extension capabilities
                pass
        except Exception as e:
            logger.error(f"Error notifying extensions of settings change: {e}")
    
    def _on_appearance_changed(self):
        """Handle appearance changes (theme/language switch)"""
        try:
            # Update status bar theme indicator
            if hasattr(self, 'theme_indicator'):
                self._update_theme_indicator()
            
            # Force UI refresh
            self.update()
            
            # Notify all tabs of appearance change
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if hasattr(widget, 'refresh_appearance'):
                    try:
                        widget.refresh_appearance()
                    except Exception as e:
                        logger.error(f"Error refreshing appearance for tab {i}: {e}")
            
            # Update window title if language changed
            self.setWindowTitle("Image Converter Pro v3.0")
            
            logger.debug("Appearance change handling completed")
            
        except Exception as e:
            logger.error(f"Error handling appearance change: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save window position and size
        geometry = self.geometry()
        self.config.update_settings(**{
            'ui.window_width': geometry.width(),
            'ui.window_height': geometry.height(),
            'ui.window_x': geometry.x(),
            'ui.window_y': geometry.y()
        })
        
        # Cleanup extensions if they exist
        try:
            if hasattr(self, 'extension_manager') and self.extension_manager:
                # Cancel any running extension operations
                gif_extension = self.extension_manager.get_extension('gif')
                if gif_extension:
                    # Cancel any running workers
                    if hasattr(gif_extension, 'creation_worker') and gif_extension.creation_worker:
                        if gif_extension.creation_worker.isRunning():
                            gif_extension.creation_worker.cancel()
                            gif_extension.creation_worker.wait(3000)  # Wait up to 3 seconds
                    
                    if hasattr(gif_extension, 'optimization_worker') and gif_extension.optimization_worker:
                        if gif_extension.optimization_worker.isRunning():
                            gif_extension.optimization_worker.cancel()
                            gif_extension.optimization_worker.wait(3000)
                
                logger.info("Extensions cleanup completed")
                
        except Exception as e:
            logger.error(f"Error during extension cleanup: {e}")
        
        logger.info("Application closing")
        event.accept()
    
    # ===============================================
    # EXTENSION SUPPORT METHODS
    # ===============================================
    
    def get_extension_manager(self):
        """Get extension manager instance"""
        return getattr(self, 'extension_manager', None)
    
    def is_extension_loaded(self, extension_name: str) -> bool:
        """Check if specific extension is loaded"""
        if hasattr(self, 'extension_manager') and self.extension_manager:
            return self.extension_manager.get_extension(extension_name) is not None
        return False
    
    def get_loaded_extensions(self) -> list:
        """Get list of loaded extension names"""
        if hasattr(self, 'extension_manager') and self.extension_manager:
            return list(self.extension_manager.list_extensions().keys())
        return []
    
    # ===============================================
    # APPEARANCE SUPPORT METHODS
    # ===============================================
    
    def get_appearance_manager(self):
        """Get appearance manager instance"""
        return getattr(self, 'appearance_manager', None)
    
    def is_appearance_system_available(self) -> bool:
        """Check if appearance system is available"""
        return self.appearance_manager is not None
    
    def get_current_theme(self) -> str:
        """Get current theme name"""
        if self.appearance_manager:
            return self.appearance_manager.get_current_theme()
        return 'light'
    
    def get_current_language(self) -> str:
        """Get current language code"""
        if self.appearance_manager:
            return self.appearance_manager.get_current_language()
        return 'en'
    
    def set_theme(self, theme_name: str) -> bool:
        """Set application theme"""
        if self.appearance_manager:
            return self.appearance_manager.set_theme(theme_name)
        return False
    
    def set_language(self, language_code: str) -> bool:
        """Set application language"""
        if self.appearance_manager:
            return self.appearance_manager.set_language(language_code)
        return False