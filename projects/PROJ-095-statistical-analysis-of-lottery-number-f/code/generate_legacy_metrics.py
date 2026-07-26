"""
Generate legacy_metrics.json to document the rejection of invalid Chi-Square metrics.

This script creates a static JSON file explicitly documenting the rejection of the
scientifically invalid per-draw Chi-Square metric (draw_uniformity_deviation) as per
FR-002 and the Plan resolution. It replaces it with valid per-draw metrics:
birthday_cluster_ratio and consecutive_pattern_count.
"""
import json
import os
import sys

# Ensure the output directory exists
OUTPUT_DIR = "data/processed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "legacy_metrics.json")

LEGACY_METRICS_DATA = {
    "is_legacy": True,
    "reason": "Chi-Square invalid for n=6; replaced by per-draw metrics",
    "metric_replaced": "draw_uniformity_deviation",
    "replacement": "birthday_cluster_ratio, consecutive_pattern_count"
}

def main():
    """Generate the legacy_metrics.json file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Write the static content to the file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(LEGACY_METRICS_DATA, f, indent=2)
        
        print(f"Successfully generated {OUTPUT_FILE}")
        return 0
        
    except IOError as e:
        print(f"Error writing file {OUTPUT_FILE}: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
