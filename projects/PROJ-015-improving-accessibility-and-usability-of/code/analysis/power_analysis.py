"""
Power Analysis Module (T036).
Computes statistical power and flags underpowered subgroups (N < 30).
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
import os
import sys
from pathlib import Path
import json

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

class PowerCalculator:
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def calculate_power_rm_anova(self, n: int, effect_size: float, alpha: float = 0.05) -> float:
        """
        Calculate statistical power for a Repeated Measures ANOVA.
        
        Uses the non-central F-distribution approximation.
        For RM ANOVA with 2 conditions (Traditional vs Explainable):
        - df1 = k - 1 (where k=2) -> df1 = 1
        - df2 = (n - 1) * (k - 1) -> df2 = n - 1
        - Non-centrality parameter (lambda) = N * effect_size^2 (simplified for eta-squared context)
        
        Args:
            n: Number of participants (subjects).
            effect_size: Estimated effect size (eta-squared or partial eta-squared).
            alpha: Significance level.
        
        Returns:
            Statistical power (1 - beta).
        """
        k = 2  # Number of conditions (Traditional, Explainable)
        df1 = k - 1
        df2 = (n - 1) * (k - 1)
        
        if df2 <= 0:
            return 0.0
        
        # Non-centrality parameter lambda
        # For eta-squared (η²), λ = N * η² / (1 - η²)
        # We assume the effect_size provided is eta-squared.
        if effect_size >= 1.0:
            effect_size = 0.99
        if effect_size <= 0.0:
            return 0.0
            
        ncp = n * (effect_size ** 2) / (1 - (effect_size ** 2))
        
        # Critical F value
        try:
            f_crit = stats.f.ppf(1 - alpha, df1, df2)
            # Power = P(F > f_crit | non-centrality parameter)
            power = stats.ncf.sf(f_crit, df1, df2, ncp)
            return float(power)
        except Exception as e:
            logger.warning(f"Could not calculate F-distribution power: {e}. Returning 0.0.")
            return 0.0

    def analyze_power(self, df: pd.DataFrame, effect_size: float = 0.06) -> List[Dict[str, Any]]:
        """
        Analyze statistical power for the current dataset.
        Flags subgroups with N < 30 as 'UNDERPOWERED'.
        
        Args:
            df: The cleaned sessions dataframe (data/processed/cleaned_sessions.csv).
            effect_size: Assumed effect size (eta-squared) for power calculation. Default 0.06 (small/medium).
        
        Returns:
            List of power flags.
        """
        flags = []
        
        # 1. Total Sample Analysis
        total_participants = df['participant_id'].nunique()
        
        if total_participants < 30:
            flags.append({
                "subgroup": "Total Sample",
                "N": total_participants,
                "power": 0.0, # Cannot reliably calculate or is effectively 0
                "flag": "UNDERPOWERED",
                "message": f"Total N ({total_participants}) is less than 30. Results are exploratory."
            })
        else:
            power = self.calculate_power_rm_anova(total_participants, effect_size)
            flag = "OK" if power >= 0.8 else "UNDERPOWERED" # Threshold 0.8
            status_msg = "Powered" if power >= 0.8 else "Low Power"
            
            flags.append({
                "subgroup": "Total Sample",
                "N": total_participants,
                "power": round(power, 4),
                "flag": flag,
                "message": f"Total N={total_participants}, Power={power:.4f} ({status_msg})"
            })
        
        # 2. Subgroup Analysis by Disability Type
        if 'disability_type' in df.columns:
            # Filter out null/empty disability types
            valid_types = df['disability_type'].dropna().unique()
            for dtype in valid_types:
                if pd.isna(dtype):
                    continue
                sub_df = df[df['disability_type'] == dtype]
                n_sub = sub_df['participant_id'].nunique()
                
                if n_sub < 30:
                    flags.append({
                        "subgroup": f"Disability: {dtype}",
                        "N": n_sub,
                        "power": 0.0,
                        "flag": "UNDERPOWERED",
                        "message": f"Subgroup N ({n_sub}) is less than 30. Results are exploratory."
                    })
                else:
                    power_sub = self.calculate_power_rm_anova(n_sub, effect_size)
                    flag_sub = "OK" if power_sub >= 0.8 else "UNDERPOWERED"
                    flags.append({
                        "subgroup": f"Disability: {dtype}",
                        "N": n_sub,
                        "power": round(power_sub, 4),
                        "flag": flag_sub,
                        "message": f"Subgroup N={n_sub}, Power={power_sub:.4f}"
                    })
        
        # 3. Subgroup Analysis by Interface Sequence (Counterbalancing)
        if 'sequence' in df.columns:
            for seq in df['sequence'].unique():
                if pd.isna(seq):
                    continue
                sub_df = df[df['sequence'] == seq]
                n_seq = sub_df['participant_id'].nunique()
                
                if n_seq < 30:
                    flags.append({
                        "subgroup": f"Sequence: {seq}",
                        "N": n_seq,
                        "power": 0.0,
                        "flag": "UNDERPOWERED",
                        "message": f"Sequence N ({n_seq}) is less than 30."
                    })
        
        return flags

def main():
    """
    CLI entry point for Power Analysis.
    Loads cleaned data, computes power, and writes to data/processed/power_flags.json.
    """
    parser = argparse.ArgumentParser(description="Run Power Analysis on cleaned session data.")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sessions.csv",
                        help="Path to cleaned sessions CSV.")
    parser.add_argument("--output", type=str, default="data/processed/power_flags.json",
                        help="Path to output JSON file.")
    parser.add_argument("--effect-size", type=float, default=0.06,
                        help="Assumed effect size (eta-squared) for calculation.")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} sessions from {input_path}")
        
        # Validate required columns
        required_cols = ['participant_id']
        if 'disability_type' in df.columns:
            required_cols.append('disability_type')
        if 'sequence' in df.columns:
            required_cols.append('sequence')
            
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logger.warning(f"Missing optional columns for subgroup analysis: {missing}. Proceeding with total sample only.")
        
        calculator = PowerCalculator()
        results = calculator.analyze_power(df, effect_size=args.effect_size)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Power analysis complete. Results written to {output_path}")
        logger.info(f"Flags generated: {len(results)}")
        
        # Print summary
        underpowered_count = sum(1 for r in results if r.get('flag') == 'UNDERPOWERED')
        if underpowered_count > 0:
            logger.warning(f"WARNING: {underpowered_count} subgroups are flagged as UNDERPOWERED.")
        
    except Exception as e:
        logger.error(f"Error during power analysis: {e}")
        raise

if __name__ == "__main__":
    import argparse
    main()
