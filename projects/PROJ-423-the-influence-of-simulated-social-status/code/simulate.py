import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

# Local imports based on API surface
from config import load_simulation_params, get_random_seed, get_sample_size
from utils import set_seed, ensure_directory
from logger import get_logger

logger = get_logger(__name__)

# --- Simulation Logic ---

def generate_synthetic_data(design_type: str = "between", n: int = None, seed: int = None) -> pd.DataFrame:
    """
    Generates synthetic data for the specified design type.
    design_type: 'between' or 'within'
    """
    if seed is None:
        seed = get_random_seed()
    if n is None:
        n = get_sample_size()

    set_seed(seed)

    logger.info(f"Generating synthetic data for {design_type}-subjects design with N={n}")

    if design_type == "between":
        # Between-subjects: Each participant appears once
        participant_ids = [f"sub_{i:04d}" for i in range(n)]
        status_levels = np.random.choice(["High", "Low"], size=n)
        observed_behaviors = np.random.choice(["Risky", "Conservative"], size=n)
        
        # Simulate risk taking score based on simple effect model
        # Base mean 50, effect sizes added
        risk_scores = np.random.normal(50, 10, size=n)
        for i, (status, behavior) in enumerate(zip(status_levels, observed_behaviors)):
            if status == "High":
                risk_scores[i] += 2.0 # Example effect
            if behavior == "Risky":
                risk_scores[i] += 1.5
        
        df = pd.DataFrame({
            "participant_id": participant_ids,
            "status_level": status_levels,
            "observed_behavior": observed_behaviors,
            "risk_taking_score": risk_scores
        })

    elif design_type == "within":
        # Within-subjects: Each participant appears in all 4 condition combinations
        conditions = [
            ("High", "Risky"),
            ("High", "Conservative"),
            ("Low", "Risky"),
            ("Low", "Conservative")
        ]
        rows = []
        for pid in range(n):
            participant_id = f"sub_{pid:04d}"
            for status, behavior in conditions:
                # Simulate score with within-subject correlation logic (simplified)
                base = 50 + np.random.normal(0, 5) # Subject baseline
                effect = 0
                if status == "High": effect += 2.0
                if behavior == "Risky": effect += 1.5
                
                score = base + effect + np.random.normal(0, 5) # Residual noise
                rows.append({
                    "participant_id": participant_id,
                    "status_level": status,
                    "observed_behavior": behavior,
                    "risk_taking_score": score
                })
        
        df = pd.DataFrame(rows)
    else:
        raise ValueError(f"Unsupported design_type: {design_type}. Must be 'between' or 'within'.")

    return df

def validate_design_adherence(df: pd.DataFrame, expected_design: str) -> bool:
    """
    Validates that the generated dataset strictly adheres to the chosen design.
    
    For between-subjects: Each participant_id must appear exactly once.
    For within-subjects: Each participant_id must appear exactly 4 times (once per condition).
    
    Raises ValueError if validation fails.
    """
    logger.info(f"Validating design adherence for {expected_design} design...")
    
    unique_participants = df['participant_id'].nunique()
    total_rows = len(df)
    
    if expected_design == "between":
        # Check: 1 row per participant
        counts = df['participant_id'].value_counts()
        if not (counts == 1).all():
            raise ValueError(
                f"Design Violation: Between-subjects design expected. "
                f"Found {unique_participants} unique participants but {total_rows} rows. "
                f"Some participants appear multiple times. "
                f"Counts: {counts[counts > 1].to_dict()}"
            )
        logger.info(f"Validation passed: Between-subjects design confirmed ({unique_participants} participants, 1 row each).")
        
    elif expected_design == "within":
        # Check: 4 rows per participant (High/Risky, High/Cons, Low/Risky, Low/Cons)
        # We expect 4 unique combinations of (status_level, observed_behavior)
        expected_combinations = 4
        counts = df['participant_id'].value_counts()
        
        if not (counts == expected_combinations).all():
            raise ValueError(
                f"Design Violation: Within-subjects design expected. "
                f"Found {unique_participants} unique participants but {total_rows} rows. "
                f"Expected {expected_combinations} rows per participant. "
                f"Found counts: {counts.value_counts().to_dict()}"
            )
        
        # Additional check: ensure all 4 condition combinations exist for each participant
        # (This is implicitly checked by count == 4 if we assume the generator is correct,
        # but let's be explicit about the combinations)
        unique_combos = df.groupby('participant_id')[['status_level', 'observed_behavior']].apply(
            lambda x: set(zip(x['status_level'], x['observed_behavior']))
        )
        
        required_set = {
            ("High", "Risky"), ("High", "Conservative"),
            ("Low", "Risky"), ("Low", "Conservative")
        }
        
        for pid, combos in unique_combos.items():
            if combos != required_set:
                missing = required_set - combos
                raise ValueError(
                    f"Design Violation: Participant {pid} missing conditions: {missing}. "
                    f"Within-subjects design requires all 4 condition combinations per participant."
                )
        
        logger.info(f"Validation passed: Within-subjects design confirmed ({unique_participants} participants, {expected_combinations} rows each).")
    else:
        raise ValueError(f"Unknown design type for validation: {expected_design}")

    return True

def main():
    parser = argparse.ArgumentParser(description="Generate and validate synthetic simulation data.")
    parser.add_argument("--design", type=str, default="between", choices=["between", "within"],
                        help="Design type: 'between' or 'within'")
    parser.add_argument("--output", type=str, default="data/raw/simulated_data.csv",
                        help="Output file path")
    parser.add_argument("--validate", action="store_true", default=True,
                        help="Run design adherence validation after generation")
    
    args = parser.parse_args()
    
    params = load_simulation_params()
    design = args.design
    n = params.get("n", 100)
    seed = params.get("seed", 42)
    
    ensure_directory(args.output)
    
    try:
        df = generate_synthetic_data(design_type=design, n=n, seed=seed)
        df.to_csv(args.output, index=False)
        logger.info(f"Data saved to {args.output}")
        
        if args.validate:
            validate_design_adherence(df, design)
            logger.info("Design validation successful.")
            
    except Exception as e:
        logger.error(f"Simulation or validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
