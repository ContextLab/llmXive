"""
Streaming Handoff Module for llmXive Data Pipeline.

Implements logic to allow downstream processes (US2/US3) to begin processing
video chunks as soon as they are written by the generator, avoiding false
serialization and enabling parallel processing.
"""
import json
import os
import time
import fcntl
import threading
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime

from src.utils.logging import get_logger
from src.utils.validation import validate_manifest_structure

logger = get_logger(__name__)


@dataclass
class ChunkManifest:
    """
    Represents the manifest of a single chunk written to disk.
    This structure is written to a JSON file alongside the chunk data.
    """
    chunk_id: str
    start_timestamp: float
    end_timestamp: float
    frame_count: int
    file_path: str
    status: str  # 'writing', 'ready', 'error'
    created_at: str
    hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkManifest':
        return cls(**data)


class HandoffManager:
    """
    Manages the handoff of data chunks from the generator (Producer)
    to downstream consumers (US2/US3).

    Features:
    - Atomic chunk marking: Uses a '.tmp' file + rename pattern to ensure
      consumers only see fully written chunks.
    - Locking: Uses file locking (fcntl) to prevent race conditions when
      updating the global manifest.
    - Streaming Polling: Provides a generator to wait for new chunks.
    """

    def __init__(self, output_dir: str, global_manifest_path: str = "manifest.jsonl"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.global_manifest_path = Path(self.output_dir) / global_manifest_path
        self.lock_file = Path(self.output_dir) / ".handoff.lock"
        self._lock = threading.Lock()  # In-memory lock for Python threads
        self.logger = get_logger(__name__)

    def _acquire_lock(self) -> bool:
        """Acquire an exclusive lock on the handoff lock file."""
        if not self.lock_file.exists():
            self.lock_file.touch()
        try:
            with open(self.lock_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
        except (IOError, OSError):
            return False

    def _release_lock(self):
        """Release the lock on the handoff lock file."""
        if self.lock_file.exists():
            try:
                with open(self.lock_file, 'w') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass

    def register_chunk_start(self, chunk_id: str, start_ts: float) -> ChunkManifest:
        """
        Registers a new chunk as 'writing'. Creates the manifest entry
        but marks it as not ready for consumption yet.
        """
        manifest = ChunkManifest(
            chunk_id=chunk_id,
            start_timestamp=start_ts,
            end_timestamp=0.0, # Will be updated
            frame_count=0,
            file_path=str(self.output_dir / f"{chunk_id}.jsonl"),
            status='writing',
            created_at=datetime.now().isoformat()
        )
        # Write initial state to a temporary file for atomicity later
        return manifest

    def finalize_chunk(self, manifest: ChunkManifest, end_ts: float, frame_count: int, file_hash: Optional[str] = None) -> ChunkManifest:
        """
        Finalizes a chunk, updates its metadata, and atomically moves
        the data file to signal readiness.
        """
        manifest.end_timestamp = end_ts
        manifest.frame_count = frame_count
        manifest.status = 'ready'
        if file_hash:
            manifest.hash = file_hash

        # Write the manifest to a .tmp file first
        manifest_path = Path(self.output_dir) / f"{manifest.chunk_id}_manifest.json"
        tmp_path = Path(str(manifest_path) + ".tmp")

        with open(tmp_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)

        # Atomic rename to signal readiness
        tmp_path.rename(manifest_path)

        self.logger.info(f"Chunk {manifest.chunk_id} finalized and ready for handoff.")
        return manifest

    def update_global_manifest(self, chunk_manifest: ChunkManifest):
        """
        Appends the chunk entry to the global manifest.jsonl file.
        Uses file locking to ensure thread safety.
        """
        entry = chunk_manifest.to_dict()
        entry['timestamp'] = datetime.now().isoformat()

        # Simple append with lock
        if self._acquire_lock():
            try:
                with open(self.global_manifest_path, 'a') as f:
                    f.write(json.dumps(entry) + '\n')
                    f.flush()
                    os.fsync(f.fileno())
            finally:
                self._release_lock()
        else:
            # Fallback if lock fails (e.g., cross-process), just append (less safe)
            with open(self.global_manifest_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')

    def get_all_chunks(self) -> List[ChunkManifest]:
        """
        Reads the global manifest and returns all registered chunks.
        """
        chunks = []
        if not self.global_manifest_path.exists():
            return chunks

        with open(self.global_manifest_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    chunks.append(ChunkManifest.from_dict(data))
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupt line in global manifest: {line}")
        return chunks

    def get_new_chunks_since(self, last_seen_id: Optional[str] = None) -> List[ChunkManifest]:
        """
        Returns chunks that have been finalized since a specific chunk ID.
        If last_seen_id is None, returns all chunks.
        """
        all_chunks = self.get_all_chunks()
        if not last_seen_id:
            return all_chunks

        # Find index of last_seen_id
        start_idx = 0
        for i, chunk in enumerate(all_chunks):
            if chunk.chunk_id == last_seen_id:
                start_idx = i + 1
                break

        return all_chunks[start_idx:]

    def wait_for_next_chunk(self, last_seen_id: Optional[str] = None, timeout: float = 30.0) -> Optional[ChunkManifest]:
        """
        Blocks until a new chunk is available or timeout occurs.
        Useful for consumers (US2/US3) to stream processing.
        """
        start_time = time.time()
        last_checked_chunks = self.get_new_chunks_since(last_seen_id)
        
        while time.time() - start_time < timeout:
            current_chunks = self.get_new_chunks_since(last_seen_id)
            if len(current_chunks) > len(last_checked_chunks):
                return current_chunks[-1]
            time.sleep(0.5)
        
        return None

    def wait_for_next_chunk_generator(self, last_seen_id: Optional[str] = None) -> Iterator[ChunkManifest]:
        """
        Generator that yields chunks as they become available.
        Runs indefinitely until interrupted.
        """
        while True:
            chunk = self.wait_for_next_chunk(last_seen_id, timeout=60.0)
            if chunk:
                yield chunk
                last_seen_id = chunk.chunk_id
            else:
                # No chunk found, yield control and retry
                time.sleep(1.0)


def get_handoff_manager(output_dir: str) -> HandoffManager:
    """
    Factory function to get a HandoffManager instance.
    """
    return HandoffManager(output_dir)
