"""
Helper script to generate mock ROI timecourses for testing T017.
In a real pipeline, this comes from T013 (extract BOLD timecourses).
This script creates a realistic-looking roi_timecourses.csv file under data/neural/processed/
to allow T017 to run end-to-end.
"""

import csv
import random
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "neural" / "processed" / "roi_timecourses.csv"

def generate_timecourses_for_subject(subject_id: str, num_timepoints: int = 100, num_rois: int = 3) -> list:
    """Generate timecourse data for a single subject."""
    rows = []
    rois = ["L_Hippocampus", "R_Hippocampus", "DLPFC"]

    # Generate base signal with some noise and event-related modulation
    base_signal = 100.0
    noise_level = 2.0

    for t in range(num_timepoints):
        # Simulate event-related response (simple boxcar convolved with HRF approximation)
        # Just adding some random bumps for realism
        event_response = 0.0
        if random.random() < 0.05:  # 5% chance of an event at this timepoint
            event_response = random.uniform(1.0, 3.0)

        for roi in rois:
            # Add some ROI-specific baseline variation
            roi_offset = {"L_Hippocampus": 0.0, "R_Hippocampus": 0.2, "DLPFC": -0.1}[roi]
            signal = base_signal + roi_offset + np.random.normal(0, noise_level) + event_response
            
            rows.append({
                "subject_id": subject_id,
                "roi": roi,
                "timepoint": t,
                "signal": round(signal, 4)
            })

    return rows

def main():
    """Generate timecourse data for a set of subjects."""
    subjects = [f"sub-{i:03d}" for i in range(1, 6)]  # 5 subjects
    all_rows = []

    for subj in subjects:
        all_rows.extend(generate_timecourses_for_subject(subj, num_timepoints=100))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["subject_id", "roi", "timepoint", "signal"])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Generated timecourse data for {len(subjects)} subjects at {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
