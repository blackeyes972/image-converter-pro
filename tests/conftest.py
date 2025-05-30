"""Pytest configuration and fixtures"""

import pytest
import tempfile
import shutil
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from src.core.config import AppConfig
from src.core.database import DatabaseManager


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration"""
    return AppConfig(temp_dir)


@pytest.fixture
def test_db(temp_dir):
    """Create test database"""
    return DatabaseManager(temp_dir / "test.db")


@pytest.fixture
def sample_image(temp_dir):
    """Create sample test image"""
    from PIL import Image

    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="red")
    image_path = temp_dir / "test_image.png"
    img.save(image_path)

    return image_path
