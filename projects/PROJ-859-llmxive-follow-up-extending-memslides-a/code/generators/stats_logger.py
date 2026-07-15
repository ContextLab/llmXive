"""
Statistics and Checksum Logger for Synthetic Trace Generation.

This module implements T017: Log generation statistics and checksums to a state file.
It provides functionality to compute SHA256 checksums for generated trace files
and aggregate generation statistics (count, total tool calls, entropy, etc.)
into a persistent JSON state file.
"""
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import Config


class GenerationStatsLogger:
    """
    Logs generation statistics and file checksums to a persistent state file.
    """

    def __init__(self, config: Config):
        self.config = config
        self.state_file_path = Path(config.DATA_DIR) / "generation_state.json"
        self._ensure_state_file()

    def _ensure_state_file(self):
        """Ensure the state file exists, initializing it if necessary."""
        if not self.state_file_path.exists():
            self._write_state({
                "last_run": None,
                "total_sessions_generated": 0,
                "total_tool_calls": 0,
                "total_arg_variance_sum": 0.0,
                "files": []
            })

    def _read_state(self) -> Dict[str, Any]:
        """Read the current state from the JSON file."""
        with open(self.state_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_state(self, state: Dict[str, Any]):
        """Write the state to the JSON file."""
        with open(self.state_file_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, default=str)

    def compute_checksum(self, file_path: Path) -> str:
        """
        Compute SHA256 checksum of a file.
        
        Args:
            file_path: Path to the file to checksum.
            
        Returns:
            Hexadecimal string of the SHA256 hash.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def log_session(self, session_id: str, file_path: Path, stats: Dict[str, Any]):
        """
        Log statistics and checksum for a single generated session.
        
        Args:
            session_id: Unique identifier for the session.
            file_path: Path to the generated JSON file.
            stats: Dictionary containing session-specific statistics 
                   (e.g., tool_call_count, arg_variance, entropy).
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Session file not found: {file_path}")

        checksum = self.compute_checksum(file_path)
        
        current_state = self._read_state()
        
        session_entry = {
            "session_id": session_id,
            "filename": file_path.name,
            "checksum": checksum,
            "stats": stats,
            "logged_at": datetime.now().isoformat()
        }
        
        current_state["files"].append(session_entry)
        current_state["total_sessions_generated"] += 1
        
        # Aggregate global stats
        if "tool_call_count" in stats:
            current_state["total_tool_calls"] += stats["tool_call_count"]
        if "arg_variance" in stats:
            current_state["total_arg_variance_sum"] += stats["arg_variance"]
            
        current_state["last_run"] = datetime.now().isoformat()
        
        self._write_state(current_state)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all logged generation statistics.
        
        Returns:
            Dictionary containing aggregated statistics.
        """
        state = self._read_state()
        total_sessions = state["total_sessions_generated"]
        
        summary = {
            "last_run": state["last_run"],
            "total_sessions": total_sessions,
            "total_tool_calls": state["total_tool_calls"],
            "average_tool_calls_per_session": (
                state["total_tool_calls"] / total_sessions if total_sessions > 0 else 0
            ),
            "average_arg_variance": (
                state["total_arg_variance_sum"] / total_sessions if total_sessions > 0 else 0
            ),
            "file_count": len(state["files"])
        }
        return summary


def log_generation_stats(
    session_id: str, 
    file_path: Path, 
    stats: Dict[str, Any], 
    config: Optional[Config] = None
):
    """
    Convenience function to log generation stats for a session.
    
    Args:
        session_id: Unique identifier for the session.
        file_path: Path to the generated JSON file.
        stats: Session-specific statistics.
        config: Optional Config instance. If None, loads default config.
    """
    if config is None:
        config = Config()
    
    logger = GenerationStatsLogger(config)
    logger.log_session(session_id, file_path, stats)


def get_generation_summary(config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Convenience function to get the generation summary.
    
    Args:
        config: Optional Config instance.
        
    Returns:
        Aggregated generation statistics.
    """
    if config is None:
        config = Config()
    
    logger = GenerationStatsLogger(config)
    return logger.get_summary()
