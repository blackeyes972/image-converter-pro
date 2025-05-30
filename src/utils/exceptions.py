"""Exception handling utilities"""

import sys
import traceback
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger


class ExceptionHandler(QObject):
    """Global exception handler"""

    exception_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"Uncaught exception: {error_msg}")

        self.exception_occurred.emit(str(exc_value))


# Global exception handler instance
_exception_handler = ExceptionHandler()


def setup_exception_handler():
    """Setup global exception handler"""
    sys.excepthook = _exception_handler.handle_exception

    def show_error_dialog(error_msg: str):
        """Show error dialog to user"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Unexpected Error")
        msg_box.setText("An unexpected error occurred:")
        msg_box.setDetailedText(error_msg)
        msg_box.exec()

    _exception_handler.exception_occurred.connect(show_error_dialog)
