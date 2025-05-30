

# src/ui/localization/translation_manager.py
"""
Translation management system with Qt Linguist integration
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from PyQt6.QtCore import QTranslator, QLocale, QCoreApplication, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from loguru import logger

from ...core.config import AppConfig


class TranslationManager(QObject):
    """Manages application translations and localization"""
    
    language_changed = pyqtSignal(str)  # language_code
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.translations_dir = Path(__file__).parent / "translations"
        self.translations_dir.mkdir(exist_ok=True)
        
        # Current translator instances
        self.app_translator = QTranslator()
        self.qt_translator = QTranslator()
        
        # Available languages
        self._available_languages = self._scan_available_languages()
        
        logger.info("Translation manager initialized")
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get dictionary of available language codes and names"""
        return {
            'en': 'English',
            'it': 'Italiano', 
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'pt': 'Português',
            'ru': 'Русский',
            'zh': '中文',
            'ja': '日本語',
            'ko': '한국어'
        }
    
    def get_system_language(self) -> str:
        """Get system default language code"""
        try:
            system_locale = QLocale.system()
            language_code = system_locale.name()[:2]  # Get just language part (e.g., 'en' from 'en_US')
            
            # Return if we support this language, otherwise default to English
            available = self.get_available_languages()
            return language_code if language_code in available else 'en'
            
        except Exception as e:
            logger.error(f"Error detecting system language: {e}")
            return 'en'
    
    def apply_language(self, language_code: str = None) -> bool:
        """Apply language to application"""
        if language_code is None:
            # Use configured language or detect system language
            language_code = self.config.settings.ui.language
            if language_code == 'auto':
                language_code = self.get_system_language()
        
        try:
            app = QApplication.instance()
            if not app:
                logger.error("No QApplication instance found")
                return False
            
            # Remove current translators
            app.removeTranslator(self.app_translator)
            app.removeTranslator(self.qt_translator)
            
            # Don't load translations for English (default)
            if language_code == 'en':
                logger.info("Using default English language")
                self.language_changed.emit(language_code)
                return True
            
            # Load application translations
            app_translation_file = self.translations_dir / f"imageconverter_{language_code}.qm"
            if app_translation_file.exists():
                if self.app_translator.load(str(app_translation_file)):
                    app.installTranslator(self.app_translator)
                    logger.info(f"Loaded application translation: {language_code}")
                else:
                    logger.warning(f"Failed to load app translation: {app_translation_file}")
            else:
                logger.warning(f"Translation file not found: {app_translation_file}")
            
            # Load Qt built-in translations
            qt_translation_file = self.translations_dir / f"qt_{language_code}.qm"
            if qt_translation_file.exists():
                if self.qt_translator.load(str(qt_translation_file)):
                    app.installTranslator(self.qt_translator)
                    logger.info(f"Loaded Qt translation: {language_code}")
            
            # Update configuration
            if language_code != self.config.settings.ui.language:
                self.config.update_settings(**{'ui.language': language_code})
            
            # Emit signal
            self.language_changed.emit(language_code)
            
            logger.info(f"Applied language: {language_code}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying language '{language_code}': {e}")
            return False
    
    def get_current_language(self) -> str:
        """Get current language code"""
        return self.config.settings.ui.language
    
    def create_translation_files(self, language_code: str) -> List[Path]:
        """Create translation template files for a language"""
        files_created = []
        
        try:
            # Create .ts file for translation
            ts_file = self.translations_dir / f"imageconverter_{language_code}.ts"
            
            # Basic TS file template
            ts_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="{language_code}">
<context>
    <name>MainWindow</name>
    <message>
        <source>Convert</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <source>History</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <source>Settings</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <source>GIF Tools</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>ConversionTab</name>
    <message>
        <source>Convert Single File</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <source>Batch Convert</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <source>Target Format:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <source>Quality:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <source>Conversion Settings</source>
        <translation type="unfinished"></translation>
    </message>
</context>
</TS>"""
            
            with open(ts_file, 'w', encoding='utf-8') as f:
                f.write(ts_content)
            
            files_created.append(ts_file)
            logger.info(f"Created translation file: {ts_file}")
            
        except Exception as e:
            logger.error(f"Error creating translation files for {language_code}: {e}")
        
        return files_created
    
    def _scan_available_languages(self) -> List[str]:
        """Scan for available translation files"""
        available = ['en']  # English is always available (default)
        
        try:
            for qm_file in self.translations_dir.glob("imageconverter_*.qm"):
                language_code = qm_file.stem.split('_')[1]
                if language_code not in available:
                    available.append(language_code)
        except Exception as e:
            logger.error(f"Error scanning translation files: {e}")
        
        return available


