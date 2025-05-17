from typing import Any
import httpx
import os
import pathlib
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("resume-generator")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"
    
async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


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


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')