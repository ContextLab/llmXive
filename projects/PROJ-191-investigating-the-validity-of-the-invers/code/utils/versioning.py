"""
Versioning utility for atomic state updates.

This module provides functionality to manage project state files
with atomic updates to prevent corruption during concurrent access
or interrupted writes.
"""

import json
import os
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class VersionedState:
    """
    Manages a versioned state file with atomic updates.

    Ensures that state file writes are atomic by writing to a
    temporary file first, then renaming it to the target path.
    """

    def __init__(self, state_path: str):
        """
        Initialize the versioned state manager.

        Args:
            state_path: Path to the state file (JSON format).
        """
        self.state_path = Path(state_path)
        self._ensure_parent_dir()

    def _ensure_parent_dir(self) -> None:
        """Ensure the parent directory of the state file exists."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def _compute_checksum(self, content: str) -> str:
        """Compute SHA-256 checksum of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def load(self) -> Dict[str, Any]:
        """
        Load the current state from disk.

        Returns:
            Dictionary containing the current state.
            Returns an empty dict if file doesn't exist.
        """
        if not self.state_path.exists():
            return {}

        with open(self.state_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, state: Dict[str, Any]) -> None:
        """
        Atomically save the state to disk.

        The state is written to a temporary file first, then
        renamed to the target path to ensure atomicity.

        Args:
            state: Dictionary to save as JSON.
        """
        # Add metadata to state
        state['metadata'] = {
            'updated_at': datetime.utcnow().isoformat(),
            'version': state.get('metadata', {}).get('version', 0) + 1,
        }

        # Serialize to JSON
        content = json.dumps(state, indent=2, ensure_ascii=False)
        checksum = self._compute_checksum(content)
        state['metadata']['checksum'] = checksum

        # Re-serialize with checksum
        content = json.dumps(state, indent=2, ensure_ascii=False)

        # Atomic write: write to temp file, then rename
        fd, temp_path = tempfile.mkstemp(
            dir=str(self.state_path.parent),
            suffix='.tmp',
            text=True
        )
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            os.replace(temp_path, self.state_path)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atomically update the state with new values.

        Args:
            updates: Dictionary of key-value pairs to update.

        Returns:
            The updated state dictionary.
        """
        current_state = self.load()
        current_state.update(updates)
        self.save(current_state)
        return current_state

    def get_version(self) -> int:
        """
        Get the current version number from the state file.

        Returns:
            Version number (0 if state file doesn't exist).
        """
        state = self.load()
        return state.get('metadata', {}).get('version', 0)

    def verify_integrity(self) -> bool:
        """
        Verify the integrity of the state file.

        Checks if the stored checksum matches the computed checksum.

        Returns:
            True if integrity check passes, False otherwise.
        """
        if not self.state_path.exists():
            return False

        state = self.load()
        stored_checksum = state.get('metadata', {}).get('checksum')

        if not stored_checksum:
            return False

        # Recompute checksum from current content
        content = json.dumps(state, indent=2, ensure_ascii=False)
        computed_checksum = self._compute_checksum(content)

        return stored_checksum == computed_checksum

    def rollback_to_version(self, target_version: int) -> bool:
        """
        Rollback state to a previous version.

        Note: This requires the version history to be maintained
        separately. Currently returns False as rollback history
        is not implemented.

        Args:
            target_version: Version number to rollback to.

        Returns:
            False until rollback history is implemented.
        """
        # TODO: Implement version history tracking for rollback
        return False


def create_state_manager(state_path: str) -> VersionedState:
    """
    Factory function to create a VersionedState instance.

    Args:
        state_path: Path to the state file.

    Returns:
        VersionedState instance.
    """
    return VersionedState(state_path)


def atomic_save_json(path: str, data: Dict[str, Any]) -> None:
    """
    Convenience function for atomic JSON file saving.

    Args:
        path: Target file path.
        data: Dictionary to save.
    """
    manager = VersionedState(path)
    manager.save(data)


def atomic_update_json(path: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for atomic JSON file updates.

    Args:
        path: Target file path.
        updates: Dictionary of updates to apply.

    Returns:
        Updated dictionary.
    """
    manager = VersionedState(path)
    return manager.update(updates)
