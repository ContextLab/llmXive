"""
Streaming Handoff Module for llmXive.

Allows US2/US3 to begin processing chunks as T013 writes them,
avoiding false serialization.
"""

import json
import os
import time
import fcntl
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional

@dataclass
class ChunkManifest:
    """Represents a single chunk in the manifest."""
    chunk_id: str
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    file_path: str
    status: str  # "writing", "ready", "processed"
    created_at: float

class HandoffManager:
    """
    Manages the handoff of data chunks between producers and consumers.
    """

    def __init__(self, manifest_path: str, lock_path: str):
        self.manifest_path = Path(manifest_path)
        self.lock_path = Path(lock_path)
        self.manifest_dir = self.manifest_path.parent
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize manifest file if not exists
        if not self.manifest_path.exists():
            self.manifest_path.write_text(json.dumps({"chunks": []}, indent=2))

    def _read_manifest(self) -> Dict[str, Any]:
        """Read the current manifest."""
        with open(self.manifest_path, 'r') as f:
            return json.load(f)

    def _write_manifest(self, data: Dict[str, Any]) -> None:
        """Write the manifest with file locking."""
        with open(self.manifest_path, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def write_chunk(self, chunk_id: str, start_frame: int, end_frame: int,
                    start_time: float, end_time: float, file_path: str) -> None:
        """
        Write a new chunk to the manifest.

        Args:
            chunk_id: Unique identifier for the chunk.
            start_frame: Starting frame index.
            end_frame: Ending frame index.
            start_time: Start timestamp.
            end_time: End timestamp.
            file_path: Path to the chunk file.
        """
        manifest = self._read_manifest()
        
        chunk = ChunkManifest(
            chunk_id=chunk_id,
            start_frame=start_frame,
            end_frame=end_frame,
            start_time=start_time,
            end_time=end_time,
            file_path=file_path,
            status="writing",
            created_at=time.time()
        )

        manifest["chunks"].append(asdict(chunk))
        self._write_manifest(manifest)

    def mark_chunk_ready(self, chunk_id: str) -> None:
        """
        Mark a chunk as ready for processing.

        Args:
            chunk_id: The chunk ID to mark.
        """
        manifest = self._read_manifest()
        for chunk in manifest["chunks"]:
            if chunk["chunk_id"] == chunk_id:
                chunk["status"] = "ready"
                break
        self._write_manifest(manifest)

    def get_all_chunks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all chunks, optionally filtered by status.

        Args:
            status: Optional status filter ("writing", "ready", "processed").

        Returns:
            List of chunk dictionaries.
        """
        manifest = self._read_manifest()
        chunks = manifest["chunks"]
        if status:
            chunks = [c for c in chunks if c["status"] == status]
        return chunks

    def get_new_chunks_since(self, timestamp: float) -> List[Dict[str, Any]]:
        """
        Get chunks created after a specific timestamp.

        Args:
            timestamp: The timestamp to compare against.

        Returns:
            List of new chunk dictionaries.
        """
        manifest = self._read_manifest()
        return [c for c in manifest["chunks"] if c["created_at"] > timestamp]

    def wait_for_next_chunk(self, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """
        Wait for the next ready chunk.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            The first ready chunk, or None if timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            chunks = self.get_all_chunks(status="ready")
            if chunks:
                return chunks[0]
            time.sleep(1.0)
        return None

def get_handoff_manager(manifest_path: str = "data/handoff_manifest.json") -> HandoffManager:
    """
    Get a HandoffManager instance.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        HandoffManager instance.
    """
    lock_path = str(Path(manifest_path).with_suffix(".lock"))
    return HandoffManager(manifest_path, lock_path)
