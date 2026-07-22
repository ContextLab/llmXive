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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_simulation_data(policy: str) -> Optional[pd.DataFrame]:
    """
    Load simulation logs for a specific policy.
    
    Args:
        policy: One of 'dynamic', 'static', 'random'
        
    Returns:
        DataFrame with simulation results or None if file missing
    """
    file_path = Path(f"data/processed/simulation_logs_{policy}.json")
    
    if not file_path.exists():
        logger.warning(f"Simulation logs not found for policy '{policy}': {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not data:
            logger.warning(f"No data in simulation logs for policy '{policy}'")
            return None
        
        # Normalize list of dicts into DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Handle cases where data might be nested
            if 'results' in data:
                df = pd.DataFrame(data['results'])
            else:
                df = pd.DataFrame([data])
        else:
            logger.error(f"Unexpected data format in {file_path}")
            return None
        
        # Ensure required columns exist
        required_cols = ['trajectory_id', 'win', 'tokens_used']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Missing required column '{col}' in {file_path}")
                return None
        
        return df
        
        logger.info(f"Successfully wrote baseline comparison to {OUTPUT_FILE}")
        logger.info(f"Output content:\n{df.to_string()}")

    except FileNotFoundError as e:
        logger.error(f"Missing required simulation data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading simulation data for {policy}: {e}")
        return None

def generate_baseline_comparison() -> Dict[str, Any]:
    """
    Generate summary CSV comparing baseline policies.
    
    Reads simulation logs for Dynamic, Static, and Random policies,
    computes aggregate statistics (win_rate, avg_tokens, std_dev_tokens),
    and writes to data/processed/baseline_comparison.csv.
    
    Returns:
        Dictionary with generation status and file path
    """
    policies = ['dynamic', 'static', 'random']
    results = []
    
    for policy in policies:
        df = load_simulation_data(policy)
        
        if df is None or len(df) == 0:
            logger.error(f"Cannot compute statistics for {policy}: no valid data")
            # We still add a row with NaN to maintain CSV structure, 
            # but downstream tasks should handle this as an error state.
            results.append({
                'condition': policy,
                'win_rate': float('nan'),
                'avg_tokens': float('nan'),
                'std_dev_tokens': float('nan'),
                'n_samples': 0
            })
            continue
        
        # Calculate metrics
        # Win rate: mean of boolean/win column (0 or 1)
        win_rate = df['win'].mean()
        
        # Token usage stats
        avg_tokens = df['tokens_used'].mean()
        std_dev_tokens = df['tokens_used'].std()
        
        # Handle single sample case where std is NaN
        if pd.isna(std_dev_tokens):
            std_dev_tokens = 0.0
        
        results.append({
            'condition': policy,
            'win_rate': round(win_rate, 4),
            'avg_tokens': round(avg_tokens, 2),
            'std_dev_tokens': round(std_dev_tokens, 2),
            'n_samples': len(df)
        })
        
        logger.info(f"Policy '{policy}': n={len(df)}, win_rate={win_rate:.4f}, "
                    f"avg_tokens={avg_tokens:.2f}, std_dev={std_dev_tokens:.2f}")
    
    # Create DataFrame and write to CSV
    comparison_df = pd.DataFrame(results)
    output_path = Path("data/processed/baseline_comparison.csv")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV with specific columns order
    comparison_df[['condition', 'win_rate', 'avg_tokens', 'std_dev_tokens']].to_csv(
        output_path, 
        index=False
    )
    
    logger.info(f"Baseline comparison written to {output_path}")
    
    return {
        'status': 'success',
        'output_file': str(output_path),
        'policies_processed': policies,
        'rows': len(results)
    }

def main():
    """Entry point for the baseline comparison generation."""
    logger.info("Starting baseline comparison generation...")
    
    try:
        result = generate_baseline_comparison()
        
        if result['status'] == 'success':
            logger.info(f"Completed successfully. Output: {result['output_file']}")
            print(json.dumps(result, indent=2))
        else:
            logger.error("Failed to generate baseline comparison")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        sys.exit(1)

def main():
    generate_baseline_comparison()

if __name__ == "__main__":
    main()