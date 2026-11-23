"""
Validation script for quickstart.md.
Ensures all documented steps produce the expected artifacts.
"""
import os
import sys
from pathlib import Path

REQUIRED_FILES = [
  "data/processed/tag_frequencies.csv",
  "data/processed/trend_results.json",
  "data/processed/decomposition_results.json",
  "data/processed/cluster_results.json",
  "data/processed/confidence_interval.json",
  "data/processed/external_metrics.json",
  "data/processed/tag_mappings.json",
  "data/processed/unmapped_tags.log",
  "data/taxonomy/survey_2023.json",
  "data/events/reference_calendar.json",
  "state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml",
  "notebooks/02_trend_analysis.ipynb",
  "notebooks/03_decomposition.ipynb",
  "notebooks/04_clustering.ipynb"
]

def main():
    base = Path(__file__).parent
    missing = []

    print("Validating quickstart.md artifacts...")
    for rel_path in REQUIRED_FILES:
        full_path = base / rel_path
        if not full_path.exists():
            missing.append(rel_path)
        else:
            size = full_path.stat().st_size
            if size == 0:
                missing.append(f"{rel_path} (empty)")
            else:
                print(f"  [OK] {rel_path} ({size} bytes)")

    if missing:
        print("\n❌ Validation Failed. Missing or empty files:")
        for f in missing:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n✅ All artifacts verified successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()