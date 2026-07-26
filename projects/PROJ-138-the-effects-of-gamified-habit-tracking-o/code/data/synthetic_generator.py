"""
Synthetic data generator for the habit tracking study.
Generates realistic longitudinal data with known ground truth.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from code.utils.config import set_random_seed
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("generator")

def generate_synthetic_data(n_users: int = 100, weeks: int = 50, seed: int = 42):
    """
    Generate synthetic longitudinal dataset.
    
    Args:
        n_users: Number of users to simulate
        weeks: Number of weeks to simulate
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with synthetic data
    """
    set_random_seed(seed)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Generate user traits
    # Conscientiousness ~ N(3.5, 0.8)
    # Need for Achievement ~ N(3.5, 0.8) with correlation 0.6
    mean = [3.5, 3.5]
    cov = [[0.8**2, 0.6 * 0.8 * 0.8], [0.6 * 0.8 * 0.8, 0.8**2]]
    traits = np.random.multivariate_normal(mean, cov, n_users)
    
    user_ids = [f"U{i:04d}" for i in range(n_users)]
    conscientiousness = traits[:, 0]
    need_for_achievement = traits[:, 1]
    
    # Gamification status: ensure >= 30 non-gamified
    n_non_gamified = max(30, int(n_users * 0.3))
    gamified_status = [False] * n_non_gamified + [True] * (n_users - n_non_gamified)
    np.random.shuffle(gamified_status)
    
    # Generate logs
    logs = []
    start_date = datetime(2023, 1, 1)
    
    event_types = ["check_in", "task_complete", "habit_done", "streak_milestone"]
    
    for i, uid in enumerate(user_ids):
        is_gamified = gamified_status[i]
        c_score = conscientiousness[i]
        n_score = need_for_achievement[i]
        
        # Base adherence probability influenced by traits
        # Higher traits -> higher adherence
        base_prob = 0.5 + (c_score - 3.5) * 0.1 + (n_score - 3.5) * 0.1
        if is_gamified:
            base_prob += 0.15  # Gamification boost
        
        base_prob = np.clip(base_prob, 0.1, 0.95)
        
        for w in range(weeks):
            week_start = start_date + timedelta(weeks=w)
            # Generate daily events for the week
            for d in range(7):
                date = week_start + timedelta(days=d)
                # Probability of event on this day
                if np.random.random() < base_prob:
                    event = np.random.choice(event_types)
                    logs.append({
                        "User_ID": uid,
                        "gamified_status": is_gamified,
                        "conscientiousness_score": c_score,
                        "need_for_achievement": n_score,
                        "date": date.strftime("%Y-%m-%d"),
                        "event_type": event
                    })
    
    df = pd.DataFrame(logs)
    return df

def write_marker(n_users: int, n_records: int):
    """Write the synthetic data marker file."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    marker_path = os.path.join(root, "data", "raw", "synthetic_data_marker.json")
    
    marker = {
        "source": "synthetic",
        "n_users": n_users,
        "n_records": n_records,
        "seed": 42
    }
    
    with open(marker_path, 'w') as f:
        json.dump(marker, f, indent=2)
    
    logger.info(f"Marker written to {marker_path}")

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n_users", type=int, default=100)
    parser.add_argument("--weeks", type=int, default=50)
    args = parser.parse_args()
    
    log_pipeline_stage(logger, "START", "Synthetic Data Generation")
    
    df = generate_synthetic_data(n_users=args.n_users, weeks=args.weeks, seed=args.seed)
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(root, "data", "raw", "synthetic_data.csv")
    
    df.to_csv(output_path, index=False)
    logger.info(f"Generated {len(df)} records to {output_path}")
    
    write_marker(args.n_users, len(df))
    
    # Verify constraints
    non_gamified = df[df['gamified_status'] == False]['User_ID'].nunique()
    if non_gamified < 30:
        logger.error(f"Constraint violated: Non-gamified users ({non_gamified}) < 30")
        sys.exit(1)
    
    # Check correlation
    corr = df['conscientiousness_score'].corr(df['need_for_achievement'])
    logger.info(f"Correlation between traits: {corr:.4f} (expected ~0.6)")
    
    log_pipeline_stage(logger, "END", "Synthetic Data Generation")

if __name__ == "__main__":
    main()
