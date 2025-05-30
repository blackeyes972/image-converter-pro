# src/utils/icons.py
"""
Gestore icone per Image Converter Pro
"""

import os
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize

class IconManager:
    """Gestisce le icone dell'applicazione"""
    
    def __init__(self):
        self.assets_dir = Path(__file__).parent.parent.parent / "assets"
        self.icons_dir = self.assets_dir / "icons"
        self._icon_cache = {}
    
    def get_app_icon(self) -> QIcon:
        """Restituisce l'icona principale dell'app"""
        icon_path = self.icons_dir / "app-icon.png"
        return self._load_icon(icon_path)
    
    def get_window_icon(self) -> QIcon:
        """Restituisce l'icona per le finestre"""
        # Su Windows usa .ico, su altri sistemi .png
        if os.name == 'nt':
            icon_path = self.icons_dir / "app-icon.ico"
        else:
            icon_path = self.icons_dir / "app-icon.png"
        
        return self._load_icon(icon_path)
    
    def get_feature_icon(self, feature_name: str, size: int = 24) -> QIcon:
        """Restituisce icona per feature specifica"""
        icon_path = self.assets_dir / "screenshots" / "feature-icons" / f"{feature_name}.png"
        return self._load_icon(icon_path, size)
    
    def _load_icon(self, icon_path: Path, size: int = None) -> QIcon:
        """Carica icona con caching"""
        cache_key = f"{icon_path}_{size}"
        
        if cache_key not in self._icon_cache:
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                if size:
                    # Ridimensiona se richiesto
                    pixmap = icon.pixmap(QSize(size, size))
                    icon = QIcon(pixmap)
                self._icon_cache[cache_key] = icon
            else:
                # Icona di fallback
                self._icon_cache[cache_key] = QIcon()
        
        return self._icon_cache[cache_key]

# Istanza globale
icon_manager = IconManager()