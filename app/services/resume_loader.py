"""
Resume data loader utility
Loads resume data from YAML file
"""
import yaml
from pathlib import Path
from app.models.resume import ResumeData
from app.core.logging import get_logger


logger = get_logger(__name__)

# Default path to resume template
DEFAULT_RESUME_PATH = Path(__file__).parent.parent.parent / "public" / "resume_template.yaml"


def load_resume_from_yaml(file_path: Path = None) -> ResumeData:
    """
    Load resume data from a YAML file
    
    Args:
        file_path: Path to YAML file, defaults to public/resume_template.yaml
        
    Returns:
        ResumeData object
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If YAML is invalid or doesn't match schema
    """
    path = file_path or DEFAULT_RESUME_PATH
    
    if not path.exists():
        raise FileNotFoundError(f"Resume template not found at: {path}")
    
    logger.info(f"Loading resume from: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if data is None:
        raise ValueError("Resume YAML file is empty or contains only comments")
    
    try:
        resume = ResumeData(**data)
        logger.info(f"Successfully loaded resume for: {resume.personal.name}")
        return resume
    except Exception as e:
        logger.error(f"Failed to parse resume YAML: {e}")
        raise ValueError(f"Invalid resume data structure: {e}")
