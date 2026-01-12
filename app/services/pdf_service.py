"""
PDF generation service
"""
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from app.core.logging import get_logger


logger = get_logger(__name__)


def generate_pdf_from_text(text: str, title: str = "Document") -> BytesIO:
    """
    Generate a PDF from plain text with professional formatting
    
    Args:
        text: The text content to convert to PDF
        title: Title of the document
        
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceBefore=6,
        spaceAfter=6,
        alignment=TA_LEFT
    ))
    
    # Split text into lines and process
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            elements.append(Spacer(1, 0.1*inch))
            continue
        
        # Escape special characters for ReportLab
        line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Detect headers (all caps or specific patterns)
        if line.isupper() and len(line) < 50:
            # Header style
            p = Paragraph(f'<b>{line}</b>', styles['Heading2'])
        elif line.endswith(':') and len(line) < 50:
            # Sub-header style
            p = Paragraph(f'<b>{line}</b>', styles['Heading3'])
        else:
            # Normal text
            p = Paragraph(line, styles['CustomBody'])
        
        elements.append(p)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    logger.info(f"Generated PDF: {title}")
    return buffer

