import csv
import json
import logging
import random
from collections import defaultdict
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def load_processed_data(filepath: str) -> List[Dict[str, Any]]:
    """Load processed PR data."""
    with open(filepath, 'r') as f:
        return json.load(f)

def stratify_data(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Stratify data by repo and PR size (simulated by commit count)."""
    buckets = defaultdict(list)
    for pr in data:
        # Simulate PR size by number of commit messages
        size_bucket = "small" if len(pr.get('commit_messages', [])) < 5 else "large"
        key = f"{pr['repo_name']}_{size_bucket}"
        buckets[key].append(pr)
    return dict(buckets)

def perform_stratified_sampling(strata: Dict[str, List[Dict[str, Any]]], n: int = 50) -> List[Dict[str, Any]]:
    """Perform stratified random sampling."""
    sample = []
    total_size = sum(len(v) for v in strata.values())
    if total_size == 0:
        return []
    
    # Proportional allocation
    for key, items in strata.items():
        proportion = len(items) / total_size
        n_stratum = max(1, int(n * proportion))
        sample.extend(random.sample(items, min(n_stratum, len(items))))
    
    return sample

def simulate_manual_review(prs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Simulate manual review to detect false negatives.
    In a real scenario, this would involve human review.
    Here we simulate based on heuristic re-evaluation.
    """
    results = []
    for pr in prs:
        # Simulate: if it's marked non-AI but has "copilot" in any message, it's a FN
        is_false_negative = False
        if not pr['is_ai']:
            for msg in pr.get('commit_messages', []):
                if "copilot" in msg.lower() or "ai-generated" in msg.lower():
                    is_false_negative = True
                    break
        
        results.append({
            "pr_id": pr['pr_id'],
            "repo_name": pr['repo_name'],
            "original_label": "AI" if pr['is_ai'] else "Human",
            "reviewed_label": "AI" if is_false_negative or pr['is_ai'] else "Human",
            "is_false_negative": is_false_negative
        })
    return results

def calculate_false_negative_rate(results: List[Dict[str, Any]]) -> float:
    """Calculate false negative rate from review results."""
    non_ai_count = sum(1 for r in results if r['original_label'] == "Human")
    if non_ai_count == 0:
        return 0.0
    fn_count = sum(1 for r in results if r['is_false_negative'])
    return fn_count / non_ai_count

def save_validation_report(results: List[Dict[str, Any]], output_path: str):
    """Save validation report to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

def main():
    """Main entry point for spot check validation."""
    logging.basicConfig(level=logging.INFO)
    
    data = load_processed_data("data/processed/pr_data.json")
    strata = stratify_data(data)
    sample = perform_stratified_sampling(strata, n=50)
    
    logger.info(f"Sampled {len(sample)} PRs for validation.")
    
    results = simulate_manual_review(sample)
    fn_rate = calculate_false_negative_rate(results)
    logger.info(f"Estimated false negative rate: {fn_rate:.2%}")
    
    save_validation_report(results, "data/spot_check/validation_report.csv")

if __name__ == "__main__":
    main()
