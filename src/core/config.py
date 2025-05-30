"""Application configuration management using Pydantic"""

from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import json
from loguru import logger


class ConversionSettings(BaseModel):
    """Conversion settings model"""

    jpeg_quality: int = Field(default=85, ge=1, le=100)
    webp_quality: int = Field(default=85, ge=1, le=100)
    png_compression: int = Field(default=6, ge=0, le=9)
    default_output_format: str = Field(default="png")
    maintain_aspect_ratio: bool = Field(default=True)
    max_image_size: int = Field(default=4096)  # pixels

    @validator("default_output_format")
    def validate_output_format(cls, v):
        valid_formats = ["png", "jpg", "jpeg", "webp", "ico"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Output format must be one of {valid_formats}")
        return v.lower()


class UISettings(BaseModel):
    """UI settings model"""

    window_width: int = Field(default=800, ge=600)
    window_height: int = Field(default=600, ge=400)
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    theme: str = Field(default="light")
    language: str = Field(default="en")
    show_preview: bool = Field(default=True)
    auto_save_settings: bool = Field(default=True)

    @validator("theme")
    def validate_theme(cls, v):
        valid_themes = ["light", "dark", "auto"]
        if v not in valid_themes:
            raise ValueError(f"Theme must be one of {valid_themes}")
        return v


class AppSettings(BaseModel):
    """Main application settings"""

    conversion: ConversionSettings = Field(default_factory=ConversionSettings)
    ui: UISettings = Field(default_factory=UISettings)
    logging_level: str = Field(default="INFO")
    enable_sentry: bool = Field(default=True)
    check_updates: bool = Field(default=True)

    @validator("logging_level")
    def validate_logging_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Logging level must be one of {valid_levels}")
        return v.upper()


class AppConfig:
    """Application configuration manager"""

    def __init__(self, app_data_dir: Path):
        self.app_data_dir = app_data_dir
        self.config_file = app_data_dir / "config.json"
        self._settings: Optional[AppSettings] = None
        self.load()

    @property
    def settings(self) -> AppSettings:
        """Get current settings"""
        if self._settings is None:
            self._settings = AppSettings()
        return self._settings

    def load(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._settings = AppSettings(**data)
                logger.info("Configuration loaded successfully")
            else:
                self._settings = AppSettings()
                self.save()  # Create default config
                logger.info("Created default configuration")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._settings = AppSettings()

    def save(self) -> None:
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.settings.dict(), f, indent=2, ensure_ascii=False)
            logger.debug("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def update_settings(self, **kwargs) -> None:
        """Update settings and save"""
        try:
            current_data = self.settings.dict()

            # Update nested settings
            for key, value in kwargs.items():
                if "." in key:
                    section, setting = key.split(".", 1)
                    if section in current_data:
                        current_data[section][setting] = value
                else:
                    current_data[key] = value

            self._settings = AppSettings(**current_data)
            self.save()
            logger.debug(f"Settings updated: {kwargs}")
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
