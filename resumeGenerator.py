from typing import Any
import httpx
import os
import pathlib
import subprocess
import platform
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("resume-generator")

def generate_pdf(tex_path: pathlib.Path) -> tuple[bool, str]:
    """
    Generate a PDF from a LaTeX file and open it on macOS.
    
    Args:
        tex_path: Path to the LaTeX file
        
    Returns:
        Tuple of (success, message)
    """
    if not tex_path.exists():
        return False, f"LaTeX file not found at {tex_path}"
    
    # Get the directory and filename
    tex_dir = tex_path.parent
    
    try:
        # Run pdflatex twice to ensure all references are resolved
        for i in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_path.name],
                cwd=tex_dir,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )
            
            # Check if there were fatal errors in the output
            if "Fatal error occurred" in result.stdout or "Fatal error occurred" in result.stderr:
                # Check if the log file exists to get more detailed error information
                log_path = tex_path.with_suffix(".log")
                error_msg = result.stderr
                if log_path.exists():
                    try:
                        with open(log_path, "r") as log_file:
                            log_content = log_file.read()
                            # Extract the error message - look for lines with "!" prefix
                            error_lines = [line for line in log_content.split('\n') if line.startswith('!')]
                            if error_lines:
                                error_msg = '\n'.join(error_lines)
                    except Exception:
                        pass  # If we can't read the log file, continue with the original error
                
                return False, f"Failed to generate PDF. Error: {error_msg}"
        
        # Check if the PDF was created
        pdf_path = tex_path.with_suffix(".pdf")
        if not pdf_path.exists():
            return False, f"Failed to generate PDF. Check {tex_path.with_suffix('.log')} for errors."
        
        # Open the PDF file on macOS
        if platform.system() == "Darwin":  # macOS
            try:
                subprocess.run(["open", pdf_path], check=False)
            except Exception as e:
                return True, f"PDF generated at {pdf_path}, but failed to open automatically: {str(e)}"
                
        return True, f"PDF generated successfully at {pdf_path}"
        
    except Exception as e:
        return False, f"Error generating PDF: {str(e)}"

@mcp.tool()
async def get_resume(name: str) -> str:
    """Get the content of a resume file.
    
    Args:
        name: Name of the person in Firstname_Lastname format (e.g. John_Doe)
    """
    # Ensure resumes directory exists
    resume_dir = pathlib.Path("resumes")
    if not resume_dir.exists():
        os.makedirs(resume_dir, exist_ok=True)
        return f"No resumes found. Created directory: {resume_dir}"
    
    # Check if there's a directory for this person
    person_dir = resume_dir / f"{name}_Resume"
    
    # Try different possible locations for the resume file
    possible_locations = [
        # Check in person-specific subdirectory with standard naming
        person_dir / f"{name}_Resume.tex",
        # Check in person-specific subdirectory with hyphenated naming
        person_dir / f"{name.replace('_', '-')}-Resume.tex",
        # Check in person-specific subdirectory with other variations
        person_dir / f"*resume*.tex",
        # Check directly in resumes directory
        resume_dir / f"{name}_Resume.tex",
        # Check for any tex file with the person's name in resumes directory
        resume_dir / f"*{name}*.tex"
    ]
    
    resume_path = None
    for pattern in possible_locations:
        if '*' in str(pattern):
            # Handle glob patterns
            matches = list(pattern.parent.glob(pattern.name))
            if matches:
                resume_path = matches[0]
                break
        elif pattern.exists():
            resume_path = pattern
            break
    
    if not resume_path:
        # List available resumes/directories
        available_dirs = [d.name.replace("_Resume", "") for d in resume_dir.glob("*_Resume") if d.is_dir()]
        if available_dirs:
            return f"Resume for '{name}' not found. Available resume directories: {', '.join(available_dirs)}"
        else:
            return "No resume directories found."
    
    # Read the resume file
    try:
        with open(resume_path, "r") as file:
            content = file.read()
        return content
    except Exception as e:
        return f"Error reading resume file: {str(e)}"


@mcp.tool()
async def list_resumes() -> str:
    """List all available resume files."""
    resume_dir = pathlib.Path("resumes")
    if not resume_dir.exists():
        os.makedirs(resume_dir, exist_ok=True)
        return "No resumes found. Created directory: resumes/"
    
    # Check for resume directories first
    resume_dirs = list(resume_dir.glob("*_Resume"))
    resume_list = []
    
    # Process each resume directory
    for directory in resume_dirs:
        if not directory.is_dir():
            continue
            
        person_name = directory.name.replace("_Resume", "")
        tex_files = list(directory.glob("*.tex"))
        
        if tex_files:
            for tex_file in tex_files:
                resume_list.append(f"{person_name} ({directory.name}/{tex_file.name})")
        else:
            resume_list.append(f"{person_name} (no .tex file found in directory)")
    
    # If no resume directories found, check for direct tex files
    if not resume_list:
        # Check for any .tex files directly in the resumes directory
        all_tex_files = list(resume_dir.glob("*.tex"))
        if all_tex_files:
            resume_list = [f"{f.stem} ({f.name})" for f in all_tex_files]
            return "Available resume files (not in standard format):\n" + "\n".join(resume_list)
        else:
            return "No resume files found in the resumes directory."
    
    return "Available resumes:\n" + "\n".join(resume_list)


@mcp.tool()
async def write_resume(name: str, content: str, overwrite: bool = True) -> str:
    """Write or replace content of a resume file.
    
    Args:
        name: Name of the person in Firstname_Lastname format (e.g. John_Doe)
        content: LaTeX content to write to the resume file
        overwrite: Whether to overwrite existing file (default: True)
    """
    # Validate input
    if not name or not content:
        return "Error: Name and content cannot be empty"
    
    # Check for invalid filesystem characters in name
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in name for char in invalid_chars):
        return f"Error: Name contains invalid characters. Avoid: {' '.join(invalid_chars)}"
    
    # Basic content validation - check if it looks like LaTeX
    if not content.strip() or '\\documentclass' not in content:
        return "Error: Content does not appear to be valid LaTeX (missing \\documentclass)"
    
    # Ensure resumes directory exists
    resume_dir = pathlib.Path("resumes")
    try:
        if not resume_dir.exists():
            os.makedirs(resume_dir, exist_ok=True)
    except PermissionError:
        return "Error: Permission denied when creating resumes directory"
    except Exception as e:
        return f"Error creating resumes directory: {str(e)}"
    
    # Create or ensure directory for this person exists
    person_dir = resume_dir / f"{name}_Resume"
    try:
        if not person_dir.exists():
            os.makedirs(person_dir, exist_ok=True)
    except PermissionError:
        return f"Error: Permission denied when creating directory for {name}"
    except Exception as e:
        return f"Error creating directory for {name}: {str(e)}"
    
    # Set the resume file path
    resume_path = person_dir / f"{name}_Resume.tex"
    
    # If the resume doesn't exist but we have other naming patterns, let's check those first
    if not resume_path.exists():
        # Check if there's an existing file with a different naming convention
        possible_locations = [
            # Check for hyphenated naming
            person_dir / f"{name.replace('_', '-')}-Resume.tex",
            # Check for other variations
            person_dir / f"*resume*.tex"
        ]
        
        for pattern in possible_locations:
            if '*' in str(pattern):
                # Handle glob patterns
                matches = list(pattern.parent.glob(pattern.name))
                if matches:
                    resume_path = matches[0]
                    break
            elif pattern.exists():
                resume_path = pattern
                break
    
    # Check if file exists and handle overwrite flag
    if resume_path.exists() and not overwrite:
        return f"File already exists at {resume_path} and overwrite is set to False"
    
    # Create backup if file exists
    if resume_path.exists():
        try:
            backup_path = resume_path.with_suffix(".tex.bak")
            import shutil
            shutil.copy2(resume_path, backup_path)
        except Exception as e:
            return f"Warning: Could not create backup before overwriting: {str(e)}"
    
    # Write the content to the file
    try:
        with open(resume_path, "w") as file:
            file.write(content)
            
        # Verify file was written successfully
        if not resume_path.exists() or resume_path.stat().st_size == 0:
            return f"Error: File appears to be empty or not written correctly at {resume_path}"
        
        # Generate PDF and open it
        pdf_success, pdf_message = generate_pdf(resume_path)
        
        if pdf_success:
            return f"Successfully wrote resume for {name} to {resume_path}. {pdf_message}"
        else:
            return f"Successfully wrote resume for {name} to {resume_path}, but PDF generation failed: {pdf_message}"
    except PermissionError:
        return f"Error: Permission denied when writing to {resume_path}"
    except IOError as e:
        return f"Error writing resume file (IO error): {str(e)}"
    except Exception as e:
        return f"Error writing resume file: {str(e)}"


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')