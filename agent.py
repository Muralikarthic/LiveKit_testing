import os
import logging
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
            instructions="You are Amanda, a friendly and helpful voice AI assistant. Respond naturally and concisely."
        )

server = AgentServer()

@server.rtc_session(agent_name="amenda")
async def entrypoint(ctx: agents.JobContext):
    logger.info(f"Connecting Amanda to room: {ctx.room.name}")
    
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            voice="Aoede",
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
