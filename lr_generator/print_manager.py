"""Print management module."""
import os
import win32print
import win32api
import time
from pathlib import Path
from typing import Optional

class PrintManager:
    def __init__(self, printer_name: str, copies: int = 1, timeout_seconds: int = 30):
        self.printer_name = printer_name
        self.copies = copies
        self.timeout_seconds = timeout_seconds

    def print_pdf(self, pdf_path: Path) -> bool:
        """Print a PDF file. Returns True if successful, False otherwise."""
        try:
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            # If printer name is "Microsoft Print to PDF", just return success
            if self.printer_name.lower() == "microsoft print to pdf":
                return True

            # Get printer handle
            printer_handle = win32print.OpenPrinter(self.printer_name)
            
            try:
                # Print the file
                for _ in range(self.copies):
                    job_id = win32api.ShellExecute(
                        0,
                        "print",
                        str(pdf_path),
                        f'"{self.printer_name}"',
                        ".",
                        0
                    )
                    
                    # Wait for print job to complete or timeout
                    start_time = time.time()
                    while time.time() - start_time < self.timeout_seconds:
                        job_info = win32print.GetJob(printer_handle, job_id, 1)
                        if job_info['Status'] == win32print.JOB_STATUS_PRINTED:
                            break
                        time.sleep(1)
                    
                return True
            finally:
                win32print.ClosePrinter(printer_handle)
                
        except Exception as e:
            print(f"Print error: {str(e)}")
            return False

    @staticmethod
    def get_available_printers() -> list:
        """Get list of available printers."""
        printers = []
        for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL):
            printers.append(printer[2])
        return printers
