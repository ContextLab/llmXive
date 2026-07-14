"""
Helper script to generate mock events metadata for testing T017.
In a real pipeline, this would be generated from the fMRI design matrix.
This script creates a realistic-looking events.json file under data/neural/processed/
to allow T017 to run end-to-end.
"""

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "neural" / "processed" / "events.json"

def generate_events_for_subject(subject_id: str, num_events: int = 10) -> list:
    """Generate a list of events for a single subject."""
    events = []
    current_time = 0
    rois = ["L_Hippocampus", "R_Hippocampus", "DLPFC"]

    for i in range(num_events):
        duration = random.randint(2, 6)  # 2-6 timepoints
        start = current_time
        end = current_time + duration

        events.append({
            "event_id": f"{subject_id}_evt_{i:03d}",
            "start": start,
            "end": end,
            "type": random.choice(["stop_signal", "go", "neutral"])
        })
        current_time = end

    return events

def main():
    """Generate events metadata for a set of subjects."""
    subjects = [f"sub-{i:03d}" for i in range(1, 6)]  # 5 subjects
    all_events = {}

    for subj in subjects:
        all_events[subj] = generate_events_for_subject(subj, num_events=8)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_events, f, indent=2)

    print(f"Generated events metadata for {len(subjects)} subjects at {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
