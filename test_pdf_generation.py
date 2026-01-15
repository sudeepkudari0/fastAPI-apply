"""
Test script for styled resume PDF generation
Generates a PDF without calling the AI API - uses the resume data as-is
"""
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.resume_loader import load_resume_from_yaml
from app.services.resume_pdf_service import generate_styled_resume_pdf
from app.services.pdf_service import generate_pdf_from_text


def main():
    # Create output directory
    output_dir = Path(__file__).parent / "public" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 50)
    print("Resume PDF Generator Test")
    print("=" * 50)
    
    # Step 1: Load resume from YAML
    print("\n[1] Loading resume from YAML...")
    try:
        resume = load_resume_from_yaml()
        print(f"    ✓ Loaded resume for: {resume.personal.name}")
    except Exception as e:
        print(f"    ✗ Error loading resume: {e}")
        return
    
    # Step 2: Generate styled resume PDF
    print("\n[2] Generating styled resume PDF...")
    try:
        pdf_buffer = generate_styled_resume_pdf(resume)
        
        # Save to file
        resume_pdf_path = output_dir / "test_resume.pdf"
        with open(resume_pdf_path, "wb") as f:
            f.write(pdf_buffer.read())
        
        print(f"    ✓ Resume PDF saved to: {resume_pdf_path}")
    except Exception as e:
        print(f"    ✗ Error generating resume PDF: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Generate a mock cover letter PDF
    print("\n[3] Generating mock cover letter PDF...")
    mock_cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the Software Developer position at your company.

As a Full-Stack Software Developer with experience in Java, TypeScript, modern Web Frameworks, and Cloud Platforms, I am excited about the opportunity to contribute to your team. My background includes building end-to-end applications from Frontend UI to Backend services with Scalable Deployments on AWS.

At ThinkRoman Ventures, I have:
- Built and deployed scalable full-stack applications using Next.js, MongoDB, and Prisma ORM
- Designed modular SaaS architectures with multi-tenant and production-grade performance
- Integrated third-party APIs including WhatsApp, Zoom, and payment gateways
- Optimized performance across mobile and desktop platforms

My personal projects, including OutPost (an AI Social Scheduler) and Forms Factory (a Collaborative Form Builder), demonstrate my ability to architect and deliver complete SaaS products independently.

I would welcome the opportunity to discuss how my skills and experience align with your needs.

Thank you for your consideration.

Best regards,
{resume.personal.name}
Email: {resume.personal.email}
Phone: {resume.personal.phone}
"""
    
    try:
        cl_buffer = generate_pdf_from_text(mock_cover_letter, "Cover Letter")
        
        # Save to file
        cover_letter_path = output_dir / "test_cover_letter.pdf"
        with open(cover_letter_path, "wb") as f:
            f.write(cl_buffer.read())
        
        print(f"    ✓ Cover letter PDF saved to: {cover_letter_path}")
    except Exception as e:
        print(f"    ✗ Error generating cover letter PDF: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST COMPLETE!")
    print("=" * 50)
    print(f"\nGenerated files in: {output_dir}")
    print(f"  - test_resume.pdf")
    print(f"  - test_cover_letter.pdf")
    print("\nOpen these PDFs to verify the styling matches your original resume.")


if __name__ == "__main__":
    main()
