# LR Generator

A CLI-based application for processing Excel sheets containing invoice data and generating Lorry Receipts (LR) in PDF format.

## Features

- Excel file monitoring and processing
- Data validation and preprocessing
- Unique LR ID generation
- PDF generation with 3 LRs per page
- PostgreSQL database storage
- Print management system

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file with your database configuration:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=lr_generator
   DB_USER=your_username
   DB_PASSWORD=your_password
   ```

2. Adjust `rules.yml` for validation rules and other settings.

## Usage

### Watch Directory for Excel Files

```bash
python -m lr_generator watch /path/to/watch/directory
```

### Process Single File

```bash
python -m lr_generator process input.xlsx /path/to/output/dir --branch-code BR01
```

## File Format Requirements

Excel files should contain the following columns:
- invoice_number
- date
- consignor_name
- consignee_name
- weight
- packages
- destination

## Development

### Project Structure

```
lr_generator/
├── lr_generator/
│   ├── __init__.py
│   ├── cli.py           # Command-line interface
│   ├── watcher.py       # File system monitoring
│   ├── excel_reader.py  # Excel processing
│   ├── lr_generator.py  # LR ID generation
│   ├── pdf_generator.py # PDF creation
│   └── db.py           # Database operations
├── requirements.txt
├── rules.yml           # Configuration
└── README.md
```

## License

MIT
