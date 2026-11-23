import json
import os
from pathlib import Path
from typing import Dict, Any, List

def generate_synthetic_binding_data(output_path: str) -> Dict[str, Any]:
    """
    Generates a synthetic dataset for testing feature binding visualization.
    Creates tokens explicitly tagged as 'color' or 'motion' to demonstrate
    how attention weights shift under oscillation vs baseline.
    
    Args:
        output_path: Path where the JSON file will be saved
        
    Returns:
        The generated data dictionary
    """
    # Ensure directory exists
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define synthetic data with explicit feature tags
    # This creates a controlled scenario where we know which tokens
    # represent 'color' features and which represent 'motion' features
    data = {
        "metadata": {
            "description": "Synthetic dataset for feature binding visualization",
            "feature_types": ["color", "motion"],
            "sequence_length": 16,
            "purpose": "Demonstrate attention weight shifts for tagged features"
        },
        "sequences": [
            {
                "id": "seq_001",
                "text": "The red ball moves quickly",
                "tokens": [
                    {"token": "The", "pos": 0, "feature_tag": "context"},
                    {"token": "red", "pos": 1, "feature_tag": "color"},
                    {"token": "ball", "pos": 2, "feature_tag": "object"},
                    {"token": "moves", "pos": 3, "feature_tag": "motion"},
                    {"token": "quickly", "pos": 4, "feature_tag": "motion"},
                    {"token": ".", "pos": 5, "feature_tag": "context"}
                ],
                "feature_pairs": [
                    {"color_token": "red", "motion_token": "moves", "expected_binding": True},
                    {"color_token": "red", "motion_token": "quickly", "expected_binding": True}
                ]
            },
            {
                "id": "seq_002",
                "text": "Blue car speeds fast",
                "tokens": [
                    {"token": "Blue", "pos": 0, "feature_tag": "color"},
                    {"token": "car", "pos": 1, "feature_tag": "object"},
                    {"token": "speeds", "pos": 2, "feature_tag": "motion"},
                    {"token": "fast", "pos": 3, "feature_tag": "motion"},
                    {"token": ".", "pos": 4, "feature_tag": "context"}
                ],
                "feature_pairs": [
                    {"color_token": "Blue", "motion_token": "speeds", "expected_binding": True},
                    {"color_token": "Blue", "motion_token": "fast", "expected_binding": True}
                ]
            },
            {
                "id": "seq_003",
                "text": "Green leaf falls slowly",
                "tokens": [
                    {"token": "Green", "pos": 0, "feature_tag": "color"},
                    {"token": "leaf", "pos": 1, "feature_tag": "object"},
                    {"token": "falls", "pos": 2, "feature_tag": "motion"},
                    {"token": "slowly", "pos": 3, "feature_tag": "motion"},
                    {"token": ".", "pos": 4, "feature_tag": "context"}
                ],
                "feature_pairs": [
                    {"color_token": "Green", "motion_token": "falls", "expected_binding": True},
                    {"color_token": "Green", "motion_token": "slowly", "expected_binding": True}
                ]
            },
            {
                "id": "seq_004",
                "text": "Yellow sun rises slowly",
                "tokens": [
                    {"token": "Yellow", "pos": 0, "feature_tag": "color"},
                    {"token": "sun", "pos": 1, "feature_tag": "object"},
                    {"token": "rises", "pos": 2, "feature_tag": "motion"},
                    {"token": "slowly", "pos": 3, "feature_tag": "motion"},
                    {"token": ".", "pos": 4, "feature_tag": "context"}
                ],
                "feature_pairs": [
                    {"color_token": "Yellow", "motion_token": "rises", "expected_binding": True},
                    {"color_token": "Yellow", "motion_token": "slowly", "expected_binding": True}
                ]
            }
        ],
        "analysis_config": {
            "target_feature_types": ["color", "motion"],
            "binding_threshold": 0.3,
            "visualization_focus": "attention_weight_differences"
        }
    }
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

if __name__ == "__main__":
    output_path = "data/synthetic/color_motion.json"
    data = generate_synthetic_binding_data(output_path)
    print(f"Generated synthetic binding data at {output_path}")
    print(f"Created {len(data['sequences'])} sequences with color/motion feature pairs")
