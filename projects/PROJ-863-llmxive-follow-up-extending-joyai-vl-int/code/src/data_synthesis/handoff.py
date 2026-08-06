"""
Streaming Handoff Logic for llmXive Data Pipeline.

This module implements the 'Streaming Handoff' mechanism allowing downstream
tasks (US2/US3) to begin processing video chunks as soon as they are written
by the generator (T013), avoiding false serialization where US2 waits for
the entire 50-hour dataset to finish generating.

It provides:
1. ChunkManifest: A dataclass representing the state of a single processed chunk.
2. HandoffManager: A thread-safe manager to write chunk manifests, track completion,
   and provide an iterator for consumers to wait for and yield new chunks.
"""

import json
import os
import time
import fcntl
import threading
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Generator
from src.utils.logging import get_logger


@dataclass
class ChunkManifest:
    """
    Represents the state of a single video chunk in the handoff process.

    Attributes:
        chunk_id (str): Unique identifier for the chunk (e.g., 'chunk_001').
        start_time (float): Start timestamp of the chunk in seconds.
        end_time (float): End timestamp of the chunk in seconds.
        frame_count (int): Number of frames in this chunk.
        file_path (str): Absolute path to the JSONL file containing the frames.
        status (str): Current status ('pending', 'processing', 'completed', 'failed').
        created_at (float): Unix timestamp of creation.
        completed_at (Optional[float]): Unix timestamp of completion.
    """
    chunk_id: str
    start_time: float
    end_time: float
    frame_count: int
    file_path: str
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def mark_processing(self) -> None:
        """Mark the chunk as currently being processed by a consumer."""
        self.status = "processing"

    def mark_completed(self) -> None:
        """Mark the chunk as successfully processed."""
        self.status = "completed"
        self.completed_at = time.time()

    def mark_failed(self) -> None:
        """Mark the chunk as failed."""
        self.status = "failed"
        self.completed_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkManifest":
        """Create a ChunkManifest from a dictionary."""
        return cls(**data)


class HandoffManager:
    """
    Manages the streaming handoff of video chunks between generator (T013)
    and downstream consumers (US2/US3).

    Features:
    - Atomic writes using temporary files and rename.
    - File locking (fcntl) to prevent race conditions on the manifest index.
    - Blocking iterator for consumers to wait for new chunks.
    """

    def __init__(self, manifest_dir: str, logger: Optional[Any] = None):
        """
        Initialize the HandoffManager.

        Args:
            manifest_dir: Directory where chunk manifests will be stored.
            logger: Optional logger instance.
        """
        self.manifest_dir = Path(manifest_dir)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.manifest_dir / "handoff_index.jsonl"
        self.logger = logger or get_logger(__name__)
        self._lock = threading.Lock()

        # Ensure index file exists
        if not self.index_file.exists():
            self.index_file.touch()

    def _get_lock_file(self) -> Path:
        """Get the path to the lock file."""
        return self.manifest_dir / ".handoff.lock"

    def write_chunk_manifest(self, manifest: ChunkManifest) -> None:
        """
        Write a new chunk manifest to the index atomically.

        This is the 'handoff' point where the producer (generator) signals
        a new chunk is ready.

        Args:
            manifest: The ChunkManifest object to write.
        """
        manifest_path = self.manifest_dir / f"{manifest.chunk_id}.json"
        
        # Write the individual chunk manifest first (atomic on most FS)
        temp_path = manifest_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
        
        # Atomic rename
        os.replace(temp_path, manifest_path)

        # Append to the main index file with locking
        lock_path = self._get_lock_file()
        with open(lock_path, 'w') as lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                with open(self.index_file, 'a') as index_fd:
                    index_fd.write(json.dumps(manifest.to_dict()) + '\n')
                    index_fd.flush()
                    os.fsync(index_fd.fileno())
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
        
        self.logger.info(f"Handoff: Chunk {manifest.chunk_id} written to {manifest_path}")

    def get_all_chunks(self) -> List[ChunkManifest]:
        """
        Retrieve all chunk manifests currently in the index.

        Returns:
            List of ChunkManifest objects.
        """
        chunks = []
        if not self.index_file.exists():
            return chunks

        with open(self.index_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        chunks.append(ChunkManifest.from_dict(data))
                    except json.JSONDecodeError:
                        self.logger.warning(f"Skipping malformed manifest line: {line}")
        return chunks

    def get_new_chunks_since(self, last_seen_chunk_id: Optional[str] = None) -> List[ChunkManifest]:
        """
        Get chunks that have been added since a specific chunk ID.

        Args:
            last_seen_chunk_id: The ID of the last chunk processed. If None, returns all.

        Returns:
            List of new ChunkManifest objects.
        """
        all_chunks = self.get_all_chunks()
        if not last_seen_chunk_id:
            return all_chunks

        # Find index of last seen
        try:
            idx = next(i for i, c in enumerate(all_chunks) if c.chunk_id == last_seen_chunk_id)
            return all_chunks[idx + 1:]
        except StopIteration:
            # If the last seen ID is not found, return everything (or log warning)
            self.logger.warning(f"Last seen chunk {last_seen_chunk_id} not found. Returning all chunks.")
            return all_chunks

    def wait_for_next_chunk(
        self, 
        last_seen_chunk_id: Optional[str] = None, 
        timeout: float = 30.0
    ) -> Optional[ChunkManifest]:
        """
        Blocking call to wait for the next available chunk.

        Args:
            last_seen_chunk_id: The ID of the last processed chunk.
            timeout: How long to wait for a new chunk before returning None.

        Returns:
            A ChunkManifest if available, or None if timeout.
        """
        start_time = time.time()
        while True:
            new_chunks = self.get_new_chunks_since(last_seen_chunk_id)
            if new_chunks:
                return new_chunks[0]
            
            if time.time() - start_time > timeout:
                return None
            
            # Sleep briefly to avoid busy waiting
            time.sleep(0.5)

    def wait_for_next_chunk_generator(
        self, 
        last_seen_chunk_id: Optional[str] = None
    ) -> Generator[ChunkManifest, None, None]:
        """
        Generator that yields chunks as they become available.
        This is the primary interface for US2/US3 to stream process data.

        Args:
            last_seen_chunk_id: The ID of the last processed chunk.

        Yields:
            ChunkManifest objects as they are written by the generator.
        """
        while True:
            chunk = self.wait_for_next_chunk(last_seen_chunk_id, timeout=10.0)
            if chunk:
                yield chunk
                last_seen_chunk_id = chunk.chunk_id
            else:
                # Check if we should stop (e.g., generator finished)
                # For now, we just loop. In a real system, a 'finished' flag might be used.
                pass

    def mark_chunk_status(self, chunk_id: str, status: str) -> bool:
        """
        Update the status of a specific chunk in the index.
        
        Note: This updates the in-memory index file. For production, 
        a database or more robust locking might be needed.

        Args:
            chunk_id: The ID of the chunk.
            status: The new status string.

        Returns:
            True if updated, False if not found.
        """
        if not self.index_file.exists():
            return False

        lock_path = self._get_lock_file()
        with open(lock_path, 'w') as lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                lines = []
                found = False
                with open(self.index_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if data.get('chunk_id') == chunk_id:
                                data['status'] = status
                                if status in ['completed', 'failed']:
                                    data['completed_at'] = time.time()
                                found = True
                            lines.append(json.dumps(data))
                        except json.JSONDecodeError:
                            lines.append(line)
                
                if found:
                    with open(self.index_file, 'w') as f:
                        f.write('\n'.join(lines) + '\n')
                    return True
                return False
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)


# Singleton instance for easy access in scripts
_handoff_manager: Optional[HandoffManager] = None
_manager_lock = threading.Lock()


def get_handoff_manager(manifest_dir: Optional[str] = None) -> HandoffManager:
    """
    Get or create the global HandoffManager instance.

    Args:
        manifest_dir: Directory for manifests. Defaults to 'data/handoff' if not set.

    Returns:
        The global HandoffManager instance.
    """
    global _handoff_manager
    with _manager_lock:
        if _handoff_manager is None:
            if manifest_dir is None:
                manifest_dir = "data/handoff"
            _handoff_manager = HandoffManager(manifest_dir)
        return _handoff_manager


def main():
    """
    CLI entry point for testing the handoff logic.
    Simulates a producer writing chunks and a consumer reading them.
    """
    import sys
    import threading

    print("Starting Handoff Logic Test...")
    
    # Use a temporary directory for testing
    test_dir = "data/test_handoff"
    manager = HandoffManager(test_dir)

    def producer():
        """Simulates the generator writing chunks."""
        for i in range(5):
            chunk = ChunkManifest(
                chunk_id=f"chunk_{i:03d}",
                start_time=i * 100.0,
                end_time=(i + 1) * 100.0,
                frame_count=1000,
                file_path=f"data/raw/chunk_{i:03d}.jsonl"
            )
            manager.write_chunk_manifest(chunk)
            print(f"Producer: Wrote {chunk.chunk_id}")
            time.sleep(2) # Simulate generation time
        print("Producer: Finished generating all chunks.")

    def consumer():
        """Simulates US2/US3 processing chunks as they arrive."""
        last_id = None
        # Wait for at least one chunk
        chunk = manager.wait_for_next_chunk(last_id, timeout=5.0)
        if not chunk:
            print("Consumer: Timeout waiting for first chunk.")
            return

        # Use the generator for continuous streaming
        for chunk in manager.wait_for_next_chunk_generator(last_id):
            print(f"Consumer: Processing {chunk.chunk_id}...")
            # Simulate processing
            time.sleep(1)
            manager.mark_chunk_status(chunk.chunk_id, "completed")
            print(f"Consumer: Completed {chunk.chunk_id}")
            last_id = chunk.chunk_id
            
            # Stop after processing all 5 chunks (for test)
            if last_id == "chunk_004":
                break

    # Run producer and consumer in threads
    p_thread = threading.Thread(target=producer)
    c_thread = threading.Thread(target=consumer)

    c_thread.start()
    p_thread.start()

    p_thread.join()
    c_thread.join()

    print("Test completed.")


if __name__ == "__main__":
    main()