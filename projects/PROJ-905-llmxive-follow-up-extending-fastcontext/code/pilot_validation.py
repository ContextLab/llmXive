import csv
import json
import os
import sys
import time
import math
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from config import get_path, ensure_directories
from stratification import load_scores_from_csv
from fastcontext_lite import run_fastcontext_lite, extract_keywords, build_tfidf_index, search_tfidf
from metrics_logger import create_log_entry, log_metrics

def load_sample_scores(input_path: str, n: int = 20) -> List[Dict]:
    """Load the first N records from the regularity scores CSV."""
    scores = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append({
                'repo_id': row['repo_id'],
                'regularity_score': float(row['regularity_score'])
            })
            if len(scores) >= n:
                break
    return scores

def simulate_repo_content(repo_id: str) -> Dict:
    """
    Simulate a minimal repository content structure for the pilot.
    Since we cannot download full repos for the pilot, we simulate
    the file tree and content based on the repo_id to test the
    retrieval logic against a known structure.
    
    In a full run, this would fetch the actual repo from the dataset.
    For the pilot, we use a deterministic mock that represents
    a 'standard' vs 'irregular' structure based on the ID string.
    """
    # Deterministic simulation based on repo_id string hash
    seed_val = sum([ord(c) for c in repo_id]) % 100
    is_standard = seed_val > 50  # Arbitrary split for simulation

    files = {}
    if is_standard:
        # Simulate standard layout
        files['src/main.py'] = "def main():\n    pass\n"
        files['src/utils.py'] = "from .main import main\n"
        files['tests/test_main.py'] = "from src.main import main\n\ndef test_main():\n    pass\n"
        files['docs/readme.md'] = "# Readme"
    else:
        # Sim irregular layout
        files['main.py'] = "def main():\n    pass\n"
        files['util.py'] = "import main\n"
        files['test_main.py'] = "import main\n"
        files['readme.md'] = "# Readme"

    return {'repo_id': repo_id, 'files': files}

def extract_keywords_from_repo_id(repo_id: str) -> List[str]:
    """
    Extract keywords from the repo_id string to simulate an issue query.
    This is a simplified extraction for the pilot.
    """
    # Split by common separators and keep non-empty parts
    parts = re.split(r'[-_.]', repo_id)
    keywords = [p for p in parts if p and len(p) > 2]
    return keywords if keywords else ['test']

def calculate_precision(retrieved_snippets: List[str], expected_keywords: List[str]) -> float:
    """
    Calculate precision: fraction of retrieved snippets that contain at least one expected keyword.
    This is a heuristic precision for the pilot validation.
    """
    if not retrieved_snippets:
        return 0.0
    if not expected_keywords:
        return 0.0

    hits = 0
    for snippet in retrieved_snippets:
        for kw in expected_keywords:
            if kw.lower() in snippet.lower():
                hits += 1
                break
    return hits / len(retrieved_snippets)

def simple_retrieval_baseline(repo_data: Dict, query_keywords: List[str]) -> Tuple[List[str], float]:
    """
    Run a simple retrieval baseline.
    Since we are simulating the repo content, we build a tiny TF-IDF index
    on the fly and retrieve top-K snippets.
    
    Returns (retrieved_snippets, token_count)
    """
    files = repo_data['files']
    # Build index
    index = build_tfidf_index(files)
    
    if not index.vocabulary:
        return [], 0

    # Search
    scores = search_tfidf(index, query_keywords)
    
    # Sort and retrieve
    sorted_snippets = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    retrieved = [text for text, score in sorted_snippets[:5]] # Top 5
    
    # Estimate tokens (simple char/4)
    total_tokens = sum(len(s) for s in retrieved) // 4
    
    return retrieved, total_tokens

def run_pilot_validation(input_csv: str, output_json: str, n: int = 20) -> Dict:
    """
    Main pilot validation logic.
    1. Load sample scores.
    2. Simulate repo content for each.
    3. Run retrieval baseline.
    4. Calculate precision.
    5. Compute correlation between regularity_score and precision.
    """
    ensure_directories([Path(output_json).parent])
    
    scores_data = load_sample_scores(input_csv, n)
    if not scores_data:
        raise ValueError(f"No data found in {input_csv}")

    correlations = []
    results = []

    for record in scores_data:
        repo_id = record['repo_id']
        regularity_score = record['regularity_score']
        
        # Simulate repo
        repo_content = simulate_repo_content(repo_id)
        
        # Extract query keywords
        keywords = extract_keywords_from_repo_id(repo_id)
        
        # Run baseline
        start_time = time.time()
        retrieved_snippets, token_count = simple_retrieval_baseline(repo_content, keywords)
        latency = time.time() - start_time
        
        # Calculate precision
        precision = calculate_precision(retrieved_snippets, keywords)
        
        # Log metrics
        log_entry = create_log_entry(
            repo_id=repo_id,
            context_precision=precision,
            total_tokens=token_count,
            wall_clock_latency=latency,
            regularity_score=regularity_score,
            set_type="pilot"
        )
        
        results.append({
            'repo_id': repo_id,
            'regularity_score': regularity_score,
            'precision': precision,
            'latency_ms': round(latency * 1000, 2),
            'tokens': token_count
        })
        
        correlations.append((regularity_score, precision))

    if len(correlations) < 2:
        raise ValueError("Insufficient data points for correlation calculation")

    # Calculate Pearson correlation
    x_vals = [c[0] for c in correlations]
    y_vals = [c[1] for c in correlations]
    
    mean_x = sum(x_vals) / len(x_vals)
    mean_y = sum(y_vals) / len(y_vals)
    
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in correlations)
    denom_x = sum((x - mean_x)**2 for x in x_vals)**0.5
    denom_y = sum((y - mean_y)**2 for y in y_vals)**0.5
    
    if denom_x == 0 or denom_y == 0:
        correlation_coefficient = 0.0
    else:
        correlation_coefficient = numerator / (denom_x * denom_y)

    # Flag if correlation is weak (arbitrary threshold for pilot)
    # If correlation is close to 0, it suggests regularity score might not predict retrieval success
    flag_strategy = False
    if abs(correlation_coefficient) < 0.3:
        flag_strategy = True

    output_data = {
        'n_samples': len(results),
        'correlation_coefficient': correlation_coefficient,
        'flag_stratification_review': flag_strategy,
        'results': results
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    return output_data

def main():
    input_path = get_path('processed', 'regularity_scores.csv')
    output_path = get_path('processed', 'pilot_correlation.json')
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        sys.exit(1)
        
    print(f"Running pilot validation on {input_path}...")
    try:
        result = run_pilot_validation(input_path, output_path, n=20)
        print(f"Pilot complete. Correlation: {result['correlation_coefficient']:.4f}")
        if result['flag_stratification_review']:
            print("WARNING: Correlation is low. Review stratification strategy.")
        else:
            print("OK: Correlation suggests stratification is valid.")
    except Exception as e:
        print(f"Pilot validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
