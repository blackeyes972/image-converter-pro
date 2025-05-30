# src/extensions/gif_processor.py
"""
GIF Processing Extension for Image Converter Pro
Extends existing functionality without modifying core code
"""

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable, Union
from PIL import Image, ImageSequence
from pydantic import BaseModel, Field, validator
from loguru import logger

from ..core.database import ConversionRecord
from ..core.image_processor import ImageProcessor, ConversionParams


class GifCreationParams(BaseModel):
    """Parameters for GIF creation from multiple images"""
    frame_duration: int = Field(default=500, ge=100, le=5000)  # milliseconds
    loop_count: int = Field(default=0)  # 0 = infinite loop
    optimize: bool = Field(default=True)
    quality: int = Field(default=85, ge=1, le=100)
    resize_width: Optional[int] = Field(default=None, ge=1, le=4096)
    resize_height: Optional[int] = Field(default=None, ge=1, le=4096)
    maintain_aspect: bool = Field(default=True)
    
    @validator('frame_duration')
    def validate_frame_duration(cls, v):
        if v < 100:
            logger.warning("Frame duration too low, setting to 100ms minimum")
            return 100
        return v


class GifOptimizationParams(BaseModel):
    """Parameters for GIF optimization"""
    reduce_colors: bool = Field(default=True)
    max_colors: int = Field(default=256, ge=2, le=256)
    dither: bool = Field(default=True)
    transparency: bool = Field(default=True)
    disposal_method: int = Field(default=2)  # 2 = restore background


class GifProcessor(ImageProcessor):
    """
    Extended processor for GIF operations
    Inherits from ImageProcessor without modifying base class
    """
    
    def __init__(self):
        super().__init__()
        # Extend supported formats
        self.supported_formats['input'].extend(['.gif'])
        self.supported_formats['output'].extend(['gif'])
        
        logger.info("GIF processor extension loaded")
    
    def create_gif_from_images(
        self,
        image_paths: List[Path],
        output_path: Path,
        params: GifCreationParams,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> ConversionRecord:
        """Create animated GIF from multiple images"""
        start_time = time.time()
        
        try:
            logger.info(f"Creating GIF from {len(image_paths)} images: {output_path}")
            
            if progress_callback:
                progress_callback(5)
            
            # Load and process all images
            frames = []
            total_source_size = 0
            
            for i, image_path in enumerate(image_paths):
                # Load image
                img = Image.open(image_path)
                total_source_size += image_path.stat().st_size
                
                # Resize if needed
                if params.resize_width or params.resize_height:
                    img = self._resize_gif_frame(img, params)
                
                # Convert to RGB if needed (GIF supports palette mode)
                if img.mode not in ('RGB', 'RGBA', 'P'):
                    img = img.convert('RGB')
                
                frames.append(img)
                
                # Update progress
                if progress_callback:
                    progress = 5 + int((i + 1) / len(image_paths) * 70)
                    progress_callback(progress)
            
            if progress_callback:
                progress_callback(80)
            
            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as animated GIF
            self._save_animated_gif(frames, output_path, params)
            
            if progress_callback:
                progress_callback(100)
            
            # Create conversion record
            duration_ms = int((time.time() - start_time) * 1000)
            target_size = output_path.stat().st_size
            
            # Use dimensions of first frame
            first_frame = frames[0] if frames else None
            width = first_frame.width if first_frame else None
            height = first_frame.height if first_frame else None
            
            record = ConversionRecord(
                source_path=f"Multiple images ({len(image_paths)} files)",
                target_path=str(output_path),
                source_format="multiple",
                target_format="gif",
                source_size=total_source_size,
                target_size=target_size,
                width=width,
                height=height,
                created_at=datetime.now(),
                duration_ms=duration_ms,
                status="completed"
            )
            
            logger.info(f"GIF created successfully in {duration_ms}ms")
            return record
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"GIF creation failed: {e}")
            
            record = ConversionRecord(
                source_path=f"Multiple images ({len(image_paths)} files)",
                target_path=str(output_path),
                source_format="multiple",
                target_format="gif",
                source_size=total_source_size if 'total_source_size' in locals() else 0,
                target_size=0,
                created_at=datetime.now(),
                duration_ms=duration_ms,
                status="failed"
            )
            raise
    
    def optimize_gif(
        self,
        source_path: Path,
        target_path: Path,
        params: GifOptimizationParams,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> ConversionRecord:
        """Optimize existing GIF file"""
        start_time = time.time()
        
        try:
            logger.info(f"Optimizing GIF: {source_path} -> {target_path}")
            
            if progress_callback:
                progress_callback(10)
            
            # Open GIF and extract frames
            with Image.open(source_path) as gif:
                frames = []
                durations = []
                
                for frame in ImageSequence.Iterator(gif):
                    # Get frame duration
                    duration = frame.info.get('duration', 100)
                    durations.append(duration)
                    
                    # Process frame
                    frame_copy = frame.copy()
                    
                    # Color reduction if requested
                    if params.reduce_colors and frame_copy.mode != 'P':
                        frame_copy = frame_copy.quantize(
                            colors=params.max_colors,
                            dither=Image.Dither.FLOYDSTEINBERG if params.dither else Image.Dither.NONE
                        )
                    
                    frames.append(frame_copy)
                
                if progress_callback:
                    progress_callback(70)
                
                # Save optimized GIF
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                frames[0].save(
                    target_path,
                    format='GIF',
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=0,
                    optimize=True,
                    transparency=255 if params.transparency else None,
                    disposal=params.disposal_method
                )
            
            if progress_callback:
                progress_callback(100)
            
            # Create record
            duration_ms = int((time.time() - start_time) * 1000)
            source_size = source_path.stat().st_size
            target_size = target_path.stat().st_size
            
            record = ConversionRecord(
                source_path=str(source_path),
                target_path=str(target_path),
                source_format="gif",
                target_format="gif",
                source_size=source_size,
                target_size=target_size,
                width=frames[0].width if frames else None,
                height=frames[0].height if frames else None,
                created_at=datetime.now(),
                duration_ms=duration_ms,
                status="completed"
            )
            
            compression_ratio = (1 - target_size / source_size) * 100
            logger.info(f"GIF optimized: {compression_ratio:.1f}% size reduction")
            return record
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"GIF optimization failed: {e}")
            raise
    
    def extract_gif_frames(
        self,
        gif_path: Path,
        output_dir: Path,
        frame_format: str = "png",
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[Path]:
        """Extract individual frames from GIF"""
        try:
            logger.info(f"Extracting frames from GIF: {gif_path}")
            
            output_dir.mkdir(parents=True, exist_ok=True)
            extracted_frames = []
            
            with Image.open(gif_path) as gif:
                total_frames = getattr(gif, 'n_frames', 1)
                
                for i, frame in enumerate(ImageSequence.Iterator(gif)):
                    frame_path = output_dir / f"frame_{i:04d}.{frame_format}"
                    
                    # Convert frame if needed
                    if frame_format.lower() in ('jpg', 'jpeg') and frame.mode in ('RGBA', 'P'):
                        # Create white background for JPEG
                        rgb_frame = Image.new('RGB', frame.size, (255, 255, 255))
                        if frame.mode == 'P':
                            frame = frame.convert('RGBA')
                        rgb_frame.paste(frame, mask=frame.split()[-1] if frame.mode == 'RGBA' else None)
                        frame = rgb_frame
                    
                    frame.save(frame_path)
                    extracted_frames.append(frame_path)
                    
                    if progress_callback:
                        progress = int((i + 1) / total_frames * 100)
                        progress_callback(progress)
            
            logger.info(f"Extracted {len(extracted_frames)} frames to {output_dir}")
            return extracted_frames
            
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            raise
    
    def _resize_gif_frame(self, img: Image.Image, params: GifCreationParams) -> Image.Image:
        """Resize frame for GIF creation"""
        target_width = params.resize_width or img.width
        target_height = params.resize_height or img.height
        
        if params.maintain_aspect:
            img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        return img
    
    def _save_animated_gif(
        self,
        frames: List[Image.Image],
        output_path: Path,
        params: GifCreationParams
    ):
        """Save frames as animated GIF"""
        if not frames:
            raise ValueError("No frames to save")
        
        # Optimize frames for GIF
        optimized_frames = []
        for frame in frames:
            # Convert to palette mode for smaller file size
            if frame.mode != 'P':
                frame = frame.quantize(colors=256, dither=Image.Dither.FLOYDSTEINBERG)
            optimized_frames.append(frame)
        
        # Save animated GIF
        optimized_frames[0].save(
            output_path,
            format='GIF',
            save_all=True,
            append_images=optimized_frames[1:],
            duration=params.frame_duration,
            loop=params.loop_count,
            optimize=params.optimize
        )


