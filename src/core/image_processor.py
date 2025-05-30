"""Image processing engine with threading support"""

import time
from pathlib import Path
from typing import Optional, Tuple, Callable, Dict, Any
from PIL import Image, ImageOps
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from loguru import logger
from pydantic import BaseModel

from .database import ConversionRecord


class ImageInfo(BaseModel):
    """Model for image information"""

    width: int
    height: int
    format: str
    mode: str
    size_bytes: int


class ConversionParams(BaseModel):
    """Model for conversion parameters"""

    target_format: str
    quality: int = 85
    resize_width: Optional[int] = None
    resize_height: Optional[int] = None
    maintain_aspect: bool = True


class ImageProcessor(QObject):
    """Thread-safe image processor"""

    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage
    conversion_completed = pyqtSignal(str, str)  # source_path, target_path
    conversion_failed = pyqtSignal(str, str)  # source_path, error_message

    def __init__(self):
        super().__init__()
        self.supported_formats = {
            "input": [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".gif"],
            "output": ["jpg", "png", "webp", "ico"],
        }

    def get_image_info(self, image_path: Path) -> ImageInfo:
        """Get image information"""
        try:
            with Image.open(image_path) as img:
                return ImageInfo(
                    width=img.width,
                    height=img.height,
                    format=img.format or "Unknown",
                    mode=img.mode,
                    size_bytes=image_path.stat().st_size,
                )
        except Exception as e:
            logger.error(f"Error getting image info for {image_path}: {e}")
            raise

    def convert_image(
        self,
        source_path: Path,
        target_path: Path,
        params: ConversionParams,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConversionRecord:
        """Convert single image"""
        start_time = time.time()

        try:
            logger.info(f"Converting {source_path} to {target_path}")

            # Get source info
            source_info = self.get_image_info(source_path)
            if progress_callback:
                progress_callback(10)

            # Open and process image
            with Image.open(source_path) as img:
                if progress_callback:
                    progress_callback(30)

                # Resize if needed
                if params.resize_width or params.resize_height:
                    img = self._resize_image(img, params)
                    if progress_callback:
                        progress_callback(60)

                # Convert color mode if needed
                img = self._convert_color_mode(img, params.target_format)
                if progress_callback:
                    progress_callback(80)

                # Save image
                self._save_image(img, target_path, params)
                if progress_callback:
                    progress_callback(100)

            # Create conversion record
            duration_ms = int((time.time() - start_time) * 1000)
            target_size = target_path.stat().st_size

            record = ConversionRecord(
                source_path=str(source_path),
                target_path=str(target_path),
                source_format=source_info.format.lower(),
                target_format=params.target_format,
                source_size=source_info.size_bytes,
                target_size=target_size,
                width=img.width if "img" in locals() else source_info.width,
                height=img.height if "img" in locals() else source_info.height,
                created_at=datetime.now(),
                duration_ms=duration_ms,
                status="completed",
            )

            logger.info(f"Conversion completed in {duration_ms}ms")
            return record

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Conversion failed: {e}")

            # Create failed record
            record = ConversionRecord(
                source_path=str(source_path),
                target_path=str(target_path),
                source_format=source_path.suffix.lower().lstrip("."),
                target_format=params.target_format,
                source_size=source_path.stat().st_size if source_path.exists() else 0,
                target_size=0,
                created_at=datetime.now(),
                duration_ms=duration_ms,
                status="failed",
            )
            raise

    def _resize_image(self, img: Image.Image, params: ConversionParams) -> Image.Image:
        """Resize image according to parameters"""
        target_width = params.resize_width or img.width
        target_height = params.resize_height or img.height

        if params.maintain_aspect:
            img = ImageOps.contain(img, (target_width, target_height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        return img

    def _convert_color_mode(self, img: Image.Image, target_format: str) -> Image.Image:
        """Convert color mode based on target format"""
        if target_format.lower() in ("jpg", "jpeg") and img.mode in ("RGBA", "LA", "P"):
            # Convert to RGB for JPEG
            if img.mode == "P":
                img = img.convert("RGBA")

            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode in ("RGBA", "LA"):
                background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            else:
                background.paste(img)
            img = background

        return img

    def _save_image(self, img: Image.Image, target_path: Path, params: ConversionParams):
        """Save image with appropriate parameters"""
        target_path.parent.mkdir(parents=True, exist_ok=True)

        save_kwargs = {}

        if params.target_format.lower() in ("jpg", "jpeg"):
            save_kwargs["quality"] = params.quality
            save_kwargs["optimize"] = True
        elif params.target_format.lower() == "webp":
            save_kwargs["quality"] = params.quality
            save_kwargs["optimize"] = True
        elif params.target_format.lower() == "png":
            save_kwargs["optimize"] = True
        elif params.target_format.lower() == "ico":
            # Special handling for ICO format
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            available_sizes = [
                size for size in sizes if size[0] <= img.width and size[1] <= img.height
            ]
            if not available_sizes:
                available_sizes = [(16, 16)]  # Fallback
            save_kwargs["sizes"] = available_sizes

        img.save(target_path, format=params.target_format.upper(), **save_kwargs)
