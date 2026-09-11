import logging
import sys
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp-server")

mcp = FastMCP("AmandaMCPServer")

@mcp.tool(
    description=(
        "Get the current date and time for a specified IANA timezone "
        "(e.g., 'Asia/Kolkata', 'Asia/Tokyo', 'Europe/London', 'America/New_York', 'UTC')."
    )
)
def get_current_time(timezone: str) -> str:
    """Get current date and time for a specified IANA timezone.

    Args:
        timezone: Standard IANA timezone identifier (e.g., 'Asia/Kolkata', 'Asia/Tokyo', 'Europe/London', 'America/New_York', 'UTC').
    """
    if not timezone or not timezone.strip():
        return (
            "Error: A valid IANA timezone identifier must be provided "
            "(e.g., 'Asia/Kolkata', 'Asia/Tokyo', 'Europe/London', 'America/New_York', 'UTC')."
        )

    tz_str = timezone.strip()

    if tz_str.upper() == "UTC":
        now = datetime.now(dt_timezone.utc)
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC+0000)")
        return f"Current time in UTC: {formatted_time}"

    try:
        tz = ZoneInfo(tz_str)
        now = datetime.now(tz)
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
        return f"Current time in {tz_str}: {formatted_time}"
    except ZoneInfoNotFoundError:
        return (
            f"Error: '{tz_str}' is not a valid IANA timezone identifier. "
            f"Please specify a valid timezone name such as 'Asia/Kolkata', 'Asia/Tokyo', 'Europe/London', 'America/New_York', or 'UTC'."
        )
    except Exception as e:
        return f"Error determining time for '{tz_str}': {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
