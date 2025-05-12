"""Command-line interface for the LR Generator."""
import click
import yaml
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from .watcher import start_watcher
from .excel_reader import ExcelReader
from .lr_generator import LRGenerator
from .pdf_generator import PDFGenerator
from .print_manager import PrintManager
from .db import Database
from typing import List, Dict

# Load environment variables
load_dotenv()

@click.group()
def cli():
    """LR Generator CLI tool."""
    pass

def load_config():
    """Load configuration from rules.yml."""
    config_path = Path(__file__).parent.parent / 'rules.yml'
    with open(config_path) as f:
        return yaml.safe_load(f)

def get_db_connection():
    """Get database connection from environment variables."""
    return Database(
        connection_params={
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'lr_generator'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        },
        table_name='lr_records'
    )

def process_file(file_path: Path, config: dict, output_dir: Path, branch_code: str = "") -> bool:
    """Process a single Excel file and return True if successful."""
    try:
        # Initialize components
        reader = ExcelReader(
            required_fields=config['validation_rules']['required_fields'],
            field_types=config['validation_rules']['field_types'],
            column_mapping=config['validation_rules']['column_mapping']
        )
        
        lr_gen = LRGenerator(
            id_pattern=config['lr_generation']['id_pattern'],
            branch_code=branch_code
        )
        
        pdf_gen = PDFGenerator(
            items_per_page=config['lr_generation']['items_per_page']
        )
        
        # Initialize database
        db = get_db_connection()
        db.create_tables()
        
        # Initialize print manager if enabled
        print_manager = None
        if config['print_settings']['enabled']:
            print_manager = PrintManager(
                printer_name=config['print_settings']['printer_name'],
                copies=config['print_settings']['copies'],
                timeout_seconds=config['print_settings']['timeout_seconds']
            )
        
        # Process Excel file in chunks
        valid_records = []
        batch_size = config['database']['batch_size']
        current_batch = []
        
        # Read and process Excel file in chunks
        for record in reader.read_excel(file_path):
            errors = reader.validate_record(record)
            if not errors:
                record['lr_id'] = lr_gen.generate_lr_id(record)
                current_batch.append(record)
                valid_records.append(record)
                
                # Process batch if it reaches the batch size
                if len(current_batch) >= batch_size:
                    _process_batch(current_batch, db, config)
                    current_batch = []
            else:
                click.echo(f"Validation errors for record: {errors}")
        
        # Process remaining records in the last batch
        if current_batch:
            _process_batch(current_batch, db, config)
        
        if not valid_records:
            click.echo("No valid records found")
            return False
        
        # Generate PDF in chunks of items_per_page
        items_per_page = config['lr_generation']['items_per_page']
        output_path = output_dir / f"lr_batch_{branch_code}_{len(valid_records)}.pdf"
        
        for i in range(0, len(valid_records), items_per_page * 10):  # Process 10 pages at a time
            batch_records = valid_records[i:i + items_per_page * 10]
            if i == 0:
                pdf_gen.create_lr_document(batch_records, str(output_path))
            else:
                pdf_gen.append_to_document(batch_records, str(output_path))
        
        click.echo(f"Generated PDF: {output_path}")
        
        # Try to print if enabled
        if print_manager:
            if print_manager.print_pdf(output_path):
                click.echo("PDF sent to printer")
            else:
                click.echo("Failed to print PDF")
        
        return True
        
    except Exception as e:
        click.echo(f"Error processing file: {str(e)}", err=True)
        return False
    finally:
        if 'db' in locals():
            db.close()

def _process_batch(batch: List[Dict], db: Database, config: dict):
    """Process a batch of records with retry logic."""
    max_attempts = config['database'].get('retry_attempts', 3)
    retry_delay = config['database'].get('retry_delay_seconds', 5)
    
    for attempt in range(max_attempts):
        try:
            db.insert_records(batch, config['database']['batch_size'])
            click.echo(f"Stored {len(batch)} records in database")
            break
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            click.echo(f"Database error (attempt {attempt + 1}): {str(e)}")
            time.sleep(retry_delay)

@cli.command()
@click.argument('watch_dir', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path(exists=True))
@click.option('--branch-code', default="", help="Branch code for LR ID generation")
def watch(watch_dir, output_dir, branch_code):
    """Start watching a directory for Excel files."""
    config = load_config()
    watch_settings = config['watch_settings']
    
    # Create process_callback
    def callback(file_path: Path) -> bool:
        return process_file(file_path, config, Path(output_dir), branch_code)
    
    click.echo(f"Starting watcher for directory: {watch_dir}")
    observer = start_watcher(
        watch_dir,
        patterns=watch_settings['patterns'],
        ignore_patterns=watch_settings['ignore_patterns'],
        process_callback=callback,
        stabilization_seconds=watch_settings['stabilization_seconds'],
        delete_after_processing=watch_settings['delete_after_processing']
    )
    
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path(exists=True))
@click.option('--branch-code', default="", help="Branch code for LR ID generation")
def process(input_file, output_dir, branch_code):
    """Process a single Excel file."""
    config = load_config()
    success = process_file(Path(input_file), config, Path(output_dir), branch_code)
    if not success:
        click.echo("Failed to process file")

if __name__ == '__main__':
    cli()
