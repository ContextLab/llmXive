"""
State Store utility for managing project state and historical confidence data.

This module provides the StateStore class to manage the YAML state file
required for tracking historical confidence scores across training cycles.

Dependencies:
- contracts/ (T004a-d): Schema validation for state data
- utils/seeds.py (T008): Seed management for reproducibility
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

from utils.logging import get_logger
from utils.validation import ensure_directory, validate_yaml_file
from config import get_config

logger = get_logger(__name__)

# Project-specific state file path
PROJECT_ID = "PROJ-923-llmxive-follow-up-extending-zone-of-prox"
STATE_DIR = Path("state") / "projects"
STATE_FILE_PATH = STATE_DIR / f"{PROJECT_ID}.yaml"

@dataclass
class CycleRecord:
    """Record for a single training cycle's state."""
    cycle_id: int
    task_id: str
    seed: int
    timestamp: str
    confidence_scores: List[float]
    prompt_length: int
    accuracy: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for YAML serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CycleRecord':
        """Create record from dictionary."""
        return cls(
            cycle_id=data['cycle_id'],
            task_id=data['task_id'],
            seed=data['seed'],
            timestamp=data['timestamp'],
            confidence_scores=data['confidence_scores'],
            prompt_length=data['prompt_length'],
            accuracy=data['accuracy'],
            metrics=data.get('metrics', {})
        )

@dataclass
class ProjectState:
    """Complete project state container."""
    project_id: str
    created_at: str
    updated_at: str
    version: int
    cycles: List[CycleRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for YAML serialization."""
        return {
            'project_id': self.project_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'version': self.version,
            'cycles': [cycle.to_dict() for cycle in self.cycles],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectState':
        """Create state from dictionary."""
        cycles = [CycleRecord.from_dict(c) for c in data.get('cycles', [])]
        return cls(
            project_id=data['project_id'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            version=data.get('version', 1),
            cycles=cycles,
            metadata=data.get('metadata', {})
        )

class StateStore:
    """
    Manages the project state YAML file for tracking historical confidence data.
    
    This class provides methods to:
    - Load state from disk
    - Save state to disk
    - Append new cycle records
    - Retrieve historical confidence scores for CAP classification
    - Validate state against schema contracts
    """
    
    def __init__(self, state_file_path: Optional[Path] = None):
        """
        Initialize the StateStore.
        
        Args:
            state_file_path: Optional custom path to state file.
                             Defaults to state/projects/{PROJECT_ID}.yaml
        """
        self._path = state_file_path or STATE_FILE_PATH
        self._state: Optional[ProjectState] = None
        self._ensure_state_directory()
        
        # Try to load existing state
        if self._path.exists():
            try:
                self._state = self._load_state_from_file()
                logger.info(f"Loaded existing state from {self._path}")
            except Exception as e:
                logger.warning(f"Failed to load existing state: {e}. Initializing new state.")
                self._state = self._create_new_state()
        else:
            self._state = self._create_new_state()
            self._save_state()
            logger.info(f"Created new state file at {self._path}")
    
    def _ensure_state_directory(self) -> None:
        """Ensure the state directory exists."""
        ensure_directory(self._path.parent)
    
    def _create_new_state(self) -> ProjectState:
        """Create a new empty project state."""
        now = datetime.utcnow().isoformat()
        return ProjectState(
            project_id=PROJECT_ID,
            created_at=now,
            updated_at=now,
            version=1,
            cycles=[],
            metadata={}
        )
    
    def _load_state_from_file(self) -> ProjectState:
        """Load state from the YAML file."""
        with open(self._path, 'r') as f:
            data = yaml.safe_load(f)
        
        state = ProjectState.from_dict(data)
        
        # Validate against schema if available
        try:
            from utils.validation import validate_yaml_file
            validate_yaml_file(self._path)
        except Exception as e:
            logger.warning(f"State validation warning: {e}")
        
        return state
    
    def _save_state(self) -> None:
        """Save current state to the YAML file."""
        if self._state is None:
            raise RuntimeError("Cannot save state: state is not initialized")
        
        self._state.updated_at = datetime.utcnow().isoformat()
        self._state.version += 1
        
        with open(self._path, 'w') as f:
            yaml.dump(self._state.to_dict(), f, default_flow_style=False, sort_keys=False)
        
        logger.debug(f"Saved state version {self._state.version} to {self._path}")
    
    def add_cycle_record(self, record: CycleRecord) -> None:
        """
        Add a new cycle record to the state.
        
        Args:
            record: The cycle record to add
        """
        if self._state is None:
            raise RuntimeError("Cannot add record: state is not initialized")
        
        self._state.cycles.append(record)
        self._save_state()
        logger.debug(f"Added cycle {record.cycle_id} for task {record.task_id}")
    
    def get_historical_confidence_scores(self, task_id: str, seed: Optional[int] = None) -> List[List[float]]:
        """
        Retrieve historical confidence scores for a specific task (optionally filtered by seed).
        
        This is the primary interface for the CAP classifier (T021) to access
        historical confidence data for calculating mean/variance across cycles.
        
        Args:
            task_id: The task ID to filter by
            seed: Optional seed value to filter by (if None, returns all seeds)
        
        Returns:
            List of confidence score lists, one per matching cycle
        """
        if self._state is None:
            return []
        
        results = []
        for cycle in self._state.cycles:
            if cycle.task_id != task_id:
                continue
            if seed is not None and cycle.seed != seed:
                continue
            results.append(cycle.confidence_scores)
        
        logger.debug(f"Retrieved {len(results)} historical confidence records for task {task_id}")
        return results
    
    def get_all_cycles_for_task(self, task_id: str) -> List[CycleRecord]:
        """
        Get all cycle records for a specific task.
        
        Args:
            task_id: The task ID to filter by
        
        Returns:
            List of CycleRecord objects for the task
        """
        if self._state is None:
            return []
        
        return [c for c in self._state.cycles if c.task_id == task_id]
    
    def get_latest_cycle(self, task_id: Optional[str] = None, seed: Optional[int] = None) -> Optional[CycleRecord]:
        """
        Get the most recent cycle record, optionally filtered by task_id and seed.
        
        Args:
            task_id: Optional task ID to filter by
            seed: Optional seed to filter by
        
        Returns:
            The most recent CycleRecord or None if no matching records exist
        """
        if self._state is None or not self._state.cycles:
            return None
        
        filtered_cycles = self._state.cycles
        if task_id is not None:
            filtered_cycles = [c for c in filtered_cycles if c.task_id == task_id]
        if seed is not None:
            filtered_cycles = [c for c in filtered_cycles if c.seed == seed]
        
        if not filtered_cycles:
            return None
        
        # Return the one with highest cycle_id
        return max(filtered_cycles, key=lambda c: c.cycle_id)
    
    def get_state_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about the current state.
        
        Returns:
            Dictionary containing state summary metrics
        """
        if self._state is None:
            return {}
        
        total_cycles = len(self._state.cycles)
        unique_tasks = len(set(c.task_id for c in self._state.cycles))
        unique_seeds = len(set(c.seed for c in self._state.cycles))
        
        return {
            'project_id': self._state.project_id,
            'version': self._state.version,
            'total_cycles': total_cycles,
            'unique_tasks': unique_tasks,
            'unique_seids': unique_seeds,
            'created_at': self._state.created_at,
            'updated_at': self._state.updated_at
        }
    
    def clear_all_records(self) -> None:
        """
        Clear all cycle records from the state.
        
        WARNING: This will permanently delete all historical data.
        """
        if self._state is None:
            return
        
        logger.warning("Clearing all cycle records from state store")
        self._state.cycles = []
        self._save_state()
    
    def reset_version(self) -> None:
        """Reset the state version to 1 and clear all records."""
        if self._state is None:
            return
        
        self._state.cycles = []
        self._state.version = 1
        self._state.updated_at = datetime.utcnow().isoformat()
        self._save_state()
    
    @property
    def path(self) -> Path:
        """Get the path to the state file."""
        return self._path
    
    @property
    def state(self) -> Optional[ProjectState]:
        """Get the current state object."""
        return self._state

# Convenience function to get a StateStore instance
def get_state_store(state_file_path: Optional[Path] = None) -> StateStore:
    """
    Get or create a StateStore instance.
    
    Args:
        state_file_path: Optional custom path to state file
    
    Returns:
        StateStore instance
    """
    return StateStore(state_file_path)

# Initialize default state store on module load
default_store = get_state_store()
logger.info(f"StateStore initialized at {default_store.path}")
