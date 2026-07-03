"""
Classification module for PR origin labeling.

Implements keyword-based "Disclosing" vs "Non-Disclosing" classification.
Per Plan Override: Heuristics (formatting, comments) are ONLY for validation/covariates,
NOT for primary labeling.
"""

import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import existing logger
from data.logging_config import get_logger
from data.models import PullRequest

logger = get_logger(__name__)

# Keywords indicating AI/LLM disclosure
DISCLOSURE_KEYWORDS = [
    "copilot", "llm", "generated", "ai-generated", "ai assisted",
    "code generation", "llm generated", "github copilot", "chatgpt",
    "codex", "starcoder", "codegen", "autocomplete"
]

# Heuristic patterns for validation/covariates (NOT primary labeling)
HEURISTIC_PATTERNS = {
    "comment_ai_mention": re.compile(r'#\s*(?:ai|copilot|llm|generated)', re.IGNORECASE),
    "docstring_ai_mention": re.compile(r'("""|\'\'\')(?:.*)(?:ai|copilot|llm|generated)(?:.*)(\1)', re.IGNORECASE | re.DOTALL),
    "variable_ai_mention": re.compile(r'\b(?:ai_|llm_|copilot_)\w+', re.IGNORECASE),
    "commit_msg_ai_mention": re.compile(r'(?:ai|copilot|llm|generated)', re.IGNORECASE),
}

def load_sampled_prs(input_path: Path) -> List[Dict[str, Any]]:
    """Load the sampled PRs from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    prs = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prs.append(row)
    return prs

def check_disclosure_keywords(text: str) -> bool:
    """
    Check if text contains any disclosure keywords.
    Returns True if any keyword is found (case-insensitive).
    """
    if not text:
        return False
    text_lower = text.lower()
    for keyword in DISCLOSURE_KEYWORDS:
        if keyword in text_lower:
            return True
    return False

def calculate_heuristic_scores(pr_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate heuristic scores for validation/covariate analysis.
    These are NOT used for primary labeling per Plan Override.
    """
    scores = {
        "comment_ai_mention": 0,
        "docstring_ai_mention": 0,
        "variable_ai_mention": 0,
        "commit_msg_ai_mention": 0,
    }

    # Check title and body for comment-style mentions (simulated)
    title = pr_data.get('title', '') or ''
    body = pr_data.get('body', '') or ''
    text_content = f"{title}\n{body}"

    for pattern_name, pattern in HEURISTIC_PATTERNS.items():
        matches = pattern.findall(text_content)
        scores[pattern_name] = len(matches)

    return scores

def classify_pr(pr_data: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """
    Classify a single PR as 'Disclosing' or 'Non-Disclosing'.

    Primary classification is based on keyword presence in title/body.
    Heuristics are calculated for validation/covariate purposes only.
    """
    title = pr_data.get('title', '') or ''
    body = pr_data.get('body', '') or ''
    combined_text = f"{title} {body}"

    is_disclosing = check_disclosure_keywords(combined_text)
    origin_label = "Disclosing" if is_disclosing else "Non-Disclosing"

    # Calculate heuristics for validation/covariates (not used for labeling)
    heuristic_scores = calculate_heuristic_scores(pr_data)

    return origin_label, heuristic_scores

def apply_classification(input_path: Path, output_path: Path) -> Dict[str, int]:
    """
    Apply classification to all PRs in the input file and save results.

    Args:
        input_path: Path to sampled_prs.csv
        output_path: Path to save classified data

    Returns:
        Dictionary with classification counts
    """
    prs = load_sampled_prs(input_path)
    logger.info(f"Loaded {len(prs)} PRs from {input_path}")

    classified_prs = []
    counts = {"Disclosing": 0, "Non-Disclosing": 0}

    for pr_data in prs:
        origin_label, heuristic_scores = classify_pr(pr_data)
        counts[origin_label] += 1

        # Add classification label and heuristic scores to PR data
        pr_data['origin_label'] = origin_label
        for score_name, score_value in heuristic_scores.items():
            pr_data[f'heuristic_{score_name}'] = score_value

        classified_prs.append(pr_data)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write classified data
    if classified_prs:
        fieldnames = list(classified_prs[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(classified_prs)

    logger.info(f"Classification complete. Saved to {output_path}")
    logger.info(f"Classification counts: {counts}")

    return counts

def main():
    """Main entry point for classification task."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / "data" / "processed" / "sampled_prs.csv"
    output_path = base_dir / "data" / "processed" / "sampled_prs.csv"

    logger.info("Starting classification task T015")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T014 has been completed first.")
        return

    counts = apply_classification(input_path, output_path)

    logger.info("Classification task completed successfully")
    logger.info(f"Disclosing: {counts['Disclosing']}, Non-Disclosing: {counts['Non-Disclosing']}")

if __name__ == "__main__":
    main()