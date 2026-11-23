import os
import yaml
from pathlib import Path
from typing import Dict, Any

def generate_inclusion_criteria() -> Dict[str, Any]:
    """
    Generates the inclusion criteria dictionary based on the logic defined in
    plan.md Phase 1.
    
    Returns:
        Dict mapping exclusion codes to their logical descriptions and regex patterns.
    """
    criteria = {
        "exclusion_codes": {
            "NO_TRUST_METRIC": {
                "description": "Study does not measure trust, trustworthiness, or credibility perception.",
                "logic": "Abstract or title must contain 'trust', 'trustworthiness', 'credibility', or 'confidence' in relation to the stimulus.",
                "keywords": ["trust", "trustworthiness", "credibility", "confidence"],
                "excluded_if_absent": True
            },
            "NO_CONTROL_CONDITION": {
                "description": "Study lacks a control condition (e.g., real faces) for comparison.",
                "logic": "Must compare deepfake/AI-generated faces against real human faces or a neutral baseline.",
                "required_comparison": ["real faces", "human faces", "original image", "baseline"],
                "excluded_if_absent": True
            },
            "NO_MODERATOR_DATA": {
                "description": "Study does not report moderator variables (e.g., realism, media literacy).",
                "logic": "Must provide data on at least one moderator variable to allow for subgroup analysis or meta-regression.",
                "required_modulators": ["realism", "media_literacy", "expertise", "age", "gender"],
                "excluded_if_absent": False # Note: T033 requires this, but T017 defines the code. T024 handles exclusion logic.
            },
            "NOT_PEER_REVIEWED": {
                "description": "Source is not a peer-reviewed publication (e.g., preprint without review, blog post).",
                "logic": "Source must be from a peer-reviewed journal or conference proceedings.",
                "allowed_sources": ["journal", "conference", "peer-reviewed"],
                "excluded_if_absent": True
            }
        },
        "inclusion_logic": {
            "must_have_trust_metric": True,
            "must_have_control": True,
            "must_be_peer_reviewed": True,
            "moderator_data_required_for_primary_pool": False,
            "moderator_data_required_for_subgroup": True
        }
    }
    return criteria

def main():
    """
    Main entry point to generate and save the inclusion criteria YAML file.
    """
    # Determine output path relative to project root
    # Assuming this script is run from the project root or code/ directory
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "data" / "screening"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "inclusion_criteria.yaml"
    
    criteria_data = generate_inclusion_criteria()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(criteria_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"Generated inclusion criteria at: {output_file}")

if __name__ == "__main__":
    main()
