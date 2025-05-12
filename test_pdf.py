"""Test script to generate a sample PDF with the new format."""
import yaml
from datetime import date, time
from pathlib import Path
from lr_generator.pdf_generator import PDFGenerator

# Sample data
sample_records = [
    {
        "lr_id": "BLR2505230001",
        "receive_date": date(2023, 5, 25),
        "party_name": "ABC Enterprises Pvt Ltd",
        "location": "Mumbai, Maharashtra",
        "boxes": 15,
        "transporter": "Express Logistics",
        "remark": "Handle with care"
    },
    {
        "lr_id": "BLR2505230002",
        "receive_date": date(2023, 5, 25),
        "party_name": "XYZ Industries",
        "location": "Delhi, NCR",
        "boxes": 8,
        "transporter": "Speed Carriers",
        "remark": "Fragile items"
    },
    {
        "lr_id": "BLR2505230003",
        "receive_date": date(2023, 5, 25),
        "party_name": "PQR Trading Co",
        "location": "Bangalore, Karnataka",
        "boxes": 12,
        "transporter": "Safe Transit",
        "remark": "Urgent delivery"
    }
]

def main():
    # Load configuration
    with open('rules.yml', 'r') as f:
        config = yaml.safe_load(f)['lr_generation']
    
    # Create output directory if it doesn't exist
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Initialize PDF generator
    pdf_gen = PDFGenerator(config)
    
    # Generate sample PDF
    output_path = output_dir / 'sample_lr.pdf'
    pdf_gen.create_lr_document(sample_records, str(output_path))
    print(f"Generated sample PDF at: {output_path}")

if __name__ == '__main__':
    main()
