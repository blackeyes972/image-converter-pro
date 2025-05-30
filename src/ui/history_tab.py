"""History tab for viewing conversion history"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QGroupBox,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime
from loguru import logger

from ..core.database import DatabaseManager
from ..utils.formatters import format_file_size, format_duration


class HistoryTab(QWidget):
    """Conversion history tab"""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        self._create_ui()
        self._load_history()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._load_history)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def _create_ui(self):
        """Create the history UI"""
        layout = QVBoxLayout(self)

        # Statistics group
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)

        self.total_label = QLabel("Total: 0")
        self.size_saved_label = QLabel("Size Saved: 0 MB")

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.size_saved_label)
        stats_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_history)
        stats_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self._clear_history)
        stats_layout.addWidget(clear_btn)

        layout.addWidget(stats_group)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels(
            ["Date", "Source", "Target", "Format", "Size", "Saved", "Duration", "Status"]
        )

        # Configure table
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Source path
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Target path

        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSortingEnabled(True)

        layout.addWidget(self.history_table)

    def _load_history(self):
        """Load conversion history from database"""
        try:
            records = self.db_manager.get_conversion_history(500)  # Last 500 records
            stats = self.db_manager.get_statistics()

            # Update statistics
            self.total_label.setText(f"Total: {stats['total_conversions']}")
            size_saved_mb = stats["size_saved_bytes"] / (1024 * 1024)
            self.size_saved_label.setText(f"Size Saved: {size_saved_mb:.1f} MB")

            # Update table
            self.history_table.setRowCount(len(records))

            for row, record in enumerate(records):
                # Date
                date_item = QTableWidgetItem(record.created_at.strftime("%Y-%m-%d %H:%M"))
                self.history_table.setItem(row, 0, date_item)

                # Source path (filename only)
                source_item = QTableWidgetItem(record.source_path.split("/")[-1])
                self.history_table.setItem(row, 1, source_item)

                # Target path (filename only)
                target_item = QTableWidgetItem(record.target_path.split("/")[-1])
                self.history_table.setItem(row, 2, target_item)

                # Format conversion
                format_item = QTableWidgetItem(f"{record.source_format} → {record.target_format}")
                self.history_table.setItem(row, 3, format_item)

                # File sizes
                size_item = QTableWidgetItem(format_file_size(record.target_size))
                self.history_table.setItem(row, 4, size_item)

                # Size saved/increased
                size_diff = record.source_size - record.target_size
                saved_item = QTableWidgetItem(
                    f"{'+' if size_diff > 0 else ''}{format_file_size(abs(size_diff))}"
                )
                if size_diff > 0:
                    saved_item.setForeground(Qt.GlobalColor.green)
                elif size_diff < 0:
                    saved_item.setForeground(Qt.GlobalColor.red)
                self.history_table.setItem(row, 5, saved_item)

                # Duration
                duration_item = QTableWidgetItem(format_duration(record.duration_ms))
                self.history_table.setItem(row, 6, duration_item)

                # Status
                status_item = QTableWidgetItem(record.status.title())
                if record.status == "completed":
                    status_item.setForeground(Qt.GlobalColor.green)
                elif record.status == "failed":
                    status_item.setForeground(Qt.GlobalColor.red)
                self.history_table.setItem(row, 7, status_item)

            # Sort by date (newest first)
            self.history_table.sortItems(0, Qt.SortOrder.DescendingOrder)

        except Exception as e:
            logger.error(f"Error loading history: {e}")

    def _clear_history(self):
        """Clear conversion history"""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all conversion history?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Clear database
                with self.db_manager.get_connection() as conn:
                    conn.execute("DELETE FROM conversion_history")
                    conn.commit()

                # Refresh display
                self._load_history()
                logger.info("Conversion history cleared")

            except Exception as e:
                logger.error(f"Error clearing history: {e}")
                QMessageBox.critical(self, "Error", f"Failed to clear history: {e}")
