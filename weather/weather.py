# ------------------------------------------------ Importing packages and setting up the instance ------------------------------------------------

from typing import Any # Python module that allows developers to specify the types of inputs to make sure the input types are correct.
# httpx is a modern, fast, and fully featured HTTP client for Python. It provides a more powerful alternative to the standard requests
import httpx # HTTPX is a fully featured HTTP client for Python 3, which provides sync and async APIs, and support for both HTTP/1.1 and HTTP/2.
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0" 


# ------------------------------------------------ Helper functions ------------------------------------------------

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT, # Identifies your client (e.g., browser, bot, app).
        "Accept": "application/geo+json" # Tells the server what type of content you expect back.
    }
    async with httpx.AsyncClient() as client:
        try:
            # timeout = If the server doesn’t respond within 30 seconds, the request is cancelled and an exception is raised.
            # headers = Metadata sent with request (like User-Agent, Accept)
            response = await client.get(url, headers=headers, timeout=30.0 ) 
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    
    # .get(key, default)
    # ----------- key: the key you want to look up.
    # ----------- default: value to return in key doesnt exist.
    return f"""
                Event: {props.get('event', 'Unknown')}
                Area: {props.get('areaDesc', 'Unknown')}
                Severity: {props.get('severity', 'Unknown')}
                Description: {props.get('description', 'No description available')}
                Instructions: {props.get('instruction', 'No specific instructions provided')}
            """


# ------------------------------------------------ Implementing tool execution ------------------------------------------------

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