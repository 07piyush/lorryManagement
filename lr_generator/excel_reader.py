"""Excel file reader and preprocessor module."""
from typing import Dict, List, Generator, Iterator
import pandas as pd
from pathlib import Path

class ExcelReader:
    def __init__(self, required_fields: List[str], field_types: Dict[str, str], column_mapping: Dict[str, str]):
        self.required_fields = required_fields
        self.field_types = field_types
        self.column_mapping = column_mapping
        self.chunk_size = 1000  # Process 1000 rows at a time

    def read_excel(self, file_path: Path) -> Generator[Dict, None, None]:
        """Read and preprocess Excel file data in chunks."""
        try:
            # Get total number of rows for progress reporting
            with pd.ExcelFile(file_path, engine='openpyxl') as xls:
                total_rows = len(pd.read_excel(xls, nrows=0))
                print(f"Total rows to process: {total_rows}")

            # Process file in chunks
            chunk_iterator = pd.read_excel(
                file_path,
                engine='openpyxl',
                chunksize=self.chunk_size
            )

            processed_rows = 0
            for chunk in self._process_chunks(chunk_iterator):
                processed_rows += len(chunk)
                print(f"Processed {processed_rows}/{total_rows} rows")
                yield from chunk

        except Exception as e:
            raise Exception(f"Error processing Excel file: {str(e)}")

    def _process_chunks(self, chunk_iterator: Iterator[pd.DataFrame]) -> Generator[List[Dict], None, None]:
        """Process Excel chunks and yield records."""
        for chunk_df in chunk_iterator:
            # Apply column mapping
            df_mapped = pd.DataFrame()
            for excel_col, lr_field in self.column_mapping.items():
                if excel_col in chunk_df.columns:
                    df_mapped[lr_field] = chunk_df[excel_col]
                else:
                    raise ValueError(f"Required column not found in Excel: {excel_col}")

            # Apply type conversions
            for field, field_type in self.field_types.items():
                if field in df_mapped.columns:
                    if field_type == 'date':
                        df_mapped[field] = pd.to_datetime(df_mapped[field]).dt.date
                    elif field_type == 'float':
                        df_mapped[field] = pd.to_numeric(df_mapped[field], errors='coerce')
                    elif field_type == 'int':
                        df_mapped[field] = pd.to_numeric(df_mapped[field], errors='coerce').astype('Int64')

            # Convert chunk to list of dictionaries and yield
            yield df_mapped.to_dict('records')

    def validate_record(self, record: Dict) -> List[str]:
        """Validate a single record against rules."""
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in record or pd.isna(record[field]):
                errors.append(f"Missing required field: {field}")

        return errors
