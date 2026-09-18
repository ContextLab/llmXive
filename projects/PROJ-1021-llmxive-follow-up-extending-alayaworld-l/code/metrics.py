"""
metrics.py: Semantic Drift Score Calculation.

Calculates the "Semantic Drift Score" by comparing the Symbolic State Log
against the Visual State Log (from CV Pipeline) on generated sequences.

Dependencies:
- symbolic_engine: Provides the Symbolic State Log structure.
- cv_pipeline: Provides the Visual State Log (FrameAnalysis/DetectedObject).

Output:
- data/results/drift_score_report.json
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from symbolic_engine import ActionLogEntry, ObjectState
from cv_pipeline import FrameAnalysis, DetectedObject


class DriftMetrics:
    """
    Computes semantic drift metrics between symbolic and visual state logs.
    """

    def __init__(self, symbolic_log_path: str, visual_log_path: str):
        self.symbolic_log_path = Path(symbolic_log_path)
        self.visual_log_path = Path(visual_log_path)
        self.symbolic_log: List[Dict] = []
        self.visual_log: List[Dict] = []
        self._load_data()

    def _load_data(self) -> None:
        """Load JSON logs from disk."""
        if not self.symbolic_log_path.exists():
            raise FileNotFoundError(f"Symbolic log not found: {self.symbolic_log_path}")
        if not self.visual_log_path.exists():
            raise FileNotFoundError(f"Visual log not found: {self.visual_log_path}")

        with open(self.symbolic_log_path, 'r') as f:
            self.symbolic_log = json.load(f)

        with open(self.visual_log_path, 'r') as f:
            self.visual_log = json.load(f)

        if len(self.symbolic_log) != len(self.visual_log):
            raise ValueError(
                f"Log length mismatch: Symbolic ({len(self.symbolic_log)}) vs "
                f"Visual ({len(self.visual_log)})"
            )

    def _compare_states(self, sym_state: Dict, vis_state: Dict) -> float:
        """
        Compare a single symbolic state entry with a visual state entry.
        Returns a drift penalty (0.0 = perfect match, >0.0 = mismatch).

        Logic:
        - HP difference: Absolute difference normalized by max HP (e.g., 100).
        - Alive/Dead status: 1.0 penalty if mismatch.
        - Position: Euclidean distance normalized (simplified to 1.0 penalty if far).
        """
        penalty = 0.0

        # 1. HP Comparison
        sym_hp = sym_state.get('hp', 0)
        vis_hp = vis_state.get('hp', 0)
        # Normalize HP difference (assuming max HP 100 for normalization)
        hp_diff = abs(sym_hp - vis_hp) / 100.0
        penalty += hp_diff * 0.4  # Weight HP at 40%

        # 2. Alive/Dead Status
        sym_alive = sym_state.get('alive', True)
        vis_alive = vis_state.get('alive', True)
        if sym_alive != vis_alive:
            penalty += 0.4  # Weight status at 40%

        # 3. Position/Presence (Simplified)
        # If symbolic says object exists but visual doesn't (or vice versa), high penalty.
        sym_exists = sym_state.get('exists', True)
        vis_exists = vis_state.get('exists', True)
        if sym_exists != vis_exists:
            penalty += 0.2  # Weight existence at 20%

        # Clamp penalty to [0.0, 1.0]
        return min(1.0, max(0.0, penalty))

    def calculate_drift_score(self) -> Dict[str, Any]:
        """
        Calculate the aggregate Semantic Drift Score.
        
        Formula: Mean of per-frame penalties across the sequence.
        """
        if not self.symbolic_log or not self.visual_log:
            return {"score": 0.0, "error": "Empty logs"}

        total_penalty = 0.0
        frame_count = len(self.symbolic_log)

        for i in range(frame_count):
            sym_entry = self.symbolic_log[i]
            vis_entry = self.visual_log[i]

            # Handle nested object lists if necessary, but assuming flat state per frame for now
            # If multiple objects, we might need to match them by ID.
            # For this implementation, we assume the logs contain a list of object states
            # and we compare them index-wise or by ID.
            
            # Assuming structure: {"frame_id": int, "objects": [{"id": str, "hp": int, ...}]}
            # If the log is a flat list of actions, we need to reconstruct state.
            # Based on symbolic_engine.py, ActionLogEntry is an action.
            # Based on cv_pipeline, FrameAnalysis contains DetectedObjects.
            
            # Let's assume the logs passed here are the *reconstructed state* per frame.
            # If they are raw action logs, we need to run the engine first.
            # Given the task description "Symbolic State Log vs Visual State Log",
            # we assume these are state snapshots.
            
            # Fallback: If logs are raw actions, we can't compare directly without state reconstruction.
            # We will assume the logs are already processed into state snapshots.
            
            # Simple object-wise comparison (assuming single object or matched order)
            if isinstance(sym_entry, list) and isinstance(vis_entry, list):
                # Compare lists of objects
                for s_obj, v_obj in zip(sym_entry, vis_entry):
                    total_penalty += self._compare_states(s_obj, v_obj)
            elif isinstance(sym_entry, dict) and isinstance(vis_entry, dict):
                total_penalty += self._compare_states(sym_entry, vis_entry)
            else:
                # Fallback for unknown structure
                total_penalty += 1.0

        mean_drift = total_penalty / frame_count if frame_count > 0 else 0.0
        
        return {
            "score": float(mean_drift),
            "frame_count": frame_count,
            "total_penalty": float(total_penalty),
            "status": "PASS" if mean_drift < 0.5 else "HIGH_DRIFT" # Threshold example
        }

    def generate_report(self, output_path: str) -> Dict[str, Any]:
        """Calculate score and save report to JSON."""
        result = self.calculate_drift_score()
        result["symbolic_log_path"] = str(self.symbolic_log_path)
        result["visual_log_path"] = str(self.visual_log_path)
        result["timestamp"] = str(datetime.now(timezone.utc))
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result


from datetime import datetime, timezone


def calculate_drift_score(
    symbolic_log_path: str, 
    visual_log_path: str, 
    output_path: str
) -> Dict[str, Any]:
    """
    Convenience function to calculate drift score and save report.
    """
    metrics = DriftMetrics(symbolic_log_path, visual_log_path)
    return metrics.generate_report(output_path)


def main():
    """
    CLI Entry Point.
    Expects paths to symbolic and visual logs.
    Default paths used if arguments not provided (for testing).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Calculate Semantic Drift Score")
    parser.add_argument(
        "--symbolic-log", 
        type=str, 
        default="data/logs/symbolic_state_log.json",
        help="Path to the symbolic state log JSON"
    )
    parser.add_argument(
        "--visual-log", 
        type=str, 
        default="data/logs/visual_state_log.json",
        help="Path to the visual state log JSON"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/results/drift_score_report.json",
        help="Path to output report JSON"
    )

    args = parser.parse_args()

    try:
        result = calculate_drift_score(args.symbolic_log, args.visual_log, args.output)
        print(f"Drift Score Calculation Complete.")
        print(f"Score: {result['score']:.4f}")
        print(f"Status: {result['status']}")
        print(f"Report saved to: {args.output}")
        return 0
    except Exception as e:
        print(f"Error calculating drift score: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())