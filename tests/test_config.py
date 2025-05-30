"""Test configuration management"""

import pytest
from src.core.config import AppConfig, AppSettings, ConversionSettings


def test_default_config(test_config):
    """Test default configuration creation"""
    settings = test_config.settings
    assert isinstance(settings, AppSettings)
    assert settings.conversion.jpeg_quality == 85
    assert settings.ui.window_width == 800


def test_save_load_config(test_config):
    """Test saving and loading configuration"""
    # Modify settings
    test_config.update_settings(**{"conversion.jpeg_quality": 95, "ui.window_width": 1000})

    # Create new config instance with same directory
    new_config = AppConfig(test_config.app_data_dir)

    # Verify settings were persisted
    assert new_config.settings.conversion.jpeg_quality == 95
    assert new_config.settings.ui.window_width == 1000


def test_invalid_settings():
    """Test validation of invalid settings"""
    with pytest.raises(ValueError):
        ConversionSettings(jpeg_quality=150)  # Invalid quality > 100

    with pytest.raises(ValueError):
        ConversionSettings(default_output_format="invalid")  # Invalid format
