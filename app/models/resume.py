"""
Resume data models for structured resume handling
"""
from pydantic import BaseModel
from typing import List, Optional


class PersonalInfo(BaseModel):
    """Personal information section"""
    name: str
    portfolio: Optional[str] = None
    email: str
    phone: str
    linkedin: Optional[str] = None


class EmploymentRole(BaseModel):
    """A role within an employment period"""
    title: str
    bullets: List[str]


class Employment(BaseModel):
    """Employment entry"""
    company: str
    position: str
    duration: str
    technologies: Optional[str] = None
    roles: List[EmploymentRole]


class Project(BaseModel):
    """Project entry"""
    name: str
    url: Optional[str] = None
    bullets: List[str]


class Education(BaseModel):
    """Education entry"""
    degree: str
    institution: str
    duration: str
    cgpa: Optional[str] = None


class ResumeData(BaseModel):
    """Complete resume data structure"""
    personal: PersonalInfo
    summary: str
    employment: List[Employment]
    projects: List[Project]
    skills: str
    education: Education
