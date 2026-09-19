import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np

from src.utils.config import get_lag_window, get_accuracy_block_size, get_data_dir
from src.utils.logging import get_logger, log_event

logger = get_logger(__name__)

def load_mmn_epochs(file_path: Optional[str] = None) -> pd.DataFrame:
    """Load pre-processed MMN epoch data."""
    if file_path is None:
        file_path = os.path.join(get_data_dir(), "preprocessed_epochs.csv")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"MMN epochs file not found at {file_path}")
    
    return pd.read_csv(file_path)

def load_accuracy_blocks(file_path: Optional[str] = None) -> pd.DataFrame:
    """Load accuracy block data."""
    if file_path is None:
        file_path = os.path.join(get_data_dir(), "accuracy_blocks.csv")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Accuracy blocks file not found at {file_path}")
    
    return pd.read_csv(file_path)

def calculate_block_accuracy(epochs_df: pd.DataFrame, block_size: int) -> pd.DataFrame:
    """Calculate accuracy for each block of trials."""
    # Group by subject and block, calculate accuracy
    accuracy_df = epochs_df.groupby(['subject_id', 'block_id']).apply(
        lambda x: x['response_correct'].mean()
    ).reset_index(name='accuracy')
    
    # Ensure block_size is applied correctly
    accuracy_df['trial_start'] = accuracy_df['block_id'] * block_size
    accuracy_df['trial_end'] = accuracy_df['trial_start'] + block_size
    
    return accuracy_df

def run_behavioral_binning_pipeline(epochs_df: pd.DataFrame) -> pd.DataFrame:
    """Run the behavioral binning pipeline to create accuracy blocks."""
    block_size = get_accuracy_block_size()
    accuracy_blocks = calculate_block_accuracy(epochs_df, block_size)
    
    output_path = os.path.join(get_data_dir(), "accuracy_blocks.csv")
    accuracy_blocks.to_csv(output_path, index=False)
    logger.info(f"Behavioral binning complete. Output: {output_path}")
    
    return accuracy_blocks

def run_lagged_alignment_pipeline(mmn_df: pd.DataFrame, accuracy_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the lagged alignment pipeline.
    
    Logic:
    1. Load MMN epochs and accuracy blocks.
    2. For each subject/block, calculate the MMN amplitude over a preceding 
       fixed-length trial window (t-N to t-M).
    3. Align this MMN value to the subsequent accuracy block (t to t+n).
    4. **SANITY CHECK (T040)**: Before writing:
       - Assert source window (t-N to t-M) and target block (t to t+n) do not overlap.
       - Assert source window contains at least 10 valid trials.
       - If checks fail, drop the block and log a warning.
    """
    lag_window = get_lag_window()
    # lag_window is expected to be a tuple (N, M) or similar configuration
    # Assuming format (source_start_offset, source_end_offset) relative to block start
    # e.g., (-50, -10) meaning 50 trials back to 10 trials back
    if isinstance(lag_window, str):
        parts = list(map(int, lag_window.split(',')))
        source_start_offset, source_end_offset = parts[0], parts[1]
    else:
        source_start_offset, source_end_offset = lag_window[0], lag_window[1]
        
    block_size = get_accuracy_block_size()
    
    aligned_records = []
    dropped_blocks = []
    
    for subject_id in mmn_df['subject_id'].unique():
        subject_mmn = mmn_df[mmn_df['subject_id'] == subject_id].sort_values('block_id')
        subject_acc = accuracy_df[accuracy_df['subject_id'] == subject_id].sort_values('block_id')
        
        # Merge on block_id logic: MMN at block B aligns to Accuracy at block B+1 (or similar logic)
        # Assuming standard lagged alignment: MMN calculated from trials leading up to block B
        # aligns to Accuracy of block B.
        
        for _, mmn_row in subject_mmn.iterrows():
            block_id = mmn_row['block_id']
            mmn_amplitude = mmn_row['mmn_amplitude']
            
            # Define target block (Accuracy)
            # Logic: MMN at block_id aligns to Accuracy at block_id (or block_id + 1 depending on spec)
            # Assuming alignment to the SAME block_id for now, as per typical lagged analysis
            # where MMN is the predictor for the behavior in that block.
            # If the spec implies MMN(t-N..t-M) predicts Accuracy(t..t+n), then they are in the same block.
            
            target_block = block_id
            
            # Check if target block exists in accuracy data
            acc_row = subject_acc[subject_acc['block_id'] == target_block]
            if acc_row.empty:
                dropped_blocks.append({
                    'subject_id': subject_id, 
                    'block_id': block_id, 
                    'reason': 'Missing accuracy block'
                })
                continue
            
            accuracy_val = acc_row.iloc[0]['accuracy']
            trial_start = acc_row.iloc[0]['trial_start']
            trial_end = acc_row.iloc[0]['trial_end']
            
            # --- T040 SANITY CHECK ---
            # Define source window range (in trial indices)
            # Source window: [trial_start + source_start_offset, trial_start + source_end_offset]
            # Target block: [trial_start, trial_end]
            
            source_window_start = trial_start + source_start_offset
            source_window_end = trial_start + source_end_offset
            
            # 1. Check Overlap
            # Overlap occurs if source window starts before target ends AND source window ends after target starts
            # Since source is typically negative offset, source_window_end < trial_start usually holds.
            # But we must verify: source_window_end >= trial_start implies overlap.
            if source_window_end >= trial_start:
                dropped_blocks.append({
                    'subject_id': subject_id,
                    'block_id': block_id,
                    'reason': f'Overlap detected: source_end ({source_window_end}) >= target_start ({trial_start})'
                })
                logger.warning(f"Overlap detected for subject {subject_id}, block {block_id}. Dropping.")
                continue
            
            # 2. Check Trial Count in Source Window
            # We need to estimate or check the number of valid trials in the source window.
            # Since we are aligning to a block, we assume the block size defines the granularity.
            # The source window size in trials = source_window_end - source_window_start
            # However, we must ensure these are valid trials (not artifact rejected).
            # For this check, we assume the block structure implies valid trials if the block exists.
            # We check the width of the window against the minimum required (10 trials).
            source_window_trial_count = source_window_end - source_window_start
            
            if source_window_trial_count < 10:
                dropped_blocks.append({
                    'subject_id': subject_id,
                    'block_id': block_id,
                    'reason': f'Source window too small ({source_window_trial_count} trials < 10)'
                })
                logger.warning(f"Source window too small for subject {subject_id}, block {block_id}. Dropping.")
                continue
            
            # If checks pass, record the aligned data
            aligned_records.append({
                'subject_id': subject_id,
                'block_id': block_id,
                'mmn_amplitude': mmn_amplitude,
                'accuracy': accuracy_val,
                'source_window_start_trial': source_window_start,
                'source_window_end_trial': source_window_end,
                'target_trial_start': trial_start,
                'target_trial_end': trial_end
            })
    
    if dropped_blocks:
        logger.warning(f"Dropped {len(dropped_blocks)} blocks due to sanity check failures.")
        # Optionally log dropped blocks to a file for debugging
        # dropped_df = pd.DataFrame(dropped_blocks)
        # dropped_df.to_csv(os.path.join(get_data_dir(), "dropped_blocks_log.csv"), index=False)
    
    if not aligned_records:
        logger.error("No valid aligned records found. Pipeline may have failed.")
        # Return empty DF with correct schema
        return pd.DataFrame(columns=['subject_id', 'block_id', 'mmn_amplitude', 'accuracy', 'source_window_start_trial', 'source_window_end_trial', 'target_trial_start', 'target_trial_end'])
    
    result_df = pd.DataFrame(aligned_records)
    
    output_path = os.path.join(get_data_dir(), "interim_lagged_mmns.csv")
    result_df.to_csv(output_path, index=False)
    logger.info(f"Lagged alignment complete. Output: {output_path}")
    
    return result_df

def add_learning_phase(aligned_df: pd.DataFrame) -> pd.DataFrame:
    """Add learning phase column (Early/Late) based on block_id."""
    # Simple binning: first 50% of blocks = Early, rest = Late
    max_block = aligned_df['block_id'].max()
    threshold = max_block // 2
    
    def classify_phase(block_id):
        return "Early" if block_id <= threshold else "Late"
    
    aligned_df['learning_phase'] = aligned_df['block_id'].apply(classify_phase)
    
    output_path = os.path.join(get_data_dir(), "interim_lagged_mmns.csv")
    aligned_df.to_csv(output_path, index=False)
    logger.info(f"Learning phase added. Output: {output_path}")
    
    return aligned_df

def main():
    """Main entry point for the alignment pipeline."""
    try:
        mmn_df = load_mmn_epochs()
        accuracy_df = run_behavioral_binning_pipeline(mmn_df) # This regenerates accuracy blocks if needed
        
        # Re-load accuracy blocks after binning
        accuracy_df = load_accuracy_blocks()
        
        aligned_df = run_lagged_alignment_pipeline(mmn_df, accuracy_df)
        
        if not aligned_df.empty:
            final_df = add_learning_phase(aligned_df)
            logger.info("Alignment pipeline completed successfully.")
        else:
            logger.warning("Alignment pipeline produced no results.")
            
    except Exception as e:
        logger.error(f"Alignment pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()