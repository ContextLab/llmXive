"""
Script to generate sample JSON event logs for T015 validation.

This script demonstrates the `generate_event_log` function by creating
a sequence of events for a simulated maze traversal and writing them
to `data/processed/sample_events.jsonl`.
"""
import os
import sys
import json

# Add project root to path to allow imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from renderer import generate_event_log

def main():
    output_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "sample_events.jsonl")

    # Simulated sequence of events for a fixed seed scenario
    events = [
        {"t": 0, "pos": (1, 1), "action": "spawn", "event": "start", "details": {"seed": 42}},
        {"t": 1, "pos": (1, 2), "action": "move_down", "event": "step"},
        {"t": 2, "pos": (2, 2), "action": "move_right", "event": "step"},
        {"t": 3, "pos": (2, 2), "action": "move_right", "event": "blocked", "details": {"reason": "wall"}},
        {"t": 4, "pos": (3, 2), "action": "move_right", "event": "step"},
        {"t": 5, "pos": (3, 3), "action": "move_down", "event": "step"},
        {"t": 6, "pos": (3, 3), "action": "pick_up", "event": "item_acquired", "details": {"item_id": "key_01"}},
    ]

    with open(output_file, 'w') as f:
        for ev in events:
            log_line = generate_event_log(
                time_step=ev["t"],
                player_pos=(ev["pos"][0], ev["pos"][1]),
                action=ev["action"],
                event_type=ev["event"],
                details=ev.get("details")
            )
            f.write(log_line + "\n")

    print(f"Successfully generated event logs to {output_file}")

if __name__ == "__main__":
    main()
