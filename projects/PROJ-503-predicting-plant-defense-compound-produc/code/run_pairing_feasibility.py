import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set

# Import from local project modules
from code.exceptions import E_PAIRING, raise_pairing_error
from code.logging_utils import log_data_pairing_mismatches_batch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('projects/PROJ-503-predicting-plant-defense-compound-produc/logs/pairing_feasibility.log')
    ]
)
logger = logging.getLogger(__name__)

def load_json_safe(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file safely, returning an empty dict if file is missing or invalid."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return {}

def load_geo_search_results(project_root: Path) -> Dict[str, Any]:
    """Load GEO search results from the project's data directory."""
    # Assuming T011/T012 produced these files
    geo_arabidopsis_path = project_root / "data" / "raw" / "geo_arabidopsis_search.json"
    geo_solanum_path = project_root / "data" / "raw" / "geo_solanum_search.json"
    
    geo_data = {}
    if geo_arabidopsis_path.exists():
        geo_data['arabidopsis'] = load_json_safe(geo_arabidopsis_path)
    if geo_solanum_path.exists():
        geo_data['solanum'] = load_json_safe(geo_solanum_path)
    
    return geo_data

def load_mw_search_results(project_root: Path) -> Dict[str, Any]:
    """Load Metabolomics Workbench search results from the project's data directory."""
    mw_path = project_root / "data" / "raw" / "metabolomics_workbench_search.json"
    return load_json_safe(mw_path)

def extract_geo_biosample_ids(geo_data: Dict[str, Any]) -> Set[str]:
    """Extract unique biosample IDs from GEO search results."""
    biosample_ids = set()
    for species, data in geo_data.items():
        if not data:
            continue
        # Assuming structure: { "results": [ { "accession": "GSE...", "samples": [ { "biosample_id": "..." } ] } ] }
        # or similar structure based on T011/T012 output
        results = data.get("results", [])
        if isinstance(results, list):
            for item in results:
                samples = item.get("samples", [])
                if isinstance(samples, list):
                    for sample in samples:
                        if "biosample_id" in sample:
                            biosample_ids.add(sample["biosample_id"])
                        # Fallback if biosample_id is nested or named differently
                        elif "sample_id" in sample:
                            biosample_ids.add(sample["sample_id"])
    return biosample_ids

def extract_mw_biosample_ids(mw_data: Dict[str, Any]) -> Set[str]:
    """Extract unique biosample IDs from Metabolomics Workbench search results."""
    biosample_ids = set()
    if not mw_data:
        return biosample_ids
    
    # Assuming structure: { "experiments": [ { "samples": [ { "biosample_id": "..." } ] } ] }
    experiments = mw_data.get("experiments", [])
    if isinstance(experiments, list):
        for exp in experiments:
            samples = exp.get("samples", [])
            if isinstance(samples, list):
                for sample in samples:
                    if "biosample_id" in sample:
                        biosample_ids.add(sample["biosample_id"])
                    elif "sample_id" in sample:
                        biosample_ids.add(sample["sample_id"])
    return biosample_ids

def run_pairing_feasibility(project_root: Path) -> Dict[str, Any]:
    """
    Verify sample-level pairing feasibility.
    Compares biosample IDs from GEO (expression) and Metabolomics Workbench (metabolites).
    Calculates pairing rate.
    
    Returns:
        Dict with pairing_rate, total_samples, matched_samples, unmatched_samples
    """
    logger.info("Starting pairing feasibility analysis...")
    
    geo_data = load_geo_search_results(project_root)
    mw_data = load_mw_search_results(project_root)
    
    if not geo_data and not mw_data:
        logger.error("No data found for pairing analysis. Ensure T011, T012, T013 have run.")
        raise_pairing_error("No data found for pairing analysis.", "T014")
    
    geo_biosample_ids = extract_geo_biosample_ids(geo_data)
    mw_biosample_ids = extract_mw_biosample_ids(mw_data)
    
    total_expression_samples = len(geo_biosample_ids)
    total_metabolite_samples = len(mw_biosample_ids)
    
    if total_expression_samples == 0 and total_metabolite_samples == 0:
        logger.warning("No samples found in either GEO or MW data.")
        return {
            "pairing_rate": 0.0,
            "total_samples": 0,
            "matched_samples": 0,
            "unmatched_samples": 0,
            "geo_samples": 0,
            "mw_samples": 0,
            "status": "NO_DATA"
        }
    
    # Total unique samples across both sources for pairing calculation
    # We consider the union of all samples as the population we want to pair
    all_samples = geo_biosample_ids.union(mw_biosample_ids)
    total_samples = len(all_samples)
    
    # Matched samples are those present in BOTH sets
    matched_samples = geo_biosample_ids.intersection(mw_biosample_ids)
    matched_count = len(matched_samples)
    
    # Unmatched are those in one but not the other
    unmatched_samples = all_samples - matched_samples
    unmatched_count = len(unmatched_samples)
    
    # Calculate pairing rate: matched / total unique samples
    # Or alternatively: matched / min(geo, mw) if we want to see how many of the smaller set are covered
    # The spec says ">=95% match rate". Usually this means (matched / total_expression) or (matched / total_mw)
    # Let's use the more conservative: matched / total_expression (assuming expression is the primary)
    # But the spec says "total_samples" in output. Let's define pairing_rate as matched / total_samples (union)
    # Wait, usually pairing rate is (matched pairs) / (total samples in one dataset).
    # Let's calculate rate relative to the expression dataset (GEO) as that's often the constraint.
    if total_expression_samples > 0:
        pairing_rate_geo = matched_count / total_expression_samples
    else:
        pairing_rate_geo = 0.0
        
    if total_metabolite_samples > 0:
        pairing_rate_mw = matched_count / total_metabolite_samples
    else:
        pairing_rate_mw = 0.0
    
    # Use the minimum of the two rates as the conservative estimate, or the rate relative to the union?
    # The task says "total_samples" in output. Let's use the union as total_samples.
    # And pairing_rate as matched / total_samples (union).
    if total_samples > 0:
        pairing_rate = matched_count / total_samples
    else:
        pairing_rate = 0.0
    
    result = {
        "pairing_rate": pairing_rate,
        "total_samples": total_samples,
        "matched_samples": matched_count,
        "unmatched_samples": unmatched_count,
        "geo_samples": total_expression_samples,
        "mw_samples": total_metabolite_samples,
        "pairing_rate_geo": pairing_rate_geo,
        "pairing_rate_mw": pairing_rate_mw,
        "matched_ids": list(matched_samples),
        "unmatched_ids": list(unmatched_samples),
        "status": "OK" if pairing_rate >= 0.95 else "FAILED"
    }
    
    logger.info(f"Pairing Analysis Results:")
    logger.info(f"  Total Samples (Union): {total_samples}")
    logger.info(f"  Matched Samples: {matched_count}")
    logger.info(f"  Unmatched Samples: {unmatched_count}")
    logger.info(f"  Pairing Rate: {pairing_rate:.4f}")
    
    # Log unmatched samples for debugging
    if unmatched_count > 0:
        logger.warning(f"Found {unmatched_count} unmatched samples. Logging to data_pairing.json...")
        # Prepare log data
        mismatch_logs = []
        for uid in unmatched_samples:
            reason = "no_sample_level_pair"
            if uid in geo_biosample_ids:
                source = "geo"
            else:
                source = "mw"
            mismatch_logs.append({
                "sample_id": uid,
                "expression_source": "geo" if uid in geo_biosample_ids else None,
                "metabolite_source": "mw" if uid in mw_biosample_ids else None,
                "reason": reason
            })
        log_data_pairing_mismatches_batch(mismatch_logs, project_root / "logs" / "data_pairing.json")
    
    return result

def main():
    project_root = Path("projects/PROJ-503-predicting-plant-defense-compound-produc")
    output_path = project_root / "logs" / "pairing_feasibility.json"
    
    try:
        result = run_pairing_feasibility(project_root)
        
        # Write result to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Pairing feasibility report written to {output_path}")
        
        # Check abort condition
        if result["pairing_rate"] < 0.95:
            logger.error(f"Pairing rate {result['pairing_rate']:.4f} is below 0.95 threshold. ABORTING with E-PAIRING.")
            raise_pairing_error(
                f"Pairing rate {result['pairing_rate']:.4f} < 0.95",
                "T014"
            )
        else:
            logger.info(f"Pairing rate {result['pairing_rate']:.4f} >= 0.95. Proceeding.")
            
    except E_PAIRING:
        # Re-raise to be caught by main.py or execution layer
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during pairing feasibility check: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
