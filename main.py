"""
Image Converter Pro - PyQt6 Professional Version
Enterprise-grade image conversion application
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir, QStandardPaths
from PyQt6.QtGui import QIcon
import sentry_sdk
from loguru import logger

from src.ui.main_window import MainWindow
from src.core.config import AppConfig
from src.core.database import DatabaseManager
from src.utils.exceptions import setup_exception_handler


def setup_application_directories():
    """Setup application directories for data storage"""
    app_data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    app_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (app_data_dir / "logs").mkdir(exist_ok=True)
    (app_data_dir / "database").mkdir(exist_ok=True)
    (app_data_dir / "temp").mkdir(exist_ok=True)
    
    return app_data_dir


def setup_logging(app_data_dir: Path):
    """Configure Loguru logging"""
    log_dir = app_data_dir / "logs"
    
    # Remove default handler
    logger.remove()
    
    # Add console handler for development
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file handlers
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    # Add error-only file
    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="60 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}"
    )


def setup_sentry():
    """Configure Sentry error tracking"""
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=0.1,
            environment=os.getenv("ENVIRONMENT", "development")
        )
        logger.info("Sentry error tracking initialized")
    else:
        logger.warning("Sentry DSN not configured - error tracking disabled")


def main():
    """Main application entry point"""
    try:
        # Setup application
        app = QApplication(sys.argv)
        app.setApplicationName("Image Converter Pro")
        app.setApplicationVersion("3.0.0")
        app.setOrganizationName("Alessandro Castaldi")
        app.setOrganizationDomain("imageconverter.local")
        
        # Setup directories and logging
        app_data_dir = setup_application_directories()
        setup_logging(app_data_dir)
        setup_sentry()
        setup_exception_handler()
        
        logger.info("Starting Image Converter Pro v3.0.0")
        
        # Initialize configuration and database
        config = AppConfig(app_data_dir)
        db_manager = DatabaseManager(app_data_dir / "database" / "app.db")
        
        # Set application icon
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Create and show main window
        main_window = MainWindow(config, db_manager)
        main_window.show()
        
        logger.info("Application started successfully")
        
        # Run application
        exit_code = app.exec()
        logger.info(f"Application exited with code {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.exception("Fatal error during application startup")
        return 1


if __name__ == "__main__":
    sys.exit(main())
