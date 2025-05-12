"""Excel file reader and preprocessor module."""
from typing import Dict, List, Generator, Iterator, Optional, Set
import pandas as pd
from pathlib import Path
import structlog

logger = structlog.get_logger()

class ExcelReader:
    def __init__(self, config: dict, chunk_size: int = 1000):
        """Initialize ExcelReader with configuration.

        Args:
            config (dict): Configuration dictionary containing validation rules
            chunk_size (int, optional): Size of chunks to process. Defaults to 1000.
        """
        self.column_mapping = config['column_mapping']
        self.field_types = config['field_types']
        self.required_fields = config['pdf_fields']
        self.chunk_size = chunk_size
        
        # Create reverse mapping for column name variations
        self.column_variations = {}
        for excel_col, db_field in self.column_mapping.items():
            normalized = self._normalize_column_name(excel_col)
            self.column_variations[normalized] = db_field

    def _normalize_column_name(self, column: str) -> str:
        """Normalize column name by removing spaces and converting to uppercase."""
        return column.strip().upper().replace(' ', '')

    def _validate_columns(self, df: pd.DataFrame) -> List[str]:
        """Validate that all required columns are present."""
        errors = []
        df_columns = {self._normalize_column_name(col) for col in df.columns}
        required_columns = {self._normalize_column_name(col) 
                          for col in self.column_mapping.keys() 
                          if self.column_mapping[col] in self.required_fields}
        
        missing_columns = required_columns - df_columns
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            logger.error(
                "missing_required_columns",
                missing=list(missing_columns)
            )
        return errors

    def get_total_rows(self, file_path: Path) -> int:
        """Get total number of rows in Excel file."""
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            return len(df)
        except Exception as e:
            logger.error(
                "error_counting_rows",
                error=str(e),
                file=str(file_path)
            )
            raise

    def read_excel(self, file_path: Path, start_row: int = 0) -> Generator[Dict, None, None]:
        """Read and preprocess Excel file data in chunks."""
        try:
            # Read the entire file first
            df = pd.read_excel(
                file_path,
                engine='openpyxl',
                skiprows=start_row
            )
            
            # Validate columns before processing
            column_errors = self._validate_columns(df)
            if column_errors:
                raise ValueError("\n".join(column_errors))
            
            # Create dynamic column mapping based on actual Excel columns
            actual_mapping = {}
            for col in df.columns:
                normalized = self._normalize_column_name(col)
                if normalized in self.column_variations:
                    actual_mapping[col] = self.column_variations[normalized]
            
            # Process in chunks
            total_rows = len(df)
            for i in range(0, total_rows, self.chunk_size):
                chunk = df.iloc[i:i + self.chunk_size]
                records = self._process_chunks([chunk], actual_mapping)
                for record in records:
                    errors = self.validate_record(record)
                    if not errors:
                        yield record
                    else:
                        logger.warning("Validation errors for record:", errors=errors)

        except Exception as e:
            logger.error(
                "error_reading_excel",
                error=str(e),
                file=str(file_path),
                start_row=start_row
            )
            raise

    def _process_chunks(self, chunk_iterator, column_mapping: Dict[str, str]) -> List[Dict]:
        """Process chunks of data and return list of records."""
        records = []
        for chunk in chunk_iterator:
            # Map columns to our field names using the dynamic mapping
            df_mapped = chunk.rename(columns=column_mapping)

            # Convert fields based on their types
            for field, field_type in self.field_types.items():
                if field not in df_mapped.columns:
                    # Skip optional fields
                    if field in self.required_fields:
                        logger.warning(
                            "missing_required_field",
                            field=field
                        )
                    continue

                try:
                    if field_type == 'date':
                        try:
                            df_mapped[field] = pd.to_datetime(df_mapped[field], format='%d-%B-%Y').dt.date
                        except:
                            df_mapped[field] = pd.to_datetime(df_mapped[field]).dt.date
                    elif field_type == 'time':
                        # Handle various time formats
                        df_mapped[field] = pd.to_datetime(df_mapped[field], format='mixed', errors='coerce').dt.time
                    elif field_type == 'int':
                        df_mapped[field] = pd.to_numeric(df_mapped[field], errors='coerce').fillna(0).astype(int)
                    elif field_type == 'float':
                        df_mapped[field] = pd.to_numeric(df_mapped[field], errors='coerce').fillna(0.0)
                    elif field_type == 'str':
                        df_mapped[field] = df_mapped[field].fillna('').astype(str).str.strip()
                except Exception as e:
                    logger.error(
                        "type_conversion_error",
                        field=field,
                        field_type=field_type,
                        error=str(e)
                    )
                    # Set default values for failed conversions
                    if field_type == 'date':
                        df_mapped[field] = None
                    elif field_type == 'time':
                        df_mapped[field] = None
                    elif field_type == 'int':
                        df_mapped[field] = 0
                    elif field_type == 'float':
                        df_mapped[field] = 0.0
                    elif field_type == 'str':
                        df_mapped[field] = ''

            # Convert to list of dicts, only including fields we care about
            available_fields = [f for f in self.field_types.keys() if f in df_mapped.columns]
            chunk_records = df_mapped[available_fields].to_dict('records')
            records.extend(chunk_records)

        return records

    def validate_record(self, record: Dict) -> List[str]:
        """Validate a single record.

        Args:
            record (Dict): Record to validate

        Returns:
            List[str]: List of validation error messages
        """
        errors = []
        # Check required fields
        for field in self.required_fields:
            if field not in record or pd.isna(record[field]):
                errors.append(f"Missing required field: {field}")
                logger.warning("validation_error", field=field, error="missing_or_null")

        return errors
