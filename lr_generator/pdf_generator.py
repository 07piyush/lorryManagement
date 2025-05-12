"""PDF generator module for creating LR documents."""
from typing import Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, KeepTogether, PageBreak, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class PDFGenerator:
    def __init__(self, config: dict):
        self.config = config
        self.items_per_page = config['items_per_page']
        self.pdf_format = config['pdf_format']
        self.company_name = config.get('company_name', '')
        self.styles = getSampleStyleSheet()
        
        # Set up styles based on configuration
        self.brand_style = ParagraphStyle(
            'BrandStyle',
            parent=self.styles['Heading1'],
            fontName=self.pdf_format['fonts']['brand']['name'],
            fontSize=self.pdf_format['fonts']['brand']['size'],
            alignment=TA_CENTER,
            spaceAfter=15
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontName=self.pdf_format['fonts']['header']['name'],
            fontSize=self.pdf_format['fonts']['header']['size'],
            alignment=TA_LEFT,
            spaceAfter=10
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontName=self.pdf_format['fonts']['body']['name'],
            fontSize=self.pdf_format['fonts']['body']['size'],
            alignment=TA_LEFT
        )

    def create_lr_document(self, records: List[Dict], output_path: str):
        """Create a PDF document with multiple LRs per page."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=self.pdf_format['margins']['right']*inch,
            leftMargin=self.pdf_format['margins']['left']*inch,
            topMargin=self.pdf_format['margins']['top']*inch,
            bottomMargin=self.pdf_format['margins']['bottom']*inch
        )

        # Process records in groups based on items_per_page
        story = []
        for i in range(0, len(records), self.items_per_page):
            group = records[i:i + self.items_per_page]
            story.extend(self._create_lr_group(group))
            if i + self.items_per_page < len(records):
                story.append(PageBreak())

        doc.build(story)

    def _create_lr_group(self, records: List[Dict]) -> List:
        """Create a group of LRs for a single page."""
        elements = []
        
        for record in records:
            lr_elements = []
            
            # Add company branding at the top of each LR
            lr_elements.append(Paragraph(self.company_name, self.brand_style))
            lr_elements.append(Spacer(1, 0.1*inch))
            
            # Process each section according to configuration
            for section in self.pdf_format['sections']:
                if section['type'] != 'brand':  # Skip brand section as we handled it above
                    section_elements = self._create_section(section, record)
                    lr_elements.extend(section_elements)
                    lr_elements.append(Spacer(1, 0.1*inch))
            
            # Create a box around the entire LR
            box_data = [[lr_elements]]
            box_table = Table(box_data, colWidths=[7*inch])
            box_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            # Keep all elements of a single LR together
            elements.append(KeepTogether(box_table))
            elements.append(Spacer(1, 0.2*inch))

        return elements

    def _create_section(self, section: Dict, record: Dict) -> List:
        """Create a section of the LR based on configuration."""
        elements = []
        
        if section['type'] == 'header':
            # Create header table
            data = []
            row = []
            for field in section['fields']:
                value = record.get(field['name'], 'N/A')
                row.extend([Paragraph(field['label'], self.header_style),
                          Paragraph(str(value), self.body_style)])
            data.append(row)
            
            widths = [field['width']*0.5*inch for field in section['fields'] for _ in range(2)]
            table = Table(data, colWidths=widths)
            table.setStyle(self._get_table_style())
            elements.append(table)
            
        elif section['type'] in ['body', 'footer']:
            # Create body/footer table
            data = []
            for field in section['fields']:
                value = record.get(field['name'], 'N/A')
                data.append([Paragraph(field['label'], self.body_style),
                            Paragraph(str(value), self.body_style)])
            
            # Calculate widths based on the configuration
            total_width = sum(field['width'] for field in section['fields'])
            label_ratio = 0.3  # 30% for labels
            widths = [2*inch, 5*inch]
            
            table = Table(data, colWidths=widths)
            style = self._get_table_style()
            if section.get('box', False):
                style.add('BOX', (0, 0), (-1, -1), 1, colors.black)
            table.setStyle(style)
            elements.append(table)
        
        return elements

    def _get_table_style(self) -> TableStyle:
        """Get the common table style."""
        return TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.pdf_format['fonts']['body']['name']),
            ('FONTSIZE', (0, 0), (-1, -1), self.pdf_format['fonts']['body']['size']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ])
