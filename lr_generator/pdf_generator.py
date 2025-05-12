"""PDF generator module for creating LR documents."""
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.units import inch

class PDFGenerator:
    def __init__(self, items_per_page: int = 3):
        self.items_per_page = items_per_page
        self.styles = getSampleStyleSheet()
        
        # Create custom style for headers
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=12,
            spaceAfter=10
        )

    def create_lr_document(self, records: List[Dict], output_path: str):
        """Create a PDF document with multiple LRs per page."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        # Process records in groups based on items_per_page
        story = []
        for i in range(0, len(records), self.items_per_page):
            group = records[i:i + self.items_per_page]
            story.extend(self._create_lr_group(group))

        doc.build(story)

    def _create_lr_group(self, records: List[Dict]) -> List:
        """Create a group of LRs for a single page."""
        elements = []
        
        for record in records:
            # Create header
            elements.append(Paragraph(f"LR No: {record.get('lr_id', 'N/A')}", self.header_style))
            
            # Create table data
            data = [
                ['Invoice No:', record.get('invoice_number', 'N/A')],
                ['Date:', record.get('date', 'N/A')],
                ['Consignor:', record.get('consignor_name', 'N/A')],
                ['Consignee:', record.get('consignee_name', 'N/A')],
                ['Weight:', f"{record.get('weight', 'N/A')} kg"],
                ['Packages:', str(record.get('packages', 'N/A'))],
                ['Destination:', record.get('destination', 'N/A')]
            ]

            # Create table
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(table)
            elements.append(Paragraph("<br/><br/>", self.styles['Normal']))

        return elements
