"""Monitoring and checkpoint management module."""
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Any
import structlog
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

class ProcessingCheckpoint:
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_file = checkpoint_dir / "checkpoint.json"
        os.makedirs(checkpoint_dir, exist_ok=True)

    def save_progress(self, file: str, last_row: int, metadata: Optional[Dict] = None):
        """Save processing progress to checkpoint file."""
        checkpoint_data = {
            'file': file,
            'last_row': last_row,
            'timestamp': time.time(),
            'metadata': metadata or {}
        }
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f)
        
        logger.info(
            "checkpoint_saved",
            file=file,
            last_row=last_row,
            **checkpoint_data.get('metadata', {})
        )

    def load_progress(self) -> Optional[Dict[str, Any]]:
        """Load progress from checkpoint file if it exists."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file) as f:
                data = json.load(f)
                logger.info("checkpoint_loaded", **data)
                return data
        return None

    def clear_checkpoint(self):
        """Clear the checkpoint file."""
        if self.checkpoint_file.exists():
            os.remove(self.checkpoint_file)
            logger.info("checkpoint_cleared")

class ProcessingMonitor:
    def __init__(self):
        self.start_time = None
        self.logger = structlog.get_logger()

    def start_processing(self, file_path: str, total_rows: int):
        """Start monitoring file processing."""
        self.start_time = time.time()
        self.logger.info(
            "processing_started",
            file=file_path,
            total_rows=total_rows
        )
        return Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn()
        )

    def log_chunk_processed(self, chunk_size: int, valid_records: int, error_count: int):
        """Log chunk processing statistics."""
        self.logger.info(
            "chunk_processed",
            chunk_size=chunk_size,
            valid_records=valid_records,
            error_count=error_count
        )

    def end_processing(self, total_processed: int, total_valid: int, total_errors: int):
        """Log end of processing with statistics."""
        duration = time.time() - self.start_time
        self.logger.info(
            "processing_completed",
            duration_seconds=duration,
            total_processed=total_processed,
            total_valid=total_valid,
            total_errors=total_errors,
            records_per_second=total_processed / duration if duration > 0 else 0
        )

def get_progress_bar(total: int, description: str) -> Progress:
    """Create a rich progress bar."""
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn()
    )
