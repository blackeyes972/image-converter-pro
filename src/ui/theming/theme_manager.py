# src/ui/theming/theme_manager.py
"""
Theme management system with support for light/dark/custom themes
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPalette, QColor
from loguru import logger

from ...core.config import AppConfig


class ThemeManager(QObject):
    """Manages application themes and styling"""
    
    theme_changed = pyqtSignal(str)  # theme_name
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.themes_dir = Path(__file__).parent / "themes"
        self.themes_dir.mkdir(exist_ok=True)
        
        # Built-in themes
        self.builtin_themes = {
            'light': self._create_light_theme(),
            'dark': self._create_dark_theme(),
            'auto': None  # Will be resolved based on system
        }
        
        # Current theme cache
        self._current_theme = None
        self._current_theme_name = None
        
        logger.info("Theme manager initialized")
    
    def get_available_themes(self) -> list:
        """Get list of available theme names"""
        themes = list(self.builtin_themes.keys())
        
        # Add custom themes from files
        for theme_file in self.themes_dir.glob("*.json"):
            theme_name = theme_file.stem
            if theme_name not in themes:
                themes.append(theme_name)
        
        return sorted(themes)
    
    def apply_theme(self, theme_name: str = None) -> bool:
        """Apply theme to application"""
        if theme_name is None:
            theme_name = self.config.settings.ui.theme
        
        try:
            # Resolve 'auto' theme based on system
            if theme_name == 'auto':
                theme_name = self._detect_system_theme()
            
            # Load theme data
            theme_data = self._load_theme(theme_name)
            if not theme_data:
                logger.warning(f"Theme '{theme_name}' not found, using light theme")
                theme_data = self.builtin_themes['light']
                theme_name = 'light'
            
            # Apply theme
            self._apply_theme_data(theme_data)
            
            # Update cache
            self._current_theme = theme_data
            self._current_theme_name = theme_name
            
            # Save preference
            if theme_name != self.config.settings.ui.theme:
                self.config.update_settings(**{'ui.theme': theme_name})
            
            # Emit signal
            self.theme_changed.emit(theme_name)
            
            logger.info(f"Applied theme: {theme_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying theme '{theme_name}': {e}")
            return False
    
    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme data"""
        return self._current_theme or self.builtin_themes['light']
    
    def get_current_theme_name(self) -> str:
        """Get current theme name"""
        return self._current_theme_name or 'light'
    
    def create_custom_theme(self, name: str, base_theme: str = 'light') -> Path:
        """Create custom theme file based on existing theme"""
        base_data = self._load_theme(base_theme) or self.builtin_themes['light']
        
        # Add metadata
        theme_data = {
            'metadata': {
                'name': name,
                'description': f'Custom theme based on {base_theme}',
                'author': 'User',
                'version': '1.0.0'
            },
            **base_data
        }
        
        # Save to file
        theme_file = self.themes_dir / f"{name}.json"
        with open(theme_file, 'w', encoding='utf-8') as f:
            json.dump(theme_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created custom theme: {theme_file}")
        return theme_file
    
    def _load_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Load theme data"""
        # Check built-in themes first
        if theme_name in self.builtin_themes:
            return self.builtin_themes[theme_name]
        
        # Check custom theme files
        theme_file = self.themes_dir / f"{theme_name}.json"
        if theme_file.exists():
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading theme file {theme_file}: {e}")
        
        return None
    
    def _apply_theme_data(self, theme_data: Dict[str, Any]):
        """Apply theme data to application"""
        app = QApplication.instance()
        if not app:
            return
        
        # Apply stylesheet if present
        if 'stylesheet' in theme_data:
            app.setStyleSheet(theme_data['stylesheet'])
        
        # Apply palette if present
        if 'palette' in theme_data:
            palette = self._create_palette_from_data(theme_data['palette'])
            app.setPalette(palette)
    
    def _create_palette_from_data(self, palette_data: Dict[str, str]) -> QPalette:
        """Create QPalette from color data"""
        palette = QPalette()
        
        # Color role mapping
        role_mapping = {
            'window': QPalette.ColorRole.Window,
            'windowText': QPalette.ColorRole.WindowText,
            'base': QPalette.ColorRole.Base,
            'text': QPalette.ColorRole.Text,
            'button': QPalette.ColorRole.Button,
            'buttonText': QPalette.ColorRole.ButtonText,
            'highlight': QPalette.ColorRole.Highlight,
            'highlightedText': QPalette.ColorRole.HighlightedText,
            'toolTipBase': QPalette.ColorRole.ToolTipBase,
            'toolTipText': QPalette.ColorRole.ToolTipText,
        }
        
        for color_name, color_value in palette_data.items():
            if color_name in role_mapping:
                color = QColor(color_value)
                palette.setColor(role_mapping[color_name], color)
        
        return palette
    
    def _detect_system_theme(self) -> str:
        """Detect system theme preference"""
        try:
            # Try to detect system dark mode
            app = QApplication.instance()
            if app:
                palette = app.palette()
                window_color = palette.color(QPalette.ColorRole.Window)
                # If window background is dark, assume dark theme
                if window_color.lightness() < 128:
                    return 'dark'
            
            return 'light'  # Default fallback
            
        except Exception:
            return 'light'
    
    def _create_light_theme(self) -> Dict[str, Any]:
        """Create built-in light theme"""
        return {
            'palette': {
                'window': '#F8FAFC',
                'windowText': '#1E293B',
                'base': '#FFFFFF',
                'text': '#334155',
                'button': '#E2E8F0',
                'buttonText': '#475569',
                'highlight': '#3B82F6',
                'highlightedText': '#FFFFFF',
                'toolTipBase': '#FEF3C7',
                'toolTipText': '#92400E',
            },
            'stylesheet': """
                /* Main Window Styling */
                QMainWindow {
                    background-color: #F8FAFC;
                    color: #1E293B;
                }
                
                /* Tab Widget */
                QTabWidget::pane {
                    border: 1px solid #E2E8F0;
                    background-color: #FFFFFF;
                    border-radius: 6px;
                }
                
                QTabWidget::tab-bar {
                    alignment: left;
                }
                
                QTabBar::tab {
                    background-color: #F1F5F9;
                    color: #64748B;
                    border: 1px solid #E2E8F0;
                    border-bottom: none;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                }
                
                QTabBar::tab:selected {
                    background-color: #3B82F6;
                    color: #FFFFFF;
                }
                
                QTabBar::tab:hover:!selected {
                    background-color: #E2E8F0;
                    color: #1E293B;
                }
                
                /* Buttons */
                QPushButton {
                    background-color: #3B82F6;
                    color: #FFFFFF;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                }
                
                QPushButton:hover {
                    background-color: #2563EB;
                }
                
                QPushButton:pressed {
                    background-color: #1D4ED8;
                }
                
                QPushButton:disabled {
                    background-color: #94A3B8;
                    color: #CBD5E1;
                }
                
                /* Group Boxes */
                QGroupBox {
                    font-weight: 600;
                    color: #374151;
                    border: 2px solid #E5E7EB;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 8px;
                }
                
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px 0 8px;
                    background-color: #F8FAFC;
                }
                
                /* Progress Bars */
                QProgressBar {
                    border: 2px solid #E5E7EB;
                    border-radius: 6px;
                    background-color: #F3F4F6;
                    text-align: center;
                    height: 20px;
                }
                
                QProgressBar::chunk {
                    background-color: #10B981;
                    border-radius: 4px;
                }
                
                /* Input Fields */
                QLineEdit, QSpinBox, QComboBox {
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 6px 12px;
                    background-color: #FFFFFF;
                    color: #374151;
                }
                
                QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                    border-color: #3B82F6;
                    outline: none;
                }
                
                /* Status Bar */
                QStatusBar {
                    background-color: #F1F5F9;
                    border-top: 1px solid #E2E8F0;
                    color: #64748B;
                }
            """
        }
    
    def _create_dark_theme(self) -> Dict[str, Any]:
        """Create built-in dark theme"""
        return {
            'palette': {
                'window': '#1E293B',
                'windowText': '#F1F5F9',
                'base': '#0F172A',
                'text': '#E2E8F0',
                'button': '#374151',
                'buttonText': '#F9FAFB',
                'highlight': '#3B82F6',
                'highlightedText': '#FFFFFF',
                'toolTipBase': '#374151',
                'toolTipText': '#F9FAFB',
            },
            'stylesheet': """
                /* Main Window Styling */
                QMainWindow {
                    background-color: #1E293B;
                    color: #F1F5F9;
                }
                
                /* Tab Widget */
                QTabWidget::pane {
                    border: 1px solid #374151;
                    background-color: #0F172A;
                    border-radius: 6px;
                }
                
                QTabBar::tab {
                    background-color: #374151;
                    color: #94A3B8;
                    border: 1px solid #4B5563;
                    border-bottom: none;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                }
                
                QTabBar::tab:selected {
                    background-color: #3B82F6;
                    color: #FFFFFF;
                }
                
                QTabBar::tab:hover:!selected {
                    background-color: #4B5563;
                    color: #F1F5F9;
                }
                
                /* Buttons */
                QPushButton {
                    background-color: #3B82F6;
                    color: #FFFFFF;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                }
                
                QPushButton:hover {
                    background-color: #2563EB;
                }
                
                QPushButton:pressed {
                    background-color: #1D4ED8;
                }
                
                QPushButton:disabled {
                    background-color: #6B7280;
                    color: #9CA3AF;
                }
                
                /* Group Boxes */
                QGroupBox {
                    font-weight: 600;
                    color: #E5E7EB;
                    border: 2px solid #4B5563;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 8px;
                }
                
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px 0 8px;
                    background-color: #1E293B;
                }
                
                /* Progress Bars */
                QProgressBar {
                    border: 2px solid #4B5563;
                    border-radius: 6px;
                    background-color: #374151;
                    text-align: center;
                    height: 20px;
                    color: #E5E7EB;
                }
                
                QProgressBar::chunk {
                    background-color: #10B981;
                    border-radius: 4px;
                }
                
                /* Input Fields */
                QLineEdit, QSpinBox, QComboBox {
                    border: 1px solid #6B7280;
                    border-radius: 6px;
                    padding: 6px 12px;
                    background-color: #374151;
                    color: #F3F4F6;
                }
                
                QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                    border-color: #3B82F6;
                    outline: none;
                }
                
                /* Status Bar */
                QStatusBar {
                    background-color: #374151;
                    border-top: 1px solid #4B5563;
                    color: #9CA3AF;
                }
                
                /* List Widgets */
                QListWidget {
                    background-color: #374151;
                    border: 1px solid #6B7280;
                    border-radius: 6px;
                    color: #E5E7EB;
                }
                
                QListWidget::item {
                    padding: 4px;
                    border-bottom: 1px solid #4B5563;
                }
                
                QListWidget::item:selected {
                    background-color: #3B82F6;
                    color: #FFFFFF;
                }
                
                /* Text Edits */
                QTextEdit {
                    background-color: #374151;
                    border: 1px solid #6B7280;
                    border-radius: 6px;
                    color: #E5E7EB;
                }
            """
        }


