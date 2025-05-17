# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Resume Generator application built as an MCP (Model Control Protocol) server using FastMCP. The project provides resume management functionality alongside weather service features (alerts and forecasts via the National Weather Service API).

## Development Environment

### Dependencies
- Python 3.11+
- httpx (for HTTP requests)
- mcp[cli] (for MCP server implementation)

### Running the Server
To run the MCP server:
```bash
python resumeGenerator.py
```

The server runs using the stdio transport method.

## Code Structure

- `resumeGenerator.py` - Main MCP server implementation with:
  - Weather API tools:
    - `get_alerts(state)` - Fetch weather alerts for a US state
    - `get_forecast(latitude, longitude)` - Get weather forecast for coordinates
  - Resume management tools:
    - `get_resume(name)` - Get content of a resume file by name
    - `list_resumes()` - List all available resume files
  
- `main.py` - Simple entry point for the application
- `resumes/` - Directory containing resume files in LaTeX format

## MCP Tools

The application exposes the following MCP tools:

1. `get_alerts` - Retrieves weather alerts for a specified US state (two-letter code)
2. `get_forecast` - Gets a weather forecast for specific latitude and longitude coordinates
3. `get_resume` - Retrieves the content of a resume file by name (Firstname_Lastname format)
4. `list_resumes` - Lists all available resume files in the resumes directory

## API Dependencies

The application interacts with the National Weather Service API (https://api.weather.gov).