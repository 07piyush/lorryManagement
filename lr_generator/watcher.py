"""File watcher module for monitoring Excel files."""
import time
import os
from pathlib import Path
from typing import List, Set, Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

class ExcelFileHandler(FileSystemEventHandler):
    def __init__(self, patterns: List[str], ignore_patterns: List[str], 
                 stabilization_seconds: int, process_callback: Callable[[Path], bool],
                 delete_after_processing: bool = True):
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns
        self.stabilization_seconds = stabilization_seconds
        self.process_callback = process_callback
        self.delete_after_processing = delete_after_processing
        self.processing_files: Set[Path] = set()
        self.seen_files: Set[Path] = set()

    def on_created(self, event):
        if not isinstance(event, FileCreatedEvent):
            return
        self._handle_file_event(event)

    def on_modified(self, event):
        if not isinstance(event, FileModifiedEvent):
            return
        self._handle_file_event(event)

    def _handle_file_event(self, event):
        file_path = Path(event.src_path)
        if not self._is_valid_file(file_path):
            return

        if file_path in self.processing_files:
            return

        self.processing_files.add(file_path)
        self._wait_for_file_stability(file_path)

    def _is_valid_file(self, file_path: Path) -> bool:
        if not file_path.is_file():
            return False

        if any(file_path.match(pattern) for pattern in self.ignore_patterns):
            return False

        return any(file_path.match(pattern) for pattern in self.patterns)

    def _wait_for_file_stability(self, file_path: Path):
        """Wait for file to stabilize (no size changes)."""
        last_size = -1
        current_size = file_path.stat().st_size

        while last_size != current_size:
            time.sleep(self.stabilization_seconds)
            last_size = current_size
            if file_path.exists():
                current_size = file_path.stat().st_size
            else:
                self.processing_files.remove(file_path)
                return

        if file_path not in self.seen_files:
            self.seen_files.add(file_path)
            try:
                # Process the file
                success = self.process_callback(file_path)
                
                # Delete file if processing was successful and deletion is enabled
                if success and self.delete_after_processing:
                    try:
                        os.remove(file_path)
                        print(f"Deleted processed file: {file_path}")
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {str(e)}")
                        
            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")

        self.processing_files.remove(file_path)

def start_watcher(watch_dir: str, patterns: List[str], ignore_patterns: List[str], 
                  process_callback: Callable[[Path], bool], stabilization_seconds: int = 5,
                  delete_after_processing: bool = True) -> Observer:
    """Start watching a directory for Excel files."""
    event_handler = ExcelFileHandler(
        patterns, 
        ignore_patterns, 
        stabilization_seconds,
        process_callback,
        delete_after_processing
    )
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()
    return observer
