"""
Metrics Collection for Preprocessing Pipeline.

Calculates 'Preprocessing Completion Rate' and logs to data/results/preprocessing_metrics.json.
Includes logic to flag 'exploratory' status if N < 20 per group (FR-010).
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config_loader import load_config, get_exclusion_dataset, get_reward_dataset

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def count_preprocessed_subjects(dataset_dir: Path, task_name: str) -> int:
    """
    Count the number of subjects that have successfully preprocessed BOLD files.
    Looks for files matching: sub-<label>/func/sub-<label>_task-<task>_space-MNI_desc-preproc_bold.nii.gz
    """
    count = 0
    subjects = set()
    
    if not dataset_dir.exists():
        logger.warning(f"Dataset directory not found: {dataset_dir}")
        return 0

    # Walk through the processed directory structure
    # Expected structure: data/processed-fmri/<dataset_id>/sub-XX/func/...
    for subject_dir in dataset_dir.glob("sub-*"):
        if not subject_dir.is_dir():
            continue
        
        func_dir = subject_dir / "func"
        if not func_dir.exists():
            continue

        # Look for preprocessed BOLD files for the specific task
        pattern = f"*task-{task_name}_*space-MNI*desc-preproc_bold.nii.gz"
        files = list(func_dir.glob(pattern))
        
        if files:
            subjects.add(subject_dir.name)
            count += 1
    
    return len(subjects)

def load_harmonized_metadata(metadata_path: Path) -> Dict[str, Any]:
    """
    Load the harmonized metadata file created by T014.
    Expected structure: JSON with 'participants' list containing group info.
    """
    if not metadata_path.exists():
        logger.error(f"Harmonized metadata file not found: {metadata_path}")
        return {"participants": []}
    
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse harmonized metadata: {e}")
        return {"participants": []}

def calculate_completion_rate(total_expected: int, processed_count: int) -> float:
    """Calculate completion rate as a percentage."""
    if total_expected == 0:
        return 0.0
    return (processed_count / total_expected) * 100.0

def generate_metrics(
    exclusion_count: int,
    reward_count: int,
    exclusion_total: int,
    reward_total: int,
    harmonized_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the metrics dictionary including completion rates and exploratory flags.
    """
    exclusion_rate = calculate_completion_rate(exclusion_total, exclusion_count)
    reward_rate = calculate_completion_rate(reward_total, reward_count)
    overall_rate = calculate_completion_rate(exclusion_total + reward_total, exclusion_count + reward_count)

    # Determine groups from harmonized data if available
    groups = {}
    if harmonized_data and "participants" in harmonized_data:
        for p in harmonized_data["participants"]:
            group = p.get("group", "unknown")
            if group not in groups:
                groups[group] = 0
            groups[group] += 1

    # Check for exploratory status (FR-010)
    is_exploratory = False
    recommendations = []
    
    # Check if any group has < 20 participants
    for group_name, count in groups.items():
        if count < 20:
            is_exploratory = True
            recommendations.append(
                f"Group '{group_name}' has N={count} (<20). "
                f"Recommend future studies with N>=30 per group for adequate power."
            )
    
    # If no groups found in metadata but we have counts, check raw counts
    if not groups:
        if exclusion_count < 20 or reward_count < 20:
            is_exploratory = True
            if exclusion_count < 20:
                recommendations.append(
                    f"Exclusion group N={exclusion_count} (<20). "
                    "Recommend future studies with N>=30."
                )
            if reward_count < 20:
                recommendations.append(
                    f"Reward group N={reward_count} (<20). "
                    "Recommend future studies with N>=30."
                )

    metrics = {
        "preprocessing_completion": {
            "exclusion_dataset": {
                "processed_subjects": exclusion_count,
                "expected_subjects": exclusion_total,
                "completion_rate_percent": round(exclusion_rate, 2)
            },
            "reward_dataset": {
                "processed_subjects": reward_count,
                "expected_subjects": reward_total,
                "completion_rate_percent": round(reward_rate, 2)
            },
            "overall": {
                "processed_subjects": exclusion_count + reward_count,
                "expected_subjects": exclusion_total + reward_total,
                "completion_rate_percent": round(overall_rate, 2)
            }
        },
        "target_met": overall_rate >= 90.0,
        "group_counts": groups,
        "exploratory_status": is_exploratory,
        "recommendations": recommendations,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    return metrics

def main():
    """Main entry point for metrics collection."""
    logger.info("Starting preprocessing metrics collection...")

    # Load configuration
    config_path = PROJECT_ROOT / "code" / "config" / "project_config.yaml"
    if not config_path.exists():
        # Fallback to default if config not found, though T007 should have created it
        logger.warning("Config not found, using defaults for dataset IDs.")
        exclusion_id = "ds000246"
        reward_id = "ds004738"
    else:
        config = load_config(config_path)
        exclusion_id = get_exclusion_dataset(config)["dataset_id"]
        reward_id = get_reward_dataset(config)["dataset_id"]

    # Define paths
    processed_dir = PROJECT_ROOT / "data" / "processed-fmri"
    metadata_path = PROJECT_ROOT / "data" / "results" / "harmonized_metadata.json"
    output_path = PROJECT_ROOT / "data" / "results" / "preprocessing_metrics.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Count preprocessed subjects
    # Exclusion dataset (Social Exclusion task)
    exclusion_dir = processed_dir / exclusion_id
    exclusion_count = count_preprocessed_subjects(exclusion_dir, "social_exclusion")
    
    # Reward dataset (Reward task)
    reward_dir = processed_dir / reward_id
    reward_count = count_preprocessed_subjects(reward_dir, "reward")

    # Estimate total expected subjects (approximate based on typical OpenNeuro sizes or config)
    # In a real scenario, this would come from the raw dataset manifest or config
    exclusion_total = 100  # Placeholder, ideally read from raw dataset
    reward_total = 100     # Placeholder, ideally read from raw dataset

    # Load harmonized metadata to get actual group counts
    harmonized_data = load_harmonized_metadata(metadata_path)

    # Generate metrics
    metrics = generate_metrics(
        exclusion_count=exclusion_count,
        reward_count=reward_count,
        exclusion_total=exclusion_total,
        reward_total=reward_total,
        harmonized_data=harmonized_data
    )

    # Write to disk
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics written to {output_path}")
    logger.info(f"Overall Completion Rate: {metrics['preprocessing_completion']['overall']['completion_rate_percent']}%")
    logger.info(f"Target (>=90%) Met: {metrics['target_met']}")
    logger.info(f"Exploratory Status: {metrics['exploratory_status']}")
    
    if metrics['recommendations']:
        for rec in metrics['recommendations']:
            logger.warning(f"Recommendation: {rec}")

    return metrics

if __name__ == "__main__":
    from datetime import datetime, timezone
    main()
