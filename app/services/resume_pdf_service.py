"""
Styled Resume PDF generation service
Generates professional PDFs matching the user's original resume styling
"""
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, 
    HRFlowable, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.models.resume import ResumeData
from app.core.logging import get_logger


logger = get_logger(__name__)

# Colors matching the original resume
LINK_COLOR = HexColor("#0000EE")  # Standard hyperlink blue
GRAY_COLOR = HexColor("#666666")  # For dates/durations
SECTION_LINE_COLOR = HexColor("#4A86E8")  # Blue section divider

# Font paths
from pathlib import Path
FONTS_DIR = Path(__file__).parent.parent.parent / "public" / "fonts"

# Flag to track if fonts are registered
_fonts_registered = False


def register_fonts():
    """Register custom fonts with ReportLab"""
    global _fonts_registered
    if _fonts_registered:
        return
    
    inter_font_path = FONTS_DIR / "inter-var-latin.ttf"
    
    if inter_font_path.exists():
        try:
            # Register Inter font (variable font as regular)
            pdfmetrics.registerFont(TTFont('Inter', str(inter_font_path)))
            # Use same file for bold (variable font should handle weight)
            pdfmetrics.registerFont(TTFont('Inter-Bold', str(inter_font_path)))
            logger.info("Successfully registered Inter font")
            _fonts_registered = True
        except Exception as e:
            logger.warning(f"Failed to register Inter font: {e}. Falling back to Helvetica.")
    else:
        logger.warning(f"Inter font not found at {inter_font_path}. Using Helvetica.")


def get_font_names():
    """Get the font names to use (Inter if available, else Helvetica)"""
    register_fonts()
    
    # Check if Inter was successfully registered
    try:
        pdfmetrics.getFont('Inter')
        return 'Inter', 'Inter-Bold'
    except KeyError:
        return 'Helvetica', 'Helvetica-Bold'


def get_styles():
    """Define all paragraph styles for the resume"""
    font_regular, font_bold = get_font_names()
    styles = {}
    
    # Name style - bold, larger
    styles['Name'] = ParagraphStyle(
        name='Name',
        fontName=font_bold,
        fontSize=14,
        leading=18,
        textColor=black,
        spaceAfter=2
    )
    
    # Contact info with links
    styles['Contact'] = ParagraphStyle(
        name='Contact',
        fontName=font_regular,
        fontSize=10,
        leading=14,
        textColor=black,
        spaceAfter=2
    )
    
    # Section headers (Employment History, Projects, Skills, Education)
    styles['SectionHeader'] = ParagraphStyle(
        name='SectionHeader',
        fontName=font_bold,
        fontSize=12,
        leading=16,
        textColor=black,
        alignment=TA_CENTER,
        spaceBefore=12,
        spaceAfter=4
    )
    
    # Subsection title (Company name, position)
    styles['SubsectionTitle'] = ParagraphStyle(
        name='SubsectionTitle',
        fontName=font_bold,
        fontSize=10,
        leading=14,
        textColor=black,
        spaceBefore=8,
        spaceAfter=2
    )
    
    # Duration/date style
    styles['Duration'] = ParagraphStyle(
        name='Duration',
        fontName=font_regular,
        fontSize=9,
        leading=12,
        textColor=GRAY_COLOR,
        spaceAfter=2
    )
    
    # Technologies style
    styles['Technologies'] = ParagraphStyle(
        name='Technologies',
        fontName=font_regular,
        fontSize=9,
        leading=12,
        textColor=GRAY_COLOR,
        spaceAfter=4
    )
    
    # Role title (As Full-Time Developer, As Intern)
    styles['RoleTitle'] = ParagraphStyle(
        name='RoleTitle',
        fontName=font_bold,
        fontSize=10,
        leading=13,
        textColor=black,
        spaceBefore=6,
        spaceAfter=2,
        leftIndent=10
    )
    
    # Bullet point text
    styles['Bullet'] = ParagraphStyle(
        name='Bullet',
        fontName=font_regular,
        fontSize=10,
        leading=13,
        textColor=black,
        leftIndent=30,
        bulletIndent=20,
        spaceAfter=2
    )
    
    # Summary text
    styles['Summary'] = ParagraphStyle(
        name='Summary',
        fontName=font_regular,
        fontSize=10,
        leading=14,
        textColor=black,
        spaceAfter=8
    )
    
    # Project title with link
    styles['ProjectTitle'] = ParagraphStyle(
        name='ProjectTitle',
        fontName=font_bold,
        fontSize=10,
        leading=14,
        textColor=black,
        spaceBefore=8,
        spaceAfter=2
    )
    
    # Skills text
    styles['Skills'] = ParagraphStyle(
        name='Skills',
        fontName=font_regular,
        fontSize=10,
        leading=14,
        textColor=black,
        spaceAfter=4
    )
    
    # Education text
    styles['Education'] = ParagraphStyle(
        name='Education',
        fontName=font_bold,
        fontSize=10,
        leading=14,
        textColor=black,
        spaceAfter=2
    )
    
    return styles


def create_link(text: str, url: str) -> str:
    """Create a clickable hyperlink in ReportLab format"""
    return f'<a href="{url}" color="#0000EE"><u>{text}</u></a>'


def add_section_header(elements: list, title: str, styles: dict):
    """Add a section header with blue underline"""
    elements.append(Paragraph(title, styles['SectionHeader']))
    elements.append(HRFlowable(
        width="100%",
        thickness=1,
        color=SECTION_LINE_COLOR,
        spaceBefore=0,
        spaceAfter=8
    ))


def build_personal_section(elements: list, personal, styles: dict):
    """Build the personal info / header section"""
    # Name
    elements.append(Paragraph(personal.name, styles['Name']))
    
    # Portfolio
    if personal.portfolio:
        portfolio_link = create_link(personal.portfolio, personal.portfolio)
        elements.append(Paragraph(f"<b>Portfolio:</b> {portfolio_link}", styles['Contact']))
    
    # Email
    email_link = create_link(personal.email, f"mailto:{personal.email}")
    elements.append(Paragraph(f"<b>Email:</b> {email_link}", styles['Contact']))
    
    # Phone
    elements.append(Paragraph(f"<b>Phone:</b> {personal.phone}", styles['Contact']))
    
    # LinkedIn
    if personal.linkedin:
        linkedin_link = create_link(personal.linkedin, personal.linkedin)
        elements.append(Paragraph(f"<b>LinkedIn:</b> {linkedin_link}", styles['Contact']))
    
    elements.append(Spacer(1, 8))


def build_summary_section(elements: list, summary: str, styles: dict):
    """Build the summary section"""
    elements.append(Paragraph(summary, styles['Summary']))


def build_employment_section(elements: list, employment_list: list, styles: dict):
    """Build the employment history section"""
    add_section_header(elements, "Employment History", styles)
    
    for emp in employment_list:
        # Company and position
        elements.append(Paragraph(f"{emp.position}, {emp.company}", styles['SubsectionTitle']))
        
        # Duration
        elements.append(Paragraph(f"Duration: {emp.duration}", styles['Duration']))
        
        # Technologies
        if emp.technologies:
            elements.append(Paragraph(
                f"Technologies Used: [{emp.technologies}]", 
                styles['Technologies']
            ))
        
        # Roles
        for role in emp.roles:
            # Role title (e.g., "As Full-Time Developer (June 2024 – Present):")
            elements.append(Paragraph(f"• {role.title}:", styles['RoleTitle']))
            
            # Bullets for this role
            for bullet in role.bullets:
                bullet_text = f"- {bullet}"
                elements.append(Paragraph(bullet_text, styles['Bullet']))


def build_projects_section(elements: list, projects_list: list, styles: dict):
    """Build the projects section"""
    add_section_header(elements, "Projects", styles)
    
    for project in projects_list:
        # Project name with optional link
        if project.url:
            project_link = create_link(project.url, project.url)
            title_text = f"{project.name} | {project_link}"
        else:
            title_text = project.name
        
        elements.append(Paragraph(title_text, styles['ProjectTitle']))
        
        # Bullets
        for bullet in project.bullets:
            bullet_text = f"- {bullet}"
            elements.append(Paragraph(bullet_text, styles['Bullet']))


def build_skills_section(elements: list, skills: str, styles: dict):
    """Build the skills section"""
    add_section_header(elements, "Skills", styles)
    elements.append(Paragraph(skills, styles['Skills']))


def build_education_section(elements: list, education, styles: dict):
    """Build the education section"""
    add_section_header(elements, "Education", styles)
    
    # Degree and institution
    elements.append(Paragraph(
        f"{education.degree}, {education.institution}",
        styles['Education']
    ))
    
    # Duration and CGPA
    duration_text = education.duration
    if education.cgpa:
        duration_text += f" | CGPA - {education.cgpa}"
    
    elements.append(Paragraph(duration_text, styles['Duration']))


def generate_styled_resume_pdf(resume_data: ResumeData) -> BytesIO:
    """
    Generate a professionally styled PDF from structured resume data
    
    Args:
        resume_data: Structured resume data
        
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.6*inch,
        leftMargin=0.6*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    elements = []
    styles = get_styles()
    
    # Build each section
    build_personal_section(elements, resume_data.personal, styles)
    build_summary_section(elements, resume_data.summary, styles)
    build_employment_section(elements, resume_data.employment, styles)
    build_projects_section(elements, resume_data.projects, styles)
    build_skills_section(elements, resume_data.skills, styles)
    build_education_section(elements, resume_data.education, styles)
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    
    logger.info(f"Generated styled resume PDF for: {resume_data.personal.name}")
    return buffer
