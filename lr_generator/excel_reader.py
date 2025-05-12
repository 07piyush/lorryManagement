"""Excel file reader and preprocessor module."""
from typing import Dict, List
import pandas as pd
from pathlib import Path

class ExcelReader:
    def __init__(self, required_fields: List[str], field_types: Dict[str, str], column_mapping: Dict[str, str]):
        self.required_fields = required_fields
        self.field_types = field_types
        self.column_mapping = column_mapping

    def read_excel(self, file_path: Path) -> List[Dict]:
        """Read and preprocess Excel file data."""
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Apply column mapping
            df_mapped = pd.DataFrame()
            for excel_col, lr_field in self.column_mapping.items():
                if excel_col in df.columns:
                    df_mapped[lr_field] = df[excel_col]
                else:
                    raise ValueError(f"Required column not found in Excel: {excel_col}")
            
            # Validate required fields
            missing_fields = [field for field in self.required_fields if field not in df_mapped.columns]
            if missing_fields:
                raise ValueError(f"Missing required fields after mapping: {missing_fields}")

            # Apply type conversions
            for field, field_type in self.field_types.items():
                if field in df_mapped.columns:
                    if field_type == 'date':
                        df_mapped[field] = pd.to_datetime(df_mapped[field]).dt.date
                    elif field_type == 'float':
                        df_mapped[field] = pd.to_numeric(df_mapped[field], errors='coerce')
                    elif field_type == 'int':
                        df_mapped[field] = pd.to_numeric(df_mapped[field], errors='coerce').astype('Int64')

            # Convert to list of dictionaries
            records = df_mapped.to_dict('records')
            
            return records
        except Exception as e:
            raise Exception(f"Error processing Excel file: {str(e)}")

    def validate_record(self, record: Dict) -> List[str]:
        """Validate a single record against rules."""
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in record or pd.isna(record[field]):
                errors.append(f"Missing required field: {field}")

        return errors
