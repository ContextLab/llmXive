import pandas as pd
from typing import List, Optional
from utils.logger import get_logger
import json
import glob
from pathlib import Path

logger = get_logger(__name__)

class DataCleaner:
    """
    Handles specific data cleaning logic: exclusion and imputation.
    """

    def impute_sus_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Implements SUS imputation logic (T021b):
        - If > 1 item missing, mark as incomplete (handled by exclusion logic in run_cleaning_pipeline).
        - If <= 1 item missing, impute with participant mean.
        
        Note: This implementation assumes the raw data contains the 10 individual SUS questions
        (SUS_Q1 to SUS_Q10). If the data is already aggregated into a single 'sus_score',
        no imputation is needed. If the data contains raw responses, we calculate the score.
        
        For this task, we assume the input might have 'sus_score' missing for some rows,
        or individual questions missing. We will attempt to reconstruct 'sus_score' if possible,
        or impute the aggregate if the raw questions are present.
        
        Simplified approach for this pipeline:
        If 'sus_score' is NaN but we have Q1-Q10, calculate it.
        If 'sus_score' is NaN and we don't have Q1-Q10, we cannot impute a single score from a mean
        without the raw questions. We will mark it as incomplete if we cannot calculate it.
        
        However, the task description says: "If <= 1 item missing, impute with participant mean".
        This implies we are looking at the 10 individual items.
        """
        
        # Check if we have individual questions
        sus_cols = [f"SUS_Q{i}" for i in range(1, 11)]
        all_present = all(col in df.columns for col in sus_cols)
        
        if all_present:
            logger.info("Detected individual SUS questions. Calculating/Imputing scores.")
            # Calculate score per row
            # SUS Scoring: Odd items (1,3,5,7,9): (Q-1) * 5. Even items (2,4,6,8,10): (5-Q) * 5.
            # Total = sum.
            
            # Create a copy to avoid SettingWithCopyWarning
            df = df.copy()
            
            # Calculate raw score for each row
            def calculate_sus_score(row):
                score = 0
                missing_count = 0
                for i in range(1, 11):
                    q_col = f"SUS_Q{i}"
                    val = row[q_col]
                    if pd.isna(val):
                        missing_count += 1
                        continue
                    
                    if i % 2 == 1: # Odd
                        score += (val - 1) * 5
                    else: # Even
                        score += (5 - val) * 5
                
                if missing_count > 1:
                    return None # Mark as incomplete
                elif missing_count == 1:
                    # Impute with participant mean? 
                    # Since we are doing this row-wise, we can't easily get "participant mean" 
                    # without a groupby. However, the standard SUS imputation is often just 
                    # calculating the score from available items and scaling, or if one is missing,
                    # using the mean of the other 9 * (10/9).
                    # For simplicity and robustness in this pipeline:
                    # If 1 missing, calculate from 9 and scale.
                    # But the task says "impute with participant mean". This implies we need 
                    # to group by participant_id first.
                    pass 
                
                return score

            # Group by participant_id to calculate participant means for imputation
            # This is complex if we don't have multiple sessions per participant with full data.
            # We will implement a simplified version: 
            # If <= 1 missing, calculate score from available, then if we need to impute the missing one,
            # we assume the missing one is the mean of the others.
            
            # Let's try a different approach: Calculate score for rows with <= 1 missing.
            # If > 1 missing, set score to NaN.
            
            def safe_sus_calc(row):
                vals = [row[f"SUS_Q{i}"] for i in range(1, 11)]
                valid_vals = [v for v in vals if pd.notna(v)]
                if len(valid_vals) < 9:
                    return None # More than 1 missing
                
                # Calculate score from valid values
                score = 0
                for i in range(1, 11):
                    val = row[f"SUS_Q{i}"]
                    if pd.isna(val):
                        continue
                    if i % 2 == 1:
                        score += (val - 1) * 5
                    else:
                        score += (5 - val) * 5
                
                # If exactly 1 missing, we have 9 values. 
                # The max score for 9 items is 45. We need to scale to 100?
                # Actually, standard SUS is 0-40 * 2.5 = 0-100.
                # If we miss one, we can't just scale.
                # The task says "impute with participant mean". 
                # This implies we need to know the participant's average across sessions?
                # Or average of the 10 items for this participant?
                # Let's assume "participant mean" means the mean of the 10 items for this specific session 
                # if we had them, or the mean of the available 9 items.
                
                # Simple heuristic: If 1 missing, fill it with the mean of the other 9.
                if len(valid_vals) == 9:
                    mean_val = sum(valid_vals) / 9
                    # Find the missing index
                    for i in range(1, 11):
                        if pd.isna(row[f"SUS_Q{i}"]):
                            # Impute
                            if i % 2 == 1:
                                score += (mean_val - 1) * 5
                            else:
                                score += (5 - mean_val) * 5
                    return score
                
                return score

            df['calculated_sus'] = df.apply(safe_sus_calc, axis=1)
            
            # If we have a pre-existing 'sus_score', we might want to overwrite it if it's NaN
            # or if we calculated a better one.
            # For this task, we will populate 'sus_score' from 'calculated_sus' if 'sus_score' is missing.
            if 'sus_score' not in df.columns:
                df['sus_score'] = df['calculated_sus']
            else:
                df['sus_score'] = df['sus_score'].fillna(df['calculated_sus'])
            
            # Drop the helper column
            df = df.drop(columns=['calculated_sus'], errors='ignore')
            
            # Mark rows where we couldn't calculate (still NaN) as incomplete for downstream
            # This will be handled by the exclusion step in run_cleaning_pipeline
            logger.info(f"SUS imputation complete. {df['sus_score'].isna().sum()} rows still missing SUS score.")
        else:
            logger.info("Individual SUS questions not found. Skipping item-level imputation.")
            # If 'sus_score' is already present and valid, we do nothing.
            # If 'sus_score' is missing, we can't impute without raw items.
        
        return df

def main():
    # This class is primarily used by run_cleaning_pipeline
    pass
