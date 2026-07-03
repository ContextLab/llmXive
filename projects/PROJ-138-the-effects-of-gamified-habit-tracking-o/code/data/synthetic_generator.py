"""
Synthetic data generator for the habit tracking study.
Generates a dataset with N=100 users, simulating gamification status and personality traits.
"""
import os
import numpy as np
import pandas as pd
from code.utils.config import set_random_seed
from code.utils.logging import pipeline_logger

OUTPUT_PATH = "data/raw/synthetic_data.csv"
N_USERS = 100
MIN_NON_GAMIFIED = 30

def generate_synthetic_data(seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic dataset.
    
    Mechanism:
    - Simulate 'self-report' for gamification status.
    - Ensure at least 30 non-gamified users.
    - Include conscientiousness_score and need_for_achievement (correlated).
    
    Args:
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with synthetic user data.
    """
    set_random_seed(seed)
    
    # Generate Gamification Status
    # Ensure at least MIN_NON_GAMIFIED are False
    # We'll generate 30 False and 70 True to match spec exactly
    num_non_gamified = MIN_NON_GAMIFIED
    num_gamified = N_USERS - num_non_gamified
    
    gamification_status = [False] * num_non_gamified + [True] * num_gamified
    np.random.shuffle(gamification_status)
    
    # Generate Personality Scores
    # Conscientiousness: Normal distribution
    conscientiousness = np.random.normal(loc=3.5, scale=0.8, size=N_USERS)
    conscientiousness = np.clip(conscientiousness, 1, 5) # Scale 1-5
    
    # Need for Achievement: Correlated with Conscientiousness
    # Generate a base and add correlation
    correlation = 0.6
    noise = np.random.normal(0, 0.5, N_USERS)
    need_for_achievement = (correlation * conscientiousness) + (np.sqrt(1 - correlation**2) * noise)
    need_for_achievement = np.clip(need_for_achievement, 1, 5)
    
    # Create DataFrame
    data = {
        "user_id": [f"U{str(i).zfill(3)}" for i in range(1, N_USERS + 1)],
        "gamification_status": gamification_status,
        "conscientiousness_score": conscientiousness,
        "need_for_achievement": need_for_achievement
    }
    
    df = pd.DataFrame(data)
    
    # Add synthetic daily logs for a subset of weeks to simulate the full dataset
    # For T013a, we just need the user-level data, but T013b expects logs.
    # We will generate a small set of logs for demonstration if needed,
    # but the primary output here is the user profile.
    # However, T017 expects a merged CSV with adherence.
    # Let's generate a basic log structure for these users.
    
    logs = []
    weeks = 12
    for _, row in df.iterrows():
        for week in range(1, weeks + 1):
            # Simulate adherence probability based on gamification and conscientiousness
            base_prob = 0.5
            if row['gamification_status']:
                base_prob += 0.1
            base_prob += (row['conscientiousness_score'] - 3.0) * 0.05
            
            prob = np.clip(base_prob, 0.1, 0.9)
            
            # Generate 7 days for this week
            for day in range(7):
                # Randomly decide if an event occurred (e.g., 80% chance)
                if np.random.random() < 0.8:
                    adherence = 1 if np.random.random() < prob else 0
                    logs.append({
                        "user_id": row['user_id'],
                        "week_number": week,
                        "day_number": day,
                        "event_type": "habit_check",
                        "adherence_flag": adherence,
                        "gamification_status": row['gamification_status'],
                        "conscientiousness_score": row['conscientiousness_score'],
                        "need_for_achievement": row['need_for_achievement']
                    })
    
    log_df = pd.DataFrame(logs)
    
    return log_df

def main():
    """Main entry point for synthetic data generation."""
    pipeline_logger.info("Starting synthetic data generation...")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    df = generate_synthetic_data(seed=42)
    
    # Save to CSV
    df.to_csv(OUTPUT_PATH, index=False)
    pipeline_logger.info(f"Synthetic data written to {OUTPUT_PATH}")
    pipeline_logger.info(f"Total records: {len(df)}, Unique users: {df['user_id'].nunique()}")
    
    # Verify group sizes
    non_gamified_count = (df['gamification_status'] == False).sum()
    pipeline_logger.info(f"Non-gamified users in logs: {non_gamified_count}")
    
    if non_gamified_count < MIN_NON_GAMIFIED:
        pipeline_logger.warning(f"Non-gamified count {non_gamified_count} is below minimum {MIN_NON_GAMIFIED}")
    else:
        pipeline_logger.info("Group size requirement met.")

if __name__ == "__main__":
    main()
