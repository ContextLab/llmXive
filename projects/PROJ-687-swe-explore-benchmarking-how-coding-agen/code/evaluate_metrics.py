import json
import os
import random
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

# Dependencies: numpy, pandas, scikit-learn, matplotlib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure output directories exist
DATA_DIR = Path("data")
FIGURES_DIR = Path("figures")
DATA_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# 1. SIMULATED REPOSITORY & ISSUES (Small Scale Proxy)
# ------------------------------------------------------------------
# We simulate a tiny repo with 3 files and 5 issues to test the evaluation logic.
# This replaces the need to clone 203 repos and run 848 agents.

SIMULATED_REPO_FILES = {
    "src/utils.py": """
def calculate_tax(amount):
    # Calculate tax for a given amount
    if amount < 0:
        return 0
    return amount * 0.2

def apply_discount(price, discount):
    # Apply discount to price
    if discount < 0 or discount > 100:
        raise ValueError("Invalid discount")
    return price * (1 - discount / 100)

def validate_email(email):
    # Simple email validation
    if '@' not in email:
        return False
    return True
""",
    "src/main.py": """
from utils import calculate_tax, apply_discount

def main():
    price = 100
    tax = calculate_tax(price)
    print(f"Total with tax: {price + tax}")
    
    # Bug: discount is applied incorrectly
    final_price = apply_discount(price, 20)
    print(f"Final price: {final_price}")

if __name__ == "__main__":
    main()
""",
    "config/settings.json": """
{
    "tax_rate": 0.2,
    "max_discount": 100,
    "debug_mode": false
}
"""
}

# Simulated Issues and their "Ground Truth" (Oracle) lines
# Format: { "path": [start_line, end_line] } (1-based, inclusive)
# We simulate that a perfect agent would identify these lines to fix the issue.
GROUNDS_TRUTH = {
    "issue_1_bug_tax_negative": {
        "src/utils.py": [2, 4] # The negative check logic
    },
    "issue_2_discount_validation": {
        "src/utils.py": [8, 10] # The validation logic
    },
    "issue_3_main_tax_call": {
        "src/main.py": [6, 6],
        "src/utils.py": [2, 6]
    },
    "issue_4_config_tax_rate": {
        "config/settings.json": [2, 2]
    },
    "issue_5_email_validation": {
        "src/utils.py": [14, 16]
    }
}

ISSUE_TEXTS = {
    "issue_1_bug_tax_negative": "Fix the issue where tax calculation returns 0 for negative amounts incorrectly.",
    "issue_2_discount_validation": "The discount validation logic is too strict, handle edge cases.",
    "issue_3_main_tax_call": "Trace how tax is calculated in the main function.",
    "issue_4_config_tax_rate": "Find the tax rate configuration.",
    "issue_5_email_validation": "Locate the email validation function."
}

# ------------------------------------------------------------------
# 2. EVALUATION LOGIC (From eval.py adapted for CPU)
# ------------------------------------------------------------------

def get_file_lines(file_content: str) -> List[str]:
    return file_content.splitlines()

def region_to_lines(region: Tuple[str, int, int], file_lines: Dict[str, List[str]]) -> Set[Tuple[str, int]]:
    """Convert a (path, start, end) region to a set of (path, line_number) tuples."""
    path, start, end = region
    lines_set = set()
    if path not in file_lines:
        return lines_set
    
    # Convert 1-based to 0-based for list access
    # Ensure bounds
    actual_start = max(0, start - 1)
    actual_end = min(len(file_lines[path]), end) # end is inclusive in 1-based, so exclusive in slice
    
    for i in range(actual_start, actual_end):
        lines_set.add((path, i + 1)) # Store as 1-based
    
    return lines_set

def regions_to_lines(regions: List[Tuple[str, int, int]], file_lines: Dict[str, List[str]]) -> Set[Tuple[str, int]]:
    all_lines = set()
    for r in regions:
        all_lines.update(region_to_lines(r, file_lines))
    return all_lines

def evaluate_metrics(pred_regions: List[Tuple[str, int, int]], gt_regions: Dict[str, List[Tuple[int, int]]], file_lines: Dict[str, List[str]]) -> Dict[str, float]:
    """
    Evaluate Precision, Recall, and nDCG.
    pred_regions: List of (path, start, end)
    gt_regions: Dict of path -> List of (start, end)
    """
    pred_lines = regions_to_lines(pred_regions, file_lines)
    
    gt_lines = set()
    for path, intervals in gt_regions.items():
        for start, end in intervals:
            gt_lines.update(region_to_lines((path, start, end), file_lines))
    
    if not pred_lines:
        precision = 0.0
    else:
        intersection = len(pred_lines & gt_lines)
        precision = intersection / len(pred_lines)
    
    if not gt_lines:
        recall = 0.0
    else:
        intersection = len(pred_lines & gt_lines)
        recall = intersection / len(gt_lines)
    
    # nDCG calculation (simplified for line-level ranking)
    # We assume the pred_regions are ranked by their order in the list.
    # We map each line in pred to a rank.
    dcg = 0.0
    idcg = 0.0
    
    # Flatten GT to a set for fast lookup
    # Calculate DCG: sum(2^rel - 1) / log2(rank + 1)
    # rel = 1 if line in GT, 0 otherwise
    
    ranked_lines = []
    for i, (path, start, end) in enumerate(pred_regions):
        # Expand region to lines
        lines = region_to_lines((path, start, end), file_lines)
        for line in lines:
            ranked_lines.append(line)
    
    for rank, line in enumerate(ranked_lines, 1):
        rel = 1.0 if line in gt_lines else 0.0
        if rel > 0:
            dcg += rel / np.log2(rank + 1)
    
    # Ideal DCG: Sort all GT lines by rank 1, 2, 3...
    ideal_lines = list(gt_lines)
    for rank in range(1, len(ideal_lines) + 1):
        idcg += 1.0 / np.log2(rank + 1)
    
    ndcg = dcg / idcg if idcg > 0 else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "ndcg": ndcg
    }

# ------------------------------------------------------------------
# 3. EXPLORER IMPLEMENTATIONS (Baselines)
# ------------------------------------------------------------------

def oracle_explorer(issue_text: str, issue_id: str) -> List[Tuple[str, int, int]]:
    """Returns the perfect ground truth regions."""
    if issue_id not in GROUNDS_TRUTH:
        return []
    gt = GROUNDS_TRUTH[issue_id]
    regions = []
    for path, intervals in gt.items():
        for start, end in intervals:
            regions.append((path, start, end))
    return regions

def random_explorer(issue_text: str, issue_id: str, all_files: Dict[str, List[str]]) -> List[Tuple[str, int, int]]:
    """Returns random regions as a baseline."""
    regions = []
    # Pick 2 random files
    paths = random.sample(list(all_files.keys()), min(2, len(all_files)))
    for path in paths:
        lines = all_files[path]
        if not lines:
            continue
        start = random.randint(1, max(1, len(lines)))
        end = random.randint(start, max(start, len(lines)))
        regions.append((path, start, end))
    return regions

def tfidf_explorer(issue_text: str, issue_id: str, all_files: Dict[str, List[str]]) -> List[Tuple[str, int, int]]:
    """
    TF-IDF baseline:
    1. Tokenize file contents.
    2. Compute TF-IDF vectors for each line (or file).
    3. Match issue text to lines.
    4. Return top-k lines as regions.
    """
    # Flatten files into (path, line_index, content)
    corpus = []
    meta = [] # (path, line_number)
    
    for path, lines in all_files.items():
        for i, line in enumerate(lines):
            corpus.append(line)
            meta.append((path, i + 1))
    
    if not corpus:
        return []

    # Vectorize
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
        query_vec = vectorizer.transform([issue_text])
        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
    except Exception:
        return [] # Fallback if TF-IDF fails
    
    # Get top-k indices
    k = 5
    top_indices = np.argsort(scores)[::-1][:k]
    
    regions = []
    # Group consecutive lines into regions
    current_path = None
    current_start = None
    current_end = None
    
    sorted_indices = sorted(top_indices, key=lambda x: meta[x][1]) # Sort by line number to form regions
    
    # Simple region formation: if lines are from same file and close, merge
    # For simplicity, we just return each top line as a 1-line region
    for idx in top_indices:
        path, line_num = meta[idx]
        if scores[idx] > 0.01: # Threshold
            regions.append((path, line_num, line_num))
            
    return regions

# ------------------------------------------------------------------
# 4. MAIN EXECUTION
# ------------------------------------------------------------------

def main():
    print("Starting SWE-Explore CPU Adaptation Evaluation...")
    
    # Prepare file lines dict
    file_lines = {path: get_file_lines(content) for path, content in SIMULATED_REPO_FILES.items()}
    
    results = []
    
    explorers = {
        "Oracle": oracle_explorer,
        "TF-IDF": tfidf_explorer,
        "Random": random_explorer
    }
    
    metrics_history = defaultdict(list)
    
    for issue_id, issue_text in ISSUE_TEXTS.items():
        print(f"Evaluating issue: {issue_id}")
        gt = GROUNDS_TRUTH.get(issue_id, {})
        
        for name, explorer_fn in explorers.items():
            # Run explorer
            if name == "Random":
                preds = explorer_fn(issue_text, issue_id, file_lines)
            else:
                preds = explorer_fn(issue_text, issue_id)
            
            # Evaluate
            metrics = evaluate_metrics(preds, gt, file_lines)
            metrics["issue_id"] = issue_id
            metrics["explorer"] = name
            results.append(metrics)
            
            print(f"  {name}: P={metrics['precision']:.2f}, R={metrics['recall']:.2f}, nDCG={metrics['ndcg']:.2f}")
    
    # Save CSV
    df = pd.DataFrame(results)
    csv_path = DATA_DIR / "evaluation_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")
    
    # Save JSON
    json_path = DATA_DIR / "evaluation_results.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved JSON to {json_path}")
    
    # Plotting
    plt.figure(figsize=(10, 6))
    explorers = ["Oracle", "TF-IDF", "Random"]
    x = np.arange(len(explorers))
    width = 0.25
    
    # Calculate averages
    avg_p = [df[df['explorer'] == e]['precision'].mean() for e in explorers]
    avg_r = [df[df['explorer'] == e]['recall'].mean() for e in explorers]
    avg_ndcg = [df[df['explorer'] == e]['ndcg'].mean() for e in explorers]
    
    plt.bar(x - width, avg_p, width, label='Precision')
    plt.bar(x, avg_r, width, label='Recall')
    plt.bar(x + width, avg_ndcg, width, label='nDCG')
    
    plt.xticks(x, explorers)
    plt.ylim(0, 1.1)
    plt.ylabel('Score')
    plt.title('SWE-Explore: Baseline Comparison (CPU Scaled)')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    fig_path = FIGURES_DIR / "comparison_scaled.png"
    plt.savefig(fig_path)
    print(f"Saved plot to {fig_path}")
    
    print("Evaluation complete.")

if __name__ == "__main__":
    main()
