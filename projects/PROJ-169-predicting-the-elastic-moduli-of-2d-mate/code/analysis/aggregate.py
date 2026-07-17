import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.logger import get_logger

logger = get_logger(__name__)

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_shap_values(path: Path) -> Dict[str, Any]:
    """Load SHAP values from the importance analysis output."""
    logger.info(f"Loading SHAP values from {path}")
    data = load_json_file(path)
    # Ensure structure exists, normalize if necessary
    if "shap_values" not in data:
        raise ValueError(f"SHAP file {path} missing 'shap_values' key")
    return data

def load_permutation_importance(path: Path) -> Dict[str, Any]:
    """Load permutation importance from the importance analysis output."""
    logger.info(f"Loading permutation importance from {path}")
    data = load_json_file(path)
    if "permutation_importance" not in data:
        raise ValueError(f"Permutation file {path} missing 'permutation_importance' key")
    return data

def load_generalization_metrics(path: Path) -> Dict[str, Any]:
    """Load generalization metrics (inter/intra family drop)."""
    logger.info(f"Loading generalization metrics from {path}")
    data = load_json_file(path)
    required_keys = ["intra_family_mape", "inter_family_mape", "drop_percentage"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Generalization file {path} missing required key: {key}")
    return data

def aggregate_metrics(
    shap_data: Dict[str, Any],
    perm_data: Dict[str, Any],
    gen_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine SHAP, permutation, and generalization metrics into a single
    intermediate JSON structure for the report generator.
    """
    logger.info("Aggregating metrics into intermediate JSON structure")

    # Extract SHAP summary if available
    shap_summary = shap_data.get("shap_values", {})
    # Extract permutation summary
    perm_summary = perm_data.get("permutation_importance", [])

    # Construct the unified intermediate object
    aggregated = {
        "metadata": {
            "source": "T027a_aggregate.py",
            "description": "Intermediate aggregation of SHAP, Permutation, and Generalization metrics",
            "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
        },
        "shap_analysis": shap_summary,
        "permutation_analysis": perm_summary,
        "generalization_metrics": {
            "intra_family_mape": gen_data["intra_family_mape"],
            "inter_family_mape": gen_data["inter_family_mape"],
            "drop_percentage": gen_data["drop_percentage"]
        },
        "unified_descriptor_scores": []
    }

    # Merge SHAP and Permutation scores into a unified list for ranking
    # Assuming SHAP summary is a dict of {descriptor: score} and perm is a list of dicts
    # We normalize keys to 'descriptor' and 'score'
    
    seen_descriptors = set()
    
    # Process SHAP values
    if isinstance(shap_summary, dict):
        for desc, score in shap_summary.items():
            if desc not in seen_descriptors:
                aggregated["unified_descriptor_scores"].append({
                    "descriptor": desc,
                    "shap_score": score,
                    "perm_score": None,
                    "source": "shap"
                })
                seen_descriptors.add(desc)

    # Process Permutation values
    if isinstance(perm_summary, list):
        for item in perm_summary:
            desc = item.get("feature") or item.get("descriptor")
            score = item.get("score")
            if desc and desc not in seen_descriptors:
                aggregated["unified_descriptor_scores"].append({
                    "descriptor": desc,
                    "shap_score": None,
                    "perm_score": score,
                    "source": "permutation"
                })
                seen_descriptors.add(desc)
            elif desc:
                # Update existing entry if descriptor found in both
                for entry in aggregated["unified_descriptor_scores"]:
                    if entry["descriptor"] == desc:
                        entry["perm_score"] = score
                        entry["source"] = "combined"
                        break

    logger.info(f"Aggregation complete. Total descriptors: {len(aggregated['unified_descriptor_scores'])}")
    return aggregated

def run_aggregation(
    shap_path: Path,
    perm_path: Path,
    gen_path: Path,
    output_path: Path
) -> None:
    """
    Run the full aggregation pipeline:
    1. Load SHAP, Permutation, and Generalization JSONs.
    2. Merge into a unified intermediate structure.
    3. Save to the specified output path.
    """
    logger.info(f"Starting aggregation pipeline")
    logger.info(f"Inputs: SHAP={shap_path}, Perm={perm_path}, Gen={gen_path}")
    logger.info(f"Output: {output_path}")

    shap_data = load_shap_values(shap_path)
    perm_data = load_permutation_importance(perm_path)
    gen_data = load_generalization_metrics(gen_path)

    aggregated = aggregate_metrics(shap_data, perm_data, gen_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated, f, indent=2)

    logger.info(f"Aggregated metrics saved to {output_path}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate SHAP, Permutation, and Generalization metrics")
    parser.add_argument("--shap-input", type=str, required=True, help="Path to SHAP values JSON")
    parser.add_argument("--perm-input", type=str, required=True, help="Path to Permutation Importance JSON")
    parser.add_argument("--gen-input", type=str, required=True, help="Path to Generalization Metrics JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output aggregated JSON")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    run_aggregation(
        shap_path=Path(args.shap_input),
        perm_path=Path(args.perm_input),
        gen_path=Path(args.gen_input),
        output_path=Path(args.output)
    )

if __name__ == "__main__":
    main()