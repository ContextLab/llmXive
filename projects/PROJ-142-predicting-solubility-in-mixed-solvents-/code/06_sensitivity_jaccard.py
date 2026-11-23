"""
T033: Calculate Jaccard similarity between top-5 term sets at different thresholds.

Reads sensitivity analysis results (shap_ranking.json) which contains top-5 interaction
terms identified at low, medium, and high thresholds. Calculates Jaccard similarity
between these sets to verify stability per SC-004 (target >= 0.6).

Output: Appends metrics to data/artifacts/shap_ranking.json
"""
import os
import json
import sys
from pathlib import Path
from typing import List, Set, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
SHAP_RANKING_PATH = ARTIFACTS_DIR / "shap_ranking.json"


def load_shap_ranking() -> Dict[str, Any]:
    """Load the existing shap_ranking.json file."""
    if not SHAP_RANKING_PATH.exists():
        raise FileNotFoundError(
            f"Required input file not found: {SHAP_RANKING_PATH}. "
            "Ensure T032 (sensitivity analysis) has been completed first."
        )
    
    with open(SHAP_RANKING_PATH, 'r') as f:
        return json.load(f)


def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Calculate Jaccard similarity between two sets.
    
    Jaccard = |Intersection| / |Union|
    Returns 0.0 if both sets are empty to avoid division by zero.
    """
    if not set1 and not set2:
        return 0.0
    
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def extract_top5_terms(threshold_data: Dict[str, Any]) -> Set[str]:
    """
    Extract the top 5 interaction terms from a threshold's data.
    
    Expected structure in threshold_data:
    {
        "threshold": "low|medium|high",
        "top_terms": [
            {"rank": 1, "feature": "term_name", ...},
            ...
        ]
    }
    """
    terms = set()
    top_terms_list = threshold_data.get("top_terms", [])
    
    for item in top_terms_list[:5]:  # Ensure we only take top 5
        feature_name = item.get("feature")
        if feature_name:
            terms.add(feature_name)
    
    return terms


def main():
    """
    Main execution function for T033.
    
    1. Load shap_ranking.json
    2. Extract top-5 term sets for low, medium, high thresholds
    3. Calculate Jaccard similarity between:
       - Low vs Medium
       - Medium vs High
       - Low vs High
    4. Calculate average Jaccard similarity
    5. Append results to shap_ranking.json
    6. Verify against SC-004 target (>= 0.6)
    """
    print("T033: Starting Jaccard similarity calculation for sensitivity analysis...")
    
    # Load existing ranking data
    try:
        ranking_data = load_shap_ranking()
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Verify expected structure
    sensitivity_results = ranking_data.get("sensitivity_analysis", {})
    if not sensitivity_results:
        print(
            "ERROR: sensitivity_analysis section not found in shap_ranking.json. "
            "Ensure T032 has populated this section.",
            file=sys.stderr
        )
        sys.exit(1)
    
    # Extract thresholds (expecting low, medium, high)
    thresholds = ["low", "medium", "high"]
    term_sets = {}
    
    for threshold in thresholds:
        if threshold not in sensitivity_results:
            print(
                f"WARNING: Threshold '{threshold}' not found in sensitivity_analysis. "
                f"Available keys: {list(sensitivity_results.keys())}",
                file=sys.stderr
            )
            continue
        
        term_sets[threshold] = extract_top5_terms(sensitivity_results[threshold])
    
    # Ensure we have at least two sets to compare
    if len(term_sets) < 2:
        print(
            "ERROR: Insufficient threshold data to calculate Jaccard similarity. "
            f"Need at least 2 thresholds, found {len(term_sets)}.",
            file=sys.stderr
        )
        sys.exit(1)
    
    # Calculate pairwise Jaccard similarities
    jaccard_results = {}
    comparisons = []
    
    threshold_list = list(term_sets.keys())
    for i in range(len(threshold_list)):
        for j in range(i + 1, len(threshold_list)):
            t1, t2 = threshold_list[i], threshold_list[j]
            set1, set2 = term_sets[t1], term_sets[t2]
            
            jaccard_score = calculate_jaccard_similarity(set1, set2)
            key = f"{t1}_vs_{t2}"
            jaccard_results[key] = jaccard_score
            comparisons.append(jaccard_score)
            
            print(f"  Jaccard({t1}, {t2}) = {jaccard_score:.4f} "
                  f"(Set1: {len(set1)} terms, Set2: {len(set2)} terms)")
    
    # Calculate average Jaccard similarity
    avg_jaccard = sum(comparisons) / len(comparisons) if comparisons else 0.0
    
    # Determine pass/fail against SC-004 target
    sc004_target = 0.6
    status = "PASS" if avg_jaccard >= sc004_target else "FAIL"
    reason = f"Average Jaccard similarity {avg_jaccard:.4f} {'meets' if status == 'PASS' else 'does not meet'} target of {sc004_target}"
    
    # Prepare results object
    jaccard_analysis = {
        "pairwise_similarities": jaccard_results,
        "average_jaccard_similarity": avg_jaccard,
        "sc004_target": sc004_target,
        "status": status,
        "reason": reason,
        "thresholds_analyzed": list(term_sets.keys()),
        "term_counts": {k: len(v) for k, v in term_sets.items()}
    }
    
    # Append to ranking data
    ranking_data["jaccard_sensitivity_analysis"] = jaccard_analysis
    
    # Write back to file
    try:
        with open(SHAP_RANKING_PATH, 'w') as f:
            json.dump(ranking_data, f, indent=2)
        print(f"\nT033: Successfully updated {SHAP_RANKING_PATH}")
        print(f"  Average Jaccard Similarity: {avg_jaccard:.4f}")
        print(f"  SC-004 Status: {status} ({reason})")
    except IOError as e:
        print(f"ERROR: Failed to write results to {SHAP_RANKING_PATH}: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Exit with appropriate code based on SC-004 status
    if status == "FAIL":
        print(f"\nWARNING: SC-004 stability threshold not met. Proceed with caution.", file=sys.stderr)
        sys.exit(0)  # Exit 0 to allow pipeline to continue to next task
    
    sys.exit(0)


if __name__ == "__main__":
    main()
