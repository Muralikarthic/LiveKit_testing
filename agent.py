import os
import logging
import asyncio
import urllib.parse
import aiohttp
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent
from livekit.plugins import google

load_dotenv(".env.local")
load_dotenv(".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("amenda-agent")

class Amanda(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are Amanda, a friendly and helpful voice AI assistant. "
                "Respond naturally, warmly, and concisely. "
                "If the user asks for weather information for any city or location, "
                "use the get_weather tool to retrieve current weather details before responding."
            )
        )

    @agents.function_tool(
        description="Get current weather information for a specified city or location."
    )
    async def get_weather(self, location: str) -> str:
        """Fetch current weather data for a location using Open-Meteo.

        Args:
            location: The name of the city or location (e.g., 'Kochi', 'London', 'Tokyo').
        """
        logger.info(f"get_weather tool called for location: {location}")
        if not location or not location.strip():
            return "Please provide a valid location name to check the weather."

        loc_clean = location.strip()
        encoded_loc = urllib.parse.quote(loc_clean)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_loc}&count=10&language=en&format=json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(geo_url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                    if response.status != 200:
                        logger.error(f"Geocoding API returned status code {response.status} for location '{loc_clean}'")
                        return f"Unable to locate '{loc_clean}' due to a weather service error."

                    geo_data = await response.json()
                    raw_results = geo_data.get("results", [])
                    if not raw_results:
                        logger.info(f"No geocoding results found for '{loc_clean}'")
                        return f"Could not find any location matching '{loc_clean}'. Please verify the location name."

                    # Deduplicate candidates by canonical (name, admin1, country)
                    seen_keys = set()
                    candidates = []
                    for r in raw_results:
                        name = (r.get("name") or "").strip()
                        admin1 = (r.get("admin1") or "").strip()
                        country = (r.get("country") or "").strip()
                        key = (name.lower(), admin1.lower(), country.lower())
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)

                        loc_parts = [name]
                        if admin1 and admin1.lower() != name.lower():
                            loc_parts.append(admin1)
                        if country:
                            loc_parts.append(country)
                        display_name = ", ".join(loc_parts)

                        candidates.append({
                            "name": name,
                            "admin1": admin1,
                            "country": country,
                            "latitude": r.get("latitude"),
                            "longitude": r.get("longitude"),
                            "population": r.get("population") or 0,
                            "display": display_name,
                        })

                    # Step 1: Check if user input contains explicit qualifiers (e.g., "Kochi, India", "Kochi, Japan")
                    query_parts = [p.strip().lower() for p in loc_clean.split(",") if p.strip()]
                    selected_candidate = None

                    if len(query_parts) > 1:
                        qualifiers = query_parts[1:]
                        matching_candidates = []
                        for c in candidates:
                            c_text = f"{c['admin1']} {c['country']} {c['display']}".lower()
                            if all(q in c_text for q in qualifiers):
                                matching_candidates.append(c)
                        if matching_candidates:
                            selected_candidate = matching_candidates[0]

                    # Step 2: If not explicitly qualified, check for dynamic ambiguity among distinct primary candidates
                    if not selected_candidate:
                        c1 = candidates[0]
                        c1_name = c1["name"].lower()
                        c1_pop = c1["population"]

                        ambiguous_candidates = [c1]
                        for c in candidates[1:5]:
                            c_name = c["name"].lower()
                            c_pop = c["population"]
                            if c_name == c1_name or c_name == query_parts[0]:
                                if c["country"] != c1["country"] or c["admin1"] != c1["admin1"]:
                                    if c_pop >= 50000 or (c1_pop > 0 and c_pop >= 0.1 * c1_pop) or (c1_pop == 0 and c_pop == 0):
                                        ambiguous_candidates.append(c)

                        if len(ambiguous_candidates) > 1:
                            options_str = "; ".join([f"{i+1}. {c['display']}" for i, c in enumerate(ambiguous_candidates[:3])])
                            return (
                                f"Multiple matching locations found for '{loc_clean}': {options_str}. "
                                f"Please ask the user to specify which location they meant."
                            )
                        selected_candidate = c1

                    display_location = selected_candidate["display"]
                    lat = selected_candidate["latitude"]
                    lon = selected_candidate["longitude"]

                forecast_url = (
                    f"https://api.open-meteo.com/v1/forecast?"
                    f"latitude={lat}&longitude={lon}&"
                    f"current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
                )

                async with session.get(forecast_url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                    if response.status != 200:
                        logger.error(f"Forecast API returned status code {response.status} for lat={lat}, lon={lon}")
                        return f"Unable to fetch weather data for '{display_location}' due to a weather service error."

                    weather_data = await response.json()
                    current = weather_data.get("current", {})

                    temp = current.get("temperature_2m")
                    feels_like = current.get("apparent_temperature")
                    humidity = current.get("relative_humidity_2m")
                    wind_speed = current.get("wind_speed_10m")
                    wmo_code = current.get("weather_code", 0)

                    return (
                        f"Location: {display_location} | WMO weather code: {wmo_code} | "
                        f"Temperature: {temp}°C | Feels Like: {feels_like}°C | "
                        f"Relative Humidity: {humidity}% | Wind Speed: {wind_speed} km/h"
                    )

        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching weather for '{loc_clean}'")
            return f"The weather service timed out while searching for '{loc_clean}'. Please try again."
        except aiohttp.ClientError as e:
            logger.error(f"Network error while fetching weather for '{loc_clean}': {e}")
            return f"Network error connecting to the weather service for '{loc_clean}'."
        except Exception as e:
            logger.error(f"Unexpected error in get_weather for '{loc_clean}': {e}", exc_info=True)
            return f"An unexpected error occurred while retrieving weather for '{loc_clean}'."

server = AgentServer()

@server.rtc_session(agent_name="amenda")
async def entrypoint(ctx: agents.JobContext):
    logger.info(f"Connecting Amanda to room: {ctx.room.name}")

    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            voice="Aoede",
            temperature=0.5
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Amanda(),
    )

    await session.generate_reply(
        instructions="Greet the user as Amanda."
    )

if __name__ == "__main__":
    agents.cli.run_app(server)

