"""
Synthetic data generator for the habit tracking study.
Generates a dataset with N=100 users, simulating self-report survey responses.
Ensures at least 30 non-gamified users.
"""
import os
import numpy as np
import pandas as pd
from code.utils.config import set_random_seed
from code.utils.logging import pipeline_logger

OUTPUT_PATH = "data/raw/synthetic_data.csv"

def generate_synthetic_data(seed: int = 42, n_users: int = 100, n_weeks: int = 12) -> pd.DataFrame:
    """
    Generate synthetic dataset.
    
    Args:
        seed: Random seed for reproducibility.
        n_users: Number of users to generate.
        n_weeks: Number of weeks of data per user.
        
    Returns:
        DataFrame with synthetic data.
    """
    set_random_seed(seed)
    pipeline_logger.info(f"Generating synthetic data with {n_users} users, {n_weeks} weeks, seed={seed}")

    # Ensure at least 30 non-gamified users
    n_non_gamified = 30
    n_gamified = n_users - n_non_gamified

    # Generate user IDs
    user_ids = [f"U{str(i).zfill(4)}" for i in range(1, n_users + 1)]
    
    # Assign gamification status
    # 30 False (non-gamified), 70 True (gamified)
    gamification_status = [False] * n_non_gamified + [True] * n_gamified
    np.random.shuffle(gamification_status)
    
    # Generate conscientiousness scores (normal distribution, mean=3.5, std=0.8, scale 1-5)
    conscientiousness = np.clip(np.random.normal(3.5, 0.8, n_users), 1, 5)
    
    # Generate need_for_achievement (correlated with conscientiousness)
    # Correlation ~0.6
    need_for_achievement = 0.6 * conscientiousness + 0.4 * np.random.normal(3.5, 0.8, n_users)
    need_for_achievement = np.clip(need_for_achievement, 1, 5)
    
    # Generate daily logs
    data = []
    for i, uid in enumerate(user_ids):
        is_gamified = gamification_status[i]
        con_score = conscientiousness[i]
        nfa_score = need_for_achievement[i]
        
        # Base adherence probability influenced by gamification and personality
        # Gamified users have slightly higher base adherence
        base_prob = 0.5
        if is_gamified:
            base_prob += 0.1
        # Conscientiousness adds to adherence
        base_prob += (con_score - 3.0) * 0.05
        # Need for achievement adds slightly
        base_prob += (nfa_score - 3.0) * 0.03
        
        base_prob = np.clip(base_prob, 0.1, 0.95)
        
        for week in range(1, n_weeks + 1):
            # Generate 7 days per week
            for day in range(1, 8):
                # Create a valid date string (YYYY-MM-DD)
                # Using a simplified month/day logic for the synthetic generation
                month = 1 + (week - 1) // 4
                day_of_month = ((week - 1) * 7 + day) % 28 + 1
                date = f"2024-{month:02d}-{day_of_month:02d}"
                
                # Adherence is probabilistic
                adherence = 1 if np.random.random() < base_prob else 0
                
                # Gamified app usage tag: 1 if user is gamified, 0 otherwise
                # This is the 'gamified_app_usage' tag required by FR-001a
                gamified_app_usage = 1 if is_gamified else 0
                
                data.append({
                    "user_id": uid,
                    "date": date,
                    "week_number": week,
                    "day_of_week": day,
                    "adherence_flag": adherence,
                    "gamification_status": is_gamified,
                    "conscientiousness_score": round(con_score, 2),
                    "need_for_achievement": round(nfa_score, 2),
                    "gamified_app_usage": gamified_app_usage
                })
    
    df = pd.DataFrame(data)
    
    # Verify constraints
    non_gamified_users = df[df["gamification_status"] == False]["user_id"].nunique()
    total_users = df["user_id"].nunique()
    
    pipeline_logger.info(f"Generated {total_users} users, {non_gamified_users} non-gamified")
    
    if non_gamified_users < 30:
        raise ValueError(f"Generated data has only {non_gamified_users} non-gamified users, required >= 30")
        
    return df

def main():
    """Main entry point for synthetic data generation."""
    pipeline_logger.info("Starting synthetic data generation...")
    
    try:
        df = generate_synthetic_data(seed=42)
        
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        df.to_csv(OUTPUT_PATH, index=False)
        pipeline_logger.info(f"Synthetic data saved to {OUTPUT_PATH}")
        
    except Exception as e:
        pipeline_logger.error(f"Synthetic data generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()