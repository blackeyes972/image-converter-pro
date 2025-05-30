# src/extensions/extension_manager.py
"""
Extension manager for registering and loading extensions
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QTabWidget
from loguru import logger

from ..core.config import AppConfig
from ..core.database import DatabaseManager


class ExtensionManager:
    """Manages application extensions"""
    
    def __init__(self, config: AppConfig, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.loaded_extensions = {}
        
    def load_gif_extension(self, tab_widget: QTabWidget) -> Optional[Any]:
        """Load GIF extension and add tab to main window"""
        try:
            from .gif_tab import GifTab
            
            gif_tab = GifTab(self.db_manager)
            tab_widget.addTab(gif_tab, "GIF Tools")
            
            self.loaded_extensions['gif'] = gif_tab
            logger.info("GIF extension loaded successfully")
            
            return gif_tab
            
        except ImportError as e:
            logger.error(f"Failed to load GIF extension: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading GIF extension: {e}")
            return None
    
    def get_extension(self, name: str) -> Optional[Any]:
        """Get loaded extension by name"""
        return self.loaded_extensions.get(name)
    
    def list_extensions(self) -> Dict[str, Any]:
        """List all loaded extensions"""
        return self.loaded_extensions.copy()


