"""Database management using SQLite"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from pydantic import BaseModel
from loguru import logger


class ConversionRecord(BaseModel):
    """Model for conversion history record"""

    id: Optional[int] = None
    source_path: str
    target_path: str
    source_format: str
    target_format: str
    source_size: int  # bytes
    target_size: int  # bytes
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime
    duration_ms: int
    status: str = "completed"  # completed, failed, cancelled


class DatabaseManager:
    """SQLite database manager"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Conversion history table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversion_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_path TEXT NOT NULL,
                        target_path TEXT NOT NULL,
                        source_format TEXT NOT NULL,
                        target_format TEXT NOT NULL,
                        source_size INTEGER NOT NULL,
                        target_size INTEGER NOT NULL,
                        width INTEGER,
                        height INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        duration_ms INTEGER NOT NULL,
                        status TEXT DEFAULT 'completed'
                    )
                """
                )

                # Settings table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_conversion_date ON conversion_history(created_at)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_conversion_format ON conversion_history(target_format)"
                )

                conn.commit()
                logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def add_conversion_record(self, record: ConversionRecord) -> int:
        """Add conversion record to history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO conversion_history 
                    (source_path, target_path, source_format, target_format, 
                     source_size, target_size, width, height, duration_ms, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        record.source_path,
                        record.target_path,
                        record.source_format,
                        record.target_format,
                        record.source_size,
                        record.target_size,
                        record.width,
                        record.height,
                        record.duration_ms,
                        record.status,
                    ),
                )
                conn.commit()
                record_id = cursor.lastrowid
                logger.debug(f"Added conversion record with ID {record_id}")
                return record_id
        except Exception as e:
            logger.error(f"Error adding conversion record: {e}")
            return 0

    def get_conversion_history(self, limit: int = 100) -> List[ConversionRecord]:
        """Get conversion history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM conversion_history 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """,
                    (limit,),
                )

                records = []
                for row in cursor.fetchall():
                    record = ConversionRecord(
                        id=row["id"],
                        source_path=row["source_path"],
                        target_path=row["target_path"],
                        source_format=row["source_format"],
                        target_format=row["target_format"],
                        source_size=row["source_size"],
                        target_size=row["target_size"],
                        width=row["width"],
                        height=row["height"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        duration_ms=row["duration_ms"],
                        status=row["status"],
                    )
                    records.append(record)

                return records
        except Exception as e:
            logger.error(f"Error getting conversion history: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Total conversions
                cursor.execute(
                    "SELECT COUNT(*) as total FROM conversion_history WHERE status = 'completed'"
                )
                total = cursor.fetchone()["total"]

                # By format
                cursor.execute(
                    """
                    SELECT target_format, COUNT(*) as count 
                    FROM conversion_history 
                    WHERE status = 'completed'
                    GROUP BY target_format
                """
                )
                by_format = {row["target_format"]: row["count"] for row in cursor.fetchall()}

                # Total size saved
                cursor.execute(
                    """
                    SELECT SUM(source_size - target_size) as saved 
                    FROM conversion_history 
                    WHERE status = 'completed' AND source_size > target_size
                """
                )
                size_saved = cursor.fetchone()["saved"] or 0

                return {
                    "total_conversions": total,
                    "by_format": by_format,
                    "size_saved_bytes": size_saved,
                }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"total_conversions": 0, "by_format": {}, "size_saved_bytes": 0}
