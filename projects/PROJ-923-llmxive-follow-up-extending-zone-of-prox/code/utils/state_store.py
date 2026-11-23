import json
import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict, is_dataclass
from utils.logging import get_logger

@dataclass
class CycleRecord:
    cycle: int
    confidence_mean: float
    confidence_var: float
    classification: str
    timestamp: str = field(default_factory=lambda: "N/A")

@dataclass
class ProjectState:
    project_id: str
    history: List[CycleRecord] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: "N/A")

class StateStore:
    def __init__(self, project_id: str, state_file: Optional[str] = None):
        self.project_id = project_id
        self.state_file = state_file or f"state/projects/{project_id}.yaml"
        self.history: List[CycleRecord] = []
        self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and 'history' in data:
                        self.history = [CycleRecord(**h) for h in data['history']]
                get_logger().info(f"Loaded state for {self.project_id} with {len(self.history)} records.")
            except Exception as e:
                get_logger().warning(f"Failed to load state file: {e}. Starting fresh.")
                self.history = []
        else:
            self.history = []

    def add_record(self, record: CycleRecord):
        self.history.append(record)
        self._save()

    def get_history(self) -> List[CycleRecord]:
        return self.history

    def _save(self):
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        data = {
            "project_id": self.project_id,
            "history": [asdict(h) for h in self.history],
            "last_updated": "N/A"
        }
        with open(self.state_file, 'w') as f:
            yaml.safe_dump(data, f)

_global_store: Optional[StateStore] = None

def get_state_store(project_id: str) -> StateStore:
    global _global_store
    if _global_store is None or _global_store.project_id != project_id:
        _global_store = StateStore(project_id)
    return _global_store

def reset_state_store():
    global _global_store
    _global_store = None
