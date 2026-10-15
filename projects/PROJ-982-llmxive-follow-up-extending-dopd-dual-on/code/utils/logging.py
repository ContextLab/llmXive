"""
TrainingLogger – writes per‑step metrics to a JSON‑Lines file and
optionally records structured events (e.g., λ‑switches) to a legacy JSON
file.

The logger is deliberately lightweight: it does not perform schema
validation itself (tests validate against the contract), but it guarantees
that the required files exist and that each line is a valid JSON object.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class TrainingLogger:
    """
    Logger for DOPD / Uniform training runs.

    Parameters
    ----------
    run_id: str
        Identifier for the run (e.g., ``dopd_seed_42``). Used only for
        traceability; it is written into each JSON‑Lines entry.
    output_dir: str
        Directory where ``training_log.jsonl`` and ``training_log.json``
        will be created (e.g., ``data/raw``).
    seed: int
        Seed associated with the run – also stored in each log line.
    """

    def __init__(self, run_id: str, output_dir: str, seed: int):
        self.run_id = run_id
        self.seed = seed
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Paths for the two log artifacts.
        self.jsonl_path = self.output_dir / "training_log.jsonl"
        self.json_path = self.output_dir / "training_log.json"

        # Ensure both files exist.
        self.jsonl_path.touch(exist_ok=True)
        if not self.json_path.exists():
            # Initialise with an empty JSON object.
            with self.json_path.open("w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

    def log_step(
        self,
        step: int,
        reward: float,
        loss: float,
        accuracy: float,
        entropy: float,
    ) -> None:
        """
        Append a single training‑step record to the JSON‑Lines file.

        The record contains the minimal fields required by the
        ``training_log.schema.yaml`` contract.
        """
        entry: Dict[str, Any] = {
            "run_id": self.run_id,
            "seed": self.seed,
            "step": step,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reward": reward,
            "loss": loss,
            "accuracy": accuracy,
            "entropy": entropy,
        }
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def log_event(self, event: Dict[str, Any]) -> None:
        """
        Record a structured event (e.g., a λ‑switch) in the legacy
        ``training_log.json`` file.

        The file stores a single JSON object; new keys are merged into it.
        If a key already exists, it is overwritten with the latest value.
        """
        # Load existing content.
        if self.json_path.exists():
            with self.json_path.open("r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}

        # Merge the incoming event.
        data.update(event)

        # Write back atomically.
        tmp_path = self.json_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(self.json_path)

    def save_metrics(self) -> None:
        """
        Placeholder for any finalisation logic.  Currently a no‑op because
        all metrics are written incrementally via ``log_step``.
        """
        pass
