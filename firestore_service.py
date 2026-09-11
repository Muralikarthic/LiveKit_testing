import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("amenda-agent.firestore")

try:
    from google.cloud.firestore import AsyncClient, SERVER_TIMESTAMP
    HAS_FIRESTORE_SDK = True
except ImportError:
    HAS_FIRESTORE_SDK = False
    AsyncClient = None
    SERVER_TIMESTAMP = None


class FirestoreService:
    """Asynchronous, non-blocking Firestore persistence layer for Amanda.
    
    If Firestore credentials or project ID are missing, or if network writes fail,
    the service gracefully degrades without interrupting the voice session.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        collection_name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.project_id = project_id or os.getenv("FIRESTORE_PROJECT_ID")
        self.collection_name = (
            collection_name
            or os.getenv("FIRESTORE_COLLECTION_NAME")
            or "conversations"
        )
        
        # Explicit override or check SDK availability
        if enabled is False:
            self.is_enabled = False
        elif not HAS_FIRESTORE_SDK:
            logger.warning("google-cloud-firestore SDK is not installed. Firestore persistence disabled.")
            self.is_enabled = False
        else:
            self.is_enabled = True

        self._db: Optional[AsyncClient] = None
        self._initialized = False

    async def _get_db(self) -> Optional[AsyncClient]:
        if not self.is_enabled:
            return None

        if self._initialized:
            return self._db

        try:
            # Create AsyncClient using Application Default Credentials (ADC) or env vars
            if self.project_id:
                self._db = AsyncClient(project=self.project_id)
            else:
                self._db = AsyncClient()
            self._initialized = True
            logger.info(f"Firestore AsyncClient initialized for collection '{self.collection_name}'.")
            return self._db
        except Exception as e:
            logger.warning(f"Failed to initialize Firestore AsyncClient: {e}. Persistence disabled.")
            self.is_enabled = False
            self._initialized = True
            return None

    async def save_message(
        self,
        session_id: str,
        message_id: str,
        role: str,
        text: str,
        created_at_epoch: Optional[float] = None,
    ) -> None:
        """Persist a message asynchronously to Firestore without blocking the caller."""
        if not self.is_enabled or not session_id or not text:
            return

        try:
            db = await self._get_db()
            if not db or not self.is_enabled:
                return

            # Session document reference
            session_ref = db.collection(self.collection_name).document(session_id)
            
            # Upsert session document metadata asynchronously
            session_data = {
                "session_id": session_id,
                "last_updated_at": SERVER_TIMESTAMP if SERVER_TIMESTAMP else datetime.now(timezone.utc),
            }
            
            # Subcollection message document reference
            message_ref = session_ref.collection("messages").document(message_id)
            message_data = {
                "message_id": message_id,
                "role": role,
                "text": text,
                "timestamp": SERVER_TIMESTAMP if SERVER_TIMESTAMP else datetime.now(timezone.utc),
                "created_at_epoch": created_at_epoch or datetime.now(timezone.utc).timestamp(),
            }

            # Batch or gather async operations safely
            await session_ref.set(session_data, merge=True)
            await message_ref.set(message_data, merge=True)
            logger.info(f"Persisted message '{message_id}' (role={role}) for session '{session_id}'.")

        except Exception as e:
            logger.error(f"Firestore error while persisting message '{message_id}' for session '{session_id}': {e}")
            # Fault tolerance: swallow error so voice agent never crashes or blocks

    async def close(self) -> None:
        """Close the AsyncClient connection if active."""
        if self._db:
            try:
                await self._db.close()
            except Exception as e:
                logger.debug(f"Error closing Firestore AsyncClient: {e}")
            self._db = None
