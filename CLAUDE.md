# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Resume Generator application built as an MCP (Model Control Protocol) server using FastMCP. The project provides resume management functionality alongside weather service features (alerts and forecasts via the National Weather Service API).

## Development Environment

### Dependencies
- Python 3.11+
- httpx (for HTTP requests)
- mcp[cli] (for MCP server implementation)
- pdflatex (for generating PDF files from LaTeX)
- LaTeX packages (required for resume compilation):
  - fullpage (part of preprint package)
  - titlesec
  - lato
  - fontaxes
  - marvosym
  - enumitem
  - fancyhdr
  - fontawesome5
  - tabularx (part of tools package)
  - babel-english
  - multirow
  - xcolor

### Running the Server
To run the MCP server:
```bash
python resumeGenerator.py
```

The server runs using the stdio transport method.

### Installing Dependencies
To install the required Python dependencies:
```bash
pip install -e .
# or
pip install httpx mcp[cli]
```

To install the required LaTeX packages (using TinyTeX through R):
```bash
# If using TinyTeX with R
Rscript -e 'tinytex::tlmgr_install(c("preprint", "titlesec", "lato", "fontaxes", "marvosym", "enumitem", "fancyhdr", "fontawesome5", "tools", "babel-english", "multirow", "xcolor"))'

# If using TeX Live directly
tlmgr install preprint titlesec lato fontaxes marvosym enumitem fancyhdr fontawesome5 babel-english multirow xcolor
```

## Code Structure

- `resumeGenerator.py` - Main MCP server implementation with:
  - Resume management tools:
    - `get_resume(name)` - Get content of a resume file by name
    - `list_resumes()` - List all available resume files
    - `write_resume(name, content, overwrite=True)` - Write or update a resume file
    - `generate_pdf(tex_path)` - Generate a PDF from a LaTeX file (internal helper function)
  - Weather API tools (mentioned in CLAUDE.md but not implemented in current code):
    - `get_alerts(state)` - Fetch weather alerts for a US state
    - `get_forecast(latitude, longitude)` - Get weather forecast for coordinates
  
- `main.py` - Simple entry point for the application
- `resumes/` - Directory containing resume files in LaTeX format, organized in subdirectories by name (e.g., `Firstname_Lastname_Resume/`)
- `pyproject.toml` - Project configuration and dependencies

## File Organization

Resumes are stored in a specific structure:
```
resumes/
  |-- Firstname_Lastname_Resume/
      |-- Firstname_Lastname_Resume.tex (or other naming variations)
      |-- Firstname_Lastname_Resume.pdf (generated from .tex file)
```

## MCP Tools

The application exposes the following MCP tools:

1. `get_resume(name)` - Retrieves the content of a resume file by name (Firstname_Lastname format)
2. `list_resumes()` - Lists all available resume files in the resumes directory
3. `write_resume(name, content, overwrite=True)` - Writes or updates a resume file and generates a PDF
4. `get_alerts(state)` - Retrieves weather alerts for a specified US state (two-letter code) - mentioned but not implemented
5. `get_forecast(latitude, longitude)` - Gets a weather forecast for specific latitude and longitude coordinates - mentioned but not implemented

## LaTeX Resume Generation

The application can:
1. Write LaTeX resume content to files
2. Generate PDFs from LaTeX files using pdflatex
3. On macOS, automatically open generated PDFs

## Common Tasks

### Managing Resume Files
- To list available resumes: Use the `list_resumes()` MCP tool
- To retrieve a resume's LaTeX content: Use the `get_resume(name)` MCP tool
- To create or update a resume: Use the `write_resume(name, content, overwrite=True)` MCP tool

### Development Tasks
- To test the MCP server: Run `python resumeGenerator.py` and interact with it using an MCP client
- To check PDF generation: Create or update a resume file and verify the PDF output

## API Dependencies

The application is designed to interact with the National Weather Service API (https://api.weather.gov), though these features are not currently implemented in the code.