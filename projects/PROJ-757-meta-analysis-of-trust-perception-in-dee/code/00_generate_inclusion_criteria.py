"""
Task T017: Generate data/screening/inclusion_criteria.yaml programmatically.

This script defines the exclusion logic based on Phase 1 of the project plan
and writes it to the required YAML file.
"""
import os
import yaml
from pathlib import Path

def generate_inclusion_criteria():
    """
    Constructs the inclusion criteria dictionary mapping exclusion codes
    to their specific logic definitions as per plan.md Phase 1.
    """
    criteria = {
        "exclusion_codes": {
            "NO_TRUST_METRIC": {
                "description": "Study does not measure trust or trustworthiness explicitly.",
                "logic": "Check abstract and methods for keywords: 'trust', 'trustworthiness', 'confidence', 'reliability perception'. If absent, flag."
            },
            "NO_CONTROL_CONDITION": {
                "description": "Study lacks a control condition (e.g., real faces) for comparison.",
                "logic": "Verify presence of a control group using authentic/non-deepfake facial stimuli. If only deepfake stimuli are presented without comparison, flag."
            },
            "NO_MODERATOR_DATA": {
                "description": "Study does not report necessary moderator variables (e.g., realism, media literacy).",
                "logic": "Check if study reports data for moderators required in Phase 3 (e.g., 'realism', 'media-literacy'). If data is missing, flag."
            },
            "NOT_PEER_REVIEWED": {
                "description": "Source is not a peer-reviewed publication.",
                "logic": "Filter out pre-prints (unless archived in a recognized repository with review status), conference abstracts without full text, or non-academic sources."
            }
        },
        "metadata": {
            "version": "1.0",
            "generated_by": "code/00_generate_inclusion_criteria.py",
            "source": "plan.md Phase 1"
        }
    }
    return criteria

def main():
    # Ensure the target directory exists
    output_dir = Path("data/screening")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "inclusion_criteria.yaml"

    criteria = generate_inclusion_criteria()

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            criteria,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True
        )

    print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    main()
