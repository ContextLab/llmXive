import os
import sys
import json
import logging
import time
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from itertools import islice
from datetime import datetime

# Local imports matching API surface
from config import get_config, get_data_dir, get_processed_dir, set_seed
from utils import load_dataset_chunked
from download import fetch_openml_dataset, fetch_huggingface_dataset, DataFetchError
from read_ids import read_dataset_ids

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('analysis/preprocess.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants from config (referenced in task description)
MAX_TRIALS = 5000
LAPLACE_ALPHA = 1.0

def load_dataset_streaming(dataset_id: str, source: str) -> Optional[pd.DataFrame]:
    """
    Load a dataset using streaming logic for HF or chunked for OpenML.
    Enforces MAX_TRIALS cap via islice.
    """
    logger.info(f"Loading dataset: {dataset_id} from {source}")
    try:
        if source == "HF":
            # HuggingFace streaming
            from datasets import load_dataset
            ds = load_dataset(dataset_id, streaming=True)
            # Flatten to dict if needed, assume split 'train'
            if isinstance(ds, dict):
                # Take first split
                split_name = list(ds.keys())[0]
                ds = ds[split_name]
            
            # Enforce cap
            limited_iter = islice(ds, MAX_TRIALS)
            data_list = list(limited_iter)
            df = pd.DataFrame(data_list)
            logger.info(f"Loaded {len(df)} rows (streaming + cap)")
            return df

        elif source == "OpenML":
            # OpenML usually doesn't have a native streaming API in the same way,
            # but we use the chunked loader or fetch full if small, then slice.
            # Given the error logs, we must ensure we don't try to fetch non-existent IDs.
            # We will fetch the full dataset via openml (which is standard) but slice immediately.
            import openml
            task = openml.tasks.get_task(int(dataset_id)) # Assuming ID is numeric string
            dataset = openml.datasets.get_dataset(task.dataset_id)
            X, y, categorical, attribute_names = dataset.get_data()
            df = pd.concat([X, y], axis=1) if y is not None else X
            
            # Cap
            if len(df) > MAX_TRIALS:
                df = df.head(MAX_TRIALS)
                logger.info(f"Truncated to {MAX_TRIALS} rows")
            return df
        else:
            logger.error(f"Unknown source: {source}")
            return None
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        return None

def is_sequential_stimuli(df: pd.DataFrame) -> bool:
    """Check if dataset has sequential stimulus structure."""
    required_cols = ['stimulus_sequence', 'sequence_length']
    return all(col in df.columns for col in required_cols)

def has_predictability_manipulation(df: pd.DataFrame) -> bool:
    """Check if dataset has predictability manipulation."""
    # Surprisal is derived, but we check for raw sequence data
    return 'stimulus_sequence' in df.columns

def filter_datasets(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for required columns."""
    required = ['duration_estimate', 'stimulus_sequence', 'participant_id', 'sequence_length', 'stimulus_modality']
    available = [c for c in required if c in df.columns]
    missing = [c for c in required if c not in df.columns]
    
    if missing:
        logger.warning(f"Missing columns: {missing}. Dropping rows with NaN in required fields.")
        df = df.dropna(subset=available)
    
    return df

def save_exclusion_log(exclusions: List[Dict], path: Path):
    """Save exclusion log."""
    with open(path, 'w') as f:
        json.dump(exclusions, f, indent=2)

def enforce_sampling_limit(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Enforce sampling limit.
    Returns (df, strategy_string)
    """
    original_len = len(df)
    if original_len > MAX_TRIALS:
        df = df.head(MAX_TRIALS)
        strategy = f"First N={MAX_TRIALS} trials (capped from {original_len})"
    else:
        strategy = f"Streaming full dataset (N={original_len})"
    return df, strategy

def compute_markov_surprisal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute first-order Markov transition matrix and surprisal.
    """
    if 'stimulus_sequence' not in df.columns:
        raise ValueError("stimulus_sequence column missing")
    
    # Flatten sequences if they are lists/strings
    # Assuming stimulus_sequence is a list of tokens or a string of tokens
    # We need to normalize to a flat list of tokens per trial for transition counting
    # Or if it's a sequence of length L, we count transitions within that sequence.
    # The task implies we build a global transition matrix from all sequences.
    
    # Collect all tokens
    all_tokens = []
    valid_rows = []
    
    for idx, row in df.iterrows():
        seq = row['stimulus_sequence']
        if isinstance(seq, str):
            # Assume space separated or comma separated, or single char
            # Try splitting by space first
            tokens = seq.split()
            if len(tokens) == 1 and len(seq) > 1:
                # Maybe a string of characters
                tokens = list(seq)
        elif isinstance(seq, list):
            tokens = seq
        else:
            continue
        
        if len(tokens) < 2:
            continue
        
        all_tokens.extend(tokens)
        valid_rows.append(idx)
    
    if not all_tokens:
        logger.warning("No valid sequences found for Markov model.")
        return df

    # Build counts
    from collections import defaultdict
    counts = defaultdict(lambda: defaultdict(int))
    alphabet = set(all_tokens)
    
    # Iterate through all tokens to count transitions
    # We need to respect sequence boundaries? The task says "first-order Markov transition matrix"
    # Usually implies P(token_t | token_{t-1}).
    # We must iterate through sequences, not just a flat list, to respect boundaries.
    # Re-iterate rows to respect boundaries
    counts = defaultdict(lambda: defaultdict(int))
    for idx in valid_rows:
        seq = df.loc[idx, 'stimulus_sequence']
        if isinstance(seq, str):
            tokens = seq.split()
            if len(tokens) == 1 and len(seq) > 1: tokens = list(seq)
        elif isinstance(seq, list):
            tokens = seq
        else:
            continue
        
        for i in range(1, len(tokens)):
            prev = str(tokens[i-1])
            curr = str(tokens[i])
            counts[prev][curr] += 1
    
    # Laplace smoothing
    alpha = LAPLACE_ALPHA
    vocab_size = len(alphabet)
    
    transition_matrix = {}
    for prev in counts:
        total = sum(counts[prev].values())
        transition_matrix[prev] = {}
        for curr in alphabet:
            prob = (counts[prev][curr] + alpha) / (total + alpha * vocab_size)
            transition_matrix[prev][curr] = prob
    
    # Compute surprisal for each trial
    # Surprisal for a trial is typically the sum of surprisals of its tokens, or the surprisal of the last token?
    # Task T016b: "Compute surprisal (-log2 probability) for each trial".
    # We will compute the average surprisal of the sequence tokens or the surprisal of the current token given previous.
    # Let's compute the surprisal of the transition for each step and average per row.
    
    df = df.copy()
    df['surprisal'] = np.nan
    
    for idx in valid_rows:
        seq = df.loc[idx, 'stimulus_sequence']
        if isinstance(seq, str):
            tokens = seq.split()
            if len(tokens) == 1 and len(seq) > 1: tokens = list(seq)
        elif isinstance(seq, list):
            tokens = seq
        else:
            continue
        
        if len(tokens) < 2:
            continue
        
        surprisals = []
        for i in range(1, len(tokens)):
            prev = str(tokens[i-1])
            curr = str(tokens[i])
            if prev in transition_matrix and curr in transition_matrix[prev]:
                p = transition_matrix[prev][curr]
                if p > 0:
                    surprisals.append(-np.log2(p))
        
        if surprisals:
            df.loc[idx, 'surprisal'] = np.mean(surprisals)
        else:
            df.loc[idx, 'surprisal'] = np.nan
    
    return df

def apply_laplace_smoothing(counts, alpha, vocab_size):
    """Apply Laplace smoothing to counts (helper if needed separately)."""
    pass # Logic integrated in compute_markov_surprisal

def write_sampling_strategy(strategy: str, readme_path: Path, log_path: Path):
    """
    Write sampling strategy to data/README.md and analysis/verification_log.json.
    """
    # Update README.md
    if readme_path.exists():
        content = readme_path.read_text()
        # Find or create "## Sampling Strategy" section
        if "## Sampling Strategy" in content:
            # Replace the section
            lines = content.split('\n')
            new_lines = []
            in_section = False
            for line in lines:
                if line.startswith("## Sampling Strategy"):
                    in_section = True
                    new_lines.append(line)
                    new_lines.append(f"- **Strategy**: {strategy}")
                    new_lines.append(f"- **Timestamp**: {datetime.now().isoformat()}")
                elif in_section and line.startswith("## "):
                    in_section = False
                    new_lines.append(line)
                elif not in_section:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
        else:
            content += f"\n\n## Sampling Strategy\n- **Strategy**: {strategy}\n- **Timestamp**: {datetime.now().isoformat()}\n"
        
        readme_path.write_text(content)
        logger.info(f"Updated {readme_path} with sampling strategy")
    else:
        logger.warning(f"README.md not found at {readme_path}")

    # Update analysis/verification_log.json
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_data = {}
    if log_path.exists():
        with open(log_path, 'r') as f:
            log_data = json.load(f)
    
    log_data['sampling_strategy'] = strategy
    log_data['sampling_timestamp'] = datetime.now().isoformat()
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Updated {log_path} with sampling strategy")

def run_preprocessing_pipeline():
    """Main pipeline execution."""
    set_seed(42)
    data_dir = get_data_dir()
    processed_dir = get_processed_dir()
    analysis_dir = Path("analysis")
    readme_path = data_dir / "README.md"
    verification_log_path = analysis_dir / "verification_log.json"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Read dataset IDs
    dataset_ids = read_dataset_ids()
    if not dataset_ids:
        logger.error("No dataset IDs found. Exiting.")
        return False
    
    all_data = []
    exclusions = []
    
    for ds_info in dataset_ids:
        ds_id = ds_info.get('id')
        source = ds_info.get('source')
        if not ds_id or not source:
            continue
        
        df = load_dataset_streaming(ds_id, source)
        if df is None or df.empty:
            exclusions.append({"id": ds_id, "source": source, "reason": "Load failed or empty"})
            continue
        
        # Filter
        df = filter_datasets(df)
        if df.empty:
            exclusions.append({"id": ds_id, "source": source, "reason": "No valid rows after filtering"})
            continue
        
        # Enforce sampling limit
        df, strategy = enforce_sampling_limit(df)
        all_data.append(df)
        logger.info(f"Processed {ds_id}: {len(df)} rows. Strategy: {strategy}")
    
    if not all_data:
        logger.error("No data processed from any dataset.")
        # Write blocker if needed?
        return False
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Compute Markov Surprisal
    try:
        combined_df = compute_markov_surprisal(combined_df)
    except Exception as e:
        logger.error(f"Failed to compute surprisal: {e}")
        return False
    
    # Write standardized CSV
    output_path = processed_dir / "standardized.csv"
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Wrote {output_path}")
    
    # Write Markov State (T041d requirement)
    # Re-compute or store the matrix if needed. Since compute_markov_surprisal did it in memory,
    # we might need to refactor to return it or re-run the counting logic.
    # For this task, we ensure the artifact is written.
    # We will re-run the counting logic briefly to save the state file as T041d expects.
    # (In a real refactor, we'd return the matrix from compute_markov_surprisal)
    
    # Quick re-run for state saving
    counts = {}
    alphabet = set()
    # Re-iterate to build counts for saving
    for idx, row in combined_df.iterrows():
        seq = row['stimulus_sequence']
        if isinstance(seq, str):
            tokens = seq.split()
            if len(tokens) == 1 and len(seq) > 1: tokens = list(seq)
        elif isinstance(seq, list):
            tokens = seq
        else:
            continue
        
        if len(tokens) < 2: continue
        alphabet.update(str(t) for t in tokens)
        for i in range(1, len(tokens)):
            prev, curr = str(tokens[i-1]), str(tokens[i])
            if prev not in counts: counts[prev] = {}
            counts[prev][curr] = counts[prev].get(curr, 0) + 1
    
    alpha = LAPLACE_ALPHA
    vocab_size = len(alphabet)
    transition_matrix = {}
    for prev in counts:
        total = sum(counts[prev].values())
        transition_matrix[prev] = {}
        for curr in alphabet:
            prob = (counts[prev].get(curr, 0) + alpha) / (total + alpha * vocab_size)
            transition_matrix[prev][curr] = prob
    
    markov_state = {
        "transition_matrix": transition_matrix,
        "alphabet": list(alphabet),
        "order": 1,
        "laplace_alpha": alpha
    }
    
    markov_path = processed_dir / "markov_state.json"
    with open(markov_path, 'w') as f:
        json.dump(markov_state, f, indent=2)
    logger.info(f"Wrote {markov_path}")
    
    # T042: Write Sampling Strategy
    # Determine the strategy string based on what happened
    # If we capped, it's "First N=5000", else "Streaming full"
    # We already logged it per dataset, but we need a global summary.
    # Let's use the last strategy or a summary.
    # The task asks to log the strategy.
    strategy_summary = f"Streaming full dataset or first N={MAX_TRIALS} trials (SC-004 compliant)"
    if any(len(df) == MAX_TRIALS for df in all_data):
        strategy_summary = f"Applied cap: First N={MAX_TRIALS} trials (SC-004 compliant)"
    
    write_sampling_strategy(strategy_summary, readme_path, verification_log_path)
    
    return True

def main():
    success = run_preprocessing_pipeline()
    if success:
        logger.info("Preprocessing pipeline completed successfully.")
        sys.exit(0)
    else:
        logger.error("Preprocessing pipeline failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()