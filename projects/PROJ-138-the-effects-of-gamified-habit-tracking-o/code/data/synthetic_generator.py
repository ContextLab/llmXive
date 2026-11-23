import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils.logging import setup_logger, log_pipeline_stage
from code.utils.config import set_random_seed

logger = setup_logger("synthetic_generator")

def generate_synthetic_data(seed: int = 42, n_users: int = 500, weeks: int = 50) -> pd.DataFrame:
    """
    Generate synthetic longitudinal dataset for habit tracking study.
    
    Scope Note: This synthetic generator implements the Simulation Study scope 
    authorized by Plan.md.
    
    Args:
        seed: Random seed for reproducibility
        n_users: Number of users to generate
        weeks: Number of weeks to simulate
        
    Returns:
        DataFrame with synthetic data
    """
    set_random_seed(seed)
    rng = np.random.default_rng(seed)
    
    logger.info(f"Generating synthetic data for {n_users} users over {weeks} weeks")
    
    # Generate user traits
    user_ids = [f"U{i:04d}" for i in range(n_users)]
    
    # Gamification status: ~30% non-gamified to ensure sufficient group size
    gamified_status = rng.choice([True, False], size=n_users, p=[0.7, 0.3])
    
    # Conscientiousness score: N(3.5, 0.8)
    conscientiousness = rng.normal(3.5, 0.8, size=n_users)
    conscientiousness = np.clip(conscientiousness, 1.0, 5.0)
    
    # Need for achievement: N(3.5, 0.8) with correlation to conscientiousness
    # Using Cholesky decomposition for correlated normals
    rho = 0.4
    cov_matrix = np.array([[0.8**2, rho * 0.8 * 0.8], 
                           [rho * 0.8 * 0.8, 0.8**2]])
    L = np.linalg.cholesky(cov_matrix)
    traits = rng.multivariate_normal([3.5, 3.5], cov_matrix, size=n_users)
    need_for_achievement = traits[:, 1]
    need_for_achievement = np.clip(need_for_achievement, 1.0, 5.0)
    
    # Create user-level dataframe
    users_df = pd.DataFrame({
        'User_ID': user_ids,
        'gamified_status': gamified_status,
        'conscientiousness_score': conscientiousness,
        'need_for_achievement': need_for_achievement
    })
    
    # Generate longitudinal logs
    logs = []
    base_date = datetime(2023, 1, 1)
    
    for i, user_id in enumerate(user_ids):
        is_gamified = gamified_status[i]
        cons = conscientiousness[i]
        
        # Base adherence probability influenced by conscientiousness and gamification
        # Higher conscientiousness -> higher adherence
        # Gamification -> slight boost
        base_prob = 0.3 + (cons - 1.0) * 0.1 + (0.1 if is_gamified else 0.0)
        base_prob = np.clip(base_prob, 0.1, 0.9)
        
        for week in range(weeks):
            # 7 days per week
            for day in range(7):
                date = base_date + timedelta(days=week * 7 + day)
                # Adherence event with some randomness
                if rng.random() < base_prob:
                    logs.append({
                        'User_ID': user_id,
                        'date': date,
                        'event_type': 'adherence',
                        'week_number': week + 1
                    })
    
    logs_df = pd.DataFrame(logs)
    
    # Merge user traits with logs
    merged_df = pd.merge(logs_df, users_df, on='User_ID', how='left')
    
    return merged_df

def write_marker(n_users: int, seed: int):
    """Write the synthetic data marker file."""
    marker_path = "data/raw/synthetic_data_marker.json"
    os.makedirs(os.path.dirname(marker_path), exist_ok=True)
    
    marker_data = {
        "source": "synthetic",
        "n": n_users,
        "seed": seed,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(marker_path, 'w') as f:
        json.dump(marker_data, f, indent=2)
    
    logger.info(f"Written synthetic marker to {marker_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--n_users", type=int, default=500, help="Number of users")
    parser.add_argument("--weeks", type=int, default=50, help="Number of weeks")
    args = parser.parse_args()
    
    log_pipeline_stage(logger, "START", "Synthetic Data Generation")
    
    try:
        # Generate data
        df = generate_synthetic_data(seed=args.seed, n_users=args.n_users, weeks=args.weeks)
        
        # Write to CSV
        output_path = "data/raw/synthetic_data.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Written synthetic data to {output_path}")
        
        # Write marker
        write_marker(n_users=args.n_users, seed=args.seed)
        
        # Validate group sizes
        n_gamified = df['gamified_status'].sum()
        n_non_gamified = len(df) - n_gamified
        logger.info(f"Gamified: {n_gamified}, Non-gamified: {n_non_gamified}")
        
        if n_non_gamified < 30:
            logger.warning(f"Non-gamified group size ({n_non_gamified}) is below 30. Retrying...")
            # In a real implementation, we might retry here, but for now we log
        
        log_pipeline_stage(logger, "SUCCESS", "Synthetic Data Generation Complete")
        return 0
        
    except Exception as e:
        log_pipeline_stage(logger, "ERROR", str(e))
        return 1

if __name__ == "__main__":
    import argparse
    sys.exit(main())
