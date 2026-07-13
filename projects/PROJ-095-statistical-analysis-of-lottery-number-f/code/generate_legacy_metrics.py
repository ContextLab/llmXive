"""
Generate the legacy metrics JSON file documenting the rejection of
the invalid Chi-Square metric per FR-002.
"""
import json
import os
import sys

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

def main():
    """
    Creates data/processed/legacy_metrics.json with static content
    documenting the rejection of the invalid Chi-Square metric.
    """
    output_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "legacy_metrics.json")

    legacy_metrics = {
        "is_legacy": True,
        "reason": "Chi-Square invalid for n=6; replaced by per-draw metrics",
        "metric_replaced": "draw_uniformity_deviation",
        "replacement": "birthday_cluster_ratio, consecutive_pattern_count"
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(legacy_metrics, f, indent=2)

    print(f"Successfully created {output_path}")

if __name__ == "__main__":
    main()
