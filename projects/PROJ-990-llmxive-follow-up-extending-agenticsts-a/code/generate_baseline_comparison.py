"""
Task T022: Generate summary CSV output for baseline comparison.

Logic:
1. Load simulation logs from T017 (dynamic), T019 (static), T020 (random).
2. Aggregate metrics per condition: win_rate, avg_tokens, std_dev_tokens.
3. Calculate token_reduction_pct using formula: (static_tokens - dynamic_tokens) / static_tokens.
4. Determine threshold_met: True if token_reduction_pct >= 0.30, else False.
5. Write results to data/processed/baseline_comparison.csv.
6. Update data/processed/build_status.json with threshold_met status (does not exit with code 1 if failed).
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = DATA_PROCESSED / "baseline_comparison.csv"
BUILD_STATUS_FILE = DATA_PROCESSED / "build_status.json"

# Simulation log inputs
DYNAMIC_LOG = DATA_PROCESSED / "simulation_logs_dynamic.json"
STATIC_LOG = DATA_PROCESSED / "simulation_logs_static.json"
RANDOM_LOG = DATA_PROCESSED / "simulation_logs_random.json"

def load_simulation_data(log_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Load simulation logs from JSON file."""
    if not log_path.exists():
        logger.error(f"Simulation log not found: {log_path}")
        return None
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        elif isinstance(data, list):
            return data
        else:
            logger.error(f"Unexpected JSON structure in {log_path}")
            return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {log_path}: {e}")
        return None

def calculate_tokens(row: Dict[str, Any]) -> int:
    """Extract token count from a simulation result row."""
    # Handle various possible structures
    if 'total_tokens' in row:
        return row['total_tokens']
    elif 'tokens_used' in row:
        return row['tokens_used']
    elif 'context_size' in row:
        return row['context_size']
    elif 'prompt_tokens' in row:
        return row['prompt_tokens']
    else:
        # Fallback: try to find any field with 'token' in name
        for key, value in row.items():
            if 'token' in key.lower() and isinstance(value, (int, float)):
                return int(value)
        logger.warning(f"Could not find token count in row: {row}")
        return 0

def calculate_win(row: Dict[str, Any]) -> bool:
    """Extract win/loss status from a simulation result row."""
    if 'win' in row:
        return bool(row['win'])
    elif 'success' in row:
        return bool(row['success'])
    elif 'outcome' in row:
        return str(row['outcome']).lower() in ['win', 'success', 'true', '1']
    else:
        logger.warning(f"Could not find win status in row: {row}")
        return False

def aggregate_metrics(results: List[Dict[str, Any]], condition: str) -> Dict[str, Any]:
    """Aggregate metrics for a given condition."""
    if not results:
        return {
            'condition': condition,
            'win_rate': 0.0,
            'avg_tokens': 0.0,
            'std_dev_tokens': 0.0,
            'token_reduction_pct': 0.0,
            'threshold_met': False
        }

    token_counts = [calculate_tokens(r) for r in results]
    wins = [calculate_win(r) for r in results]

    total_tokens = sum(token_counts)
    avg_tokens = total_tokens / len(token_counts) if token_counts else 0.0
    
    if len(token_counts) > 1:
        # Calculate standard deviation manually to avoid numpy dependency issues
        variance = sum((t - avg_tokens) ** 2 for t in token_counts) / (len(token_counts) - 1)
        std_dev_tokens = variance ** 0.5
    else:
        std_dev_tokens = 0.0

    win_rate = sum(wins) / len(wins) if wins else 0.0

    return {
        'condition': condition,
        'win_rate': win_rate,
        'avg_tokens': avg_tokens,
        'std_dev_tokens': std_dev_tokens,
        'token_reduction_pct': 0.0,  # Will be calculated after all conditions
        'threshold_met': False
    }

def generate_baseline_comparison() -> bool:
    """Generate the baseline comparison CSV and update build status."""
    logger.info("Starting baseline comparison generation (T022)...")

    # Load simulation data
    dynamic_data = load_simulation_data(DYNAMIC_LOG)
    static_data = load_simulation_data(STATIC_LOG)
    random_data = load_simulation_data(RANDOM_LOG)

    if not dynamic_data or not static_data:
        logger.error("Missing required simulation logs (dynamic or static). Cannot proceed.")
        return False

    # Aggregate metrics
    dynamic_metrics = aggregate_metrics(dynamic_data, "dynamic")
    static_metrics = aggregate_metrics(static_data, "static")
    random_metrics = aggregate_metrics(random_data, "random")

    # Calculate token reduction
    # Formula: (static_tokens - dynamic_tokens) / static_tokens
    if static_metrics['avg_tokens'] > 0:
        reduction_dynamic = (static_metrics['avg_tokens'] - dynamic_metrics['avg_tokens']) / static_metrics['avg_tokens']
        dynamic_metrics['token_reduction_pct'] = reduction_dynamic
        dynamic_metrics['threshold_met'] = reduction_dynamic >= 0.30
    else:
        dynamic_metrics['token_reduction_pct'] = 0.0
        dynamic_metrics['threshold_met'] = False

    # For random baseline, calculate reduction relative to static as well
    if static_metrics['avg_tokens'] > 0:
        reduction_random = (static_metrics['avg_tokens'] - random_metrics['avg_tokens']) / static_metrics['avg_tokens']
        random_metrics['token_reduction_pct'] = reduction_random
        random_metrics['threshold_met'] = reduction_random >= 0.30
    else:
        random_metrics['token_reduction_pct'] = 0.0
        random_metrics['threshold_met'] = False

    # Prepare DataFrame
    df = pd.DataFrame([
        dynamic_metrics,
        static_metrics,
        random_metrics
    ])

    # Ensure correct column order
    df = df[['condition', 'win_rate', 'avg_tokens', 'std_dev_tokens', 'token_reduction_pct', 'threshold_met']]

    # Write CSV
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    logger.info(f"Baseline comparison CSV written to {OUTPUT_CSV}")

    # Update build_status.json
    build_status = {
        "pipeline_status": "completed",
        "timestamp": pd.Timestamp.now().isoformat(),
        "threshold_met": dynamic_metrics['threshold_met'],
        "message": "Token reduction threshold met" if dynamic_metrics['threshold_met'] else "Token reduction threshold NOT met (< 30%)",
        "details": {
            "dynamic_token_reduction_pct": dynamic_metrics['token_reduction_pct'],
            "static_avg_tokens": static_metrics['avg_tokens'],
            "dynamic_avg_tokens": dynamic_metrics['avg_tokens']
        }
    }

    with open(BUILD_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(build_status, f, indent=2)
    logger.info(f"Build status updated at {BUILD_STATUS_FILE}")

    # Log threshold result (do not exit with error)
    if not dynamic_metrics['threshold_met']:
        logger.warning(f"Token reduction threshold NOT met: {dynamic_metrics['token_reduction_pct']:.2%} < 30%")
        logger.info("Pipeline continues to generate statistical evidence as per spec.")

    return True

def main():
    """Main entry point."""
    success = generate_baseline_comparison()
    if not success:
        logger.error("Failed to generate baseline comparison.")
        sys.exit(1)
    logger.info("Baseline comparison generation completed successfully.")

if __name__ == "__main__":
    main()
