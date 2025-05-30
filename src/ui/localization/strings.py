# src/ui/localization/strings.py
"""
Translatable strings for the application
Use tr() function for all user-facing strings
"""

from PyQt6.QtCore import QCoreApplication

def tr(text: str, context: str = "Global") -> str:
    """Translate text using Qt translation system"""
    return QCoreApplication.translate(context, text)

# Common strings used throughout the application
class Strings:
    """Container for translatable strings"""
    
    # Main window
    MAIN_WINDOW_TITLE = lambda: tr("Image Converter Pro", "MainWindow")
    
    # Tabs
    TAB_CONVERT = lambda: tr("Convert", "MainWindow")
    TAB_HISTORY = lambda: tr("History", "MainWindow") 
    TAB_SETTINGS = lambda: tr("Settings", "MainWindow")
    TAB_GIF_TOOLS = lambda: tr("GIF Tools", "MainWindow")
    
    # Conversion
    CONVERT_SINGLE_FILE = lambda: tr("Convert Single File", "ConversionTab")
    BATCH_CONVERT = lambda: tr("Batch Convert", "ConversionTab")
    TARGET_FORMAT = lambda: tr("Target Format:", "ConversionTab")
    QUALITY = lambda: tr("Quality:", "ConversionTab")
    CONVERSION_SETTINGS = lambda: tr("Conversion Settings", "ConversionTab")
    MAINTAIN_ASPECT_RATIO = lambda: tr("Maintain Aspect Ratio", "ConversionTab")
    
    # Status messages
    STATUS_READY = lambda: tr("Ready", "StatusBar")
    STATUS_CONVERTING = lambda: tr("Converting images...", "StatusBar")
    STATUS_COMPLETED = lambda: tr("Conversion completed", "StatusBar")
    
    # Buttons
    BTN_OK = lambda: tr("OK", "Buttons")
    BTN_CANCEL = lambda: tr("Cancel", "Buttons")
    BTN_APPLY = lambda: tr("Apply", "Buttons")
    BTN_BROWSE = lambda: tr("Browse", "Buttons")
    
    # File dialogs
    SELECT_IMAGE_FILE = lambda: tr("Select Image File", "FileDialog")
    SELECT_OUTPUT_DIR = lambda: tr("Select Output Directory", "FileDialog")
    SAVE_AS = lambda: tr("Save As", "FileDialog")
    
    # Messages
    CONVERSION_SUCCESS = lambda: tr("Conversion completed successfully!", "Messages")
    CONVERSION_FAILED = lambda: tr("Conversion failed", "Messages")
    NO_FILES_SELECTED = lambda: tr("No files selected", "Messages")


