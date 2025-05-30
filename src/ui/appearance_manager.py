# src/ui/appearance_manager.py
"""
Combined appearance manager that handles both themes and translations
"""

from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from ..core.config import AppConfig
from .theming.theme_manager import ThemeManager
from .localization.translation_manager import TranslationManager


class AppearanceManager(QObject):
    """Manages both theming and localization"""
    
    appearance_changed = pyqtSignal()  # General appearance change signal
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        
        # Initialize managers
        self.theme_manager = ThemeManager(config)
        self.translation_manager = TranslationManager(config)
        
        # Connect signals
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        self.translation_manager.language_changed.connect(self._on_language_changed)
        
        logger.info("Appearance manager initialized")
    
    def initialize(self):
        """Initialize appearance with saved settings"""
        # Apply saved theme
        self.theme_manager.apply_theme()
        
        # Apply saved language
        self.translation_manager.apply_language()
        
        logger.info("Appearance initialized with saved settings")
    
    def set_theme(self, theme_name: str) -> bool:
        """Set application theme"""
        return self.theme_manager.apply_theme(theme_name)
    
    def set_language(self, language_code: str) -> bool:
        """Set application language"""
        return self.translation_manager.apply_language(language_code)
    
    def get_available_themes(self) -> list:
        """Get available theme names"""
        return self.theme_manager.get_available_themes()
    
    def get_available_languages(self) -> dict:
        """Get available languages"""
        return self.translation_manager.get_available_languages()
    
    def get_current_theme(self) -> str:
        """Get current theme name"""
        return self.theme_manager.get_current_theme_name()
    
    def get_current_language(self) -> str:
        """Get current language code"""
        return self.translation_manager.get_current_language()
    
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        logger.info(f"Theme changed to: {theme_name}")
        self.appearance_changed.emit()
    
    def _on_language_changed(self, language_code: str):
        """Handle language change"""
        logger.info(f"Language changed to: {language_code}")
        self.appearance_changed.emit()


