import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Set, List
import pandas as pd

from config import get_data_dir, get_output_dir, ensure_directories

logger = logging.getLogger(__name__)

# --- State Management ---
STATE_FILE = "project_state.json"

def load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"checksums": {}, "last_run": {}, "metrics": {}}

def save_state(state: Dict[str, Any]) -> None:
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def record_checksum(file_path: str, hash_value: str) -> None:
    state = load_state()
    state["checksums"][file_path] = hash_value
    save_state(state)

# --- Data Loading ---
def compute_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_defects4j_data() -> Path:
    """
    Fetches Defects4J parquet data from the verified HuggingFace URL.
    Caches to data/defects4j_v1.0.parquet.
    """
    data_dir = get_data_dir()
    ensure_directories()
    output_path = data_dir / "defects4j_v1.0.parquet"

    if output_path.exists():
        logger.info(f"Data file already exists at {output_path}. Skipping fetch.")
        return output_path

    logger.info(f"Fetching Defects4J data to {output_path}...")
    try:
        from datasets import load_dataset
        # Verified source: defects4j/defects4j-parquet, v1.0.parquet
        # Using streaming to handle potential size, then collecting to DataFrame
        ds = load_dataset("defects4j/defects4j-parquet", split="train", streaming=True)
        
        df_chunks = []
        # Iterate through the dataset to build the dataframe
        # Note: This assumes the dataset fits in memory for the chunking logic.
        # If memory is an issue, we could process in batches, but parquet write usually needs a full df or append.
        # For Defects4J v1, it is small enough (< 1GB).
        for batch in ds:
            df = pd.DataFrame(batch)
            df_chunks.append(df)
        
        if not df_chunks:
            raise ValueError("Dataset is empty.")
        
        full_df = pd.concat(df_chunks, ignore_index=True)
        full_df.to_parquet(output_path, index=False)
        
        logger.info(f"Data saved to {output_path}")
        
        # Record checksum immediately after saving (Fix for T006b)
        checksum = compute_sha256(str(output_path))
        record_checksum(str(output_path), checksum)
        logger.info(f"Checksum recorded: {checksum}")
        
        return output_path

    except Exception as e:
        logger.error(f"Failed to fetch Defects4J data: {e}")
        raise RuntimeError("Could not fetch real Defects4J data. Execution halted.")

def load_defects4j_data() -> pd.DataFrame:
    """Loads the cached parquet file."""
    data_dir = get_data_dir()
    file_path = data_dir / "defects4j_v1.0.parquet"
    if not file_path.exists():
        raise FileNotFoundError(f"Defects4J data not found at {file_path}. Run fetch_defects4j_data first.")
    return pd.read_parquet(file_path)

def verify_data_integrity() -> bool:
    """Verifies the checksum of the cached data matches the recorded state."""
    data_dir = get_data_dir()
    file_path = data_dir / "defects4j_v1.0.parquet"
    if not file_path.exists():
        return False
    
    current_hash = compute_sha256(str(file_path))
    state = load_state()
    recorded_hash = state.get("checksums", {}).get(str(file_path))
    
    if recorded_hash is None:
        logger.warning(f"No recorded checksum for {file_path}.")
        return False
    
    if current_hash != recorded_hash:
        logger.error(f"Checksum mismatch for {file_path}.")
        return False
    
    return True

def ensure_data_loaded_and_integrity_recorded() -> Path:
    """Ensures data is fetched and checksum is recorded."""
    if not verify_data_integrity():
        logger.info("Data integrity check failed or missing. Fetching...")
        return fetch_defects4j_data()
    return get_data_dir() / "defects4j_v1.0.parquet"

# --- New Function: Extract Changed Lines ---
def extract_changed_lines() -> Dict[str, Set[int]]:
    """
    Parses Defects4J commit diffs from the cached parquet file.
    Extracts line numbers (integers) that were added or modified.
    Outputs a JSON file: data/changed_lines.json
    Format: { "project_id": [line1, line2, ...], ... }
    
    Returns the dictionary for immediate use.
    """
    logger.info("Extracting changed lines from Defects4J data...")
    df = load_defects4j_data()
    
    # Ensure required columns exist
    # Defects4J parquet usually contains 'project', 'bug_id', 'diff' or 'patch'
    # We assume 'diff' contains the unified diff text.
    required_cols = ['project', 'bug_id', 'diff']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    
    changed_lines_map = {}
    
    for _, row in df.iterrows():
        project_id = f"{row['project']}_{row['bug_id']}"
        diff_text = str(row['diff'])
        
        lines = set()
        if not diff_text or diff_text.strip() == "":
            changed_lines_map[project_id] = lines
            continue
        
        # Parse unified diff to extract line numbers
        # Unified diff format:
        # @@ -old_start,old_count +new_start,new_count @@
        # - removed line
        # + added line
        #   context line
        #
        # We are interested in lines that are ADDED or MODIFIED (start with '+').
        # We track the current line number in the 'new' file.
        
        current_new_line = 0
        in_hunk = False
        
        for line in diff_text.splitlines():
            if line.startswith('@@'):
                # Parse header: @@ -old_start,old_count +new_start,new_count @@
                try:
                    parts = line.split()
                    # parts[1] is usually "+new_start,new_count"
                    plus_part = parts[1]
                    if '+' in plus_part:
                        start_str, count_str = plus_part[1:].split(',')
                        current_new_line = int(start_str)
                    in_hunk = True
                except (IndexError, ValueError):
                    in_hunk = False
                continue
            
            if not in_hunk:
                continue
            
            if line.startswith('+'):
                # Added line
                lines.add(current_new_line)
                current_new_line += 1
            elif line.startswith('-'):
                # Removed line - do not increment new line counter
                pass
            elif line.startswith(' '):
                # Context line - increment both
                current_new_line += 1
            elif line.startswith('\\'):
                # No newline at end of file marker
                pass
            else:
                # Potential format error or other diff style, skip
                pass
        
        changed_lines_map[project_id] = lines

    # Write to JSON
    data_dir = get_data_dir()
    ensure_directories()
    output_path = data_dir / "changed_lines.json"
    
    # Convert sets to lists for JSON serialization
    serializable_map = {k: sorted(list(v)) for k, v in changed_lines_map.items()}
    
    with open(output_path, 'w') as f:
        json.dump(serializable_map, f, indent=2)
    
    logger.info(f"Changed lines extracted and saved to {output_path}")
    logger.info(f"Total projects processed: {len(changed_lines_map)}")
    
    return serializable_map

def extract_bug_fix_description(project_id: str, df: Optional[pd.DataFrame] = None) -> str:
    """
    Extracts and formats the bug fix description for a given project.
    If df is not provided, loads the data.
    """
    if df is None:
        df = load_defects4j_data()
    
    # Assuming columns: project, bug_id, description, fix_description
    # We look for a 'description' or 'summary' column, or construct from 'diff'
    if 'description' in df.columns:
        desc = df.loc[(df['project'] == project_id.split('_')[0]) & (df['bug_id'] == int(project_id.split('_')[1])), 'description']
        if not desc.empty:
            return desc.iloc[0]
    
    if 'summary' in df.columns:
         desc = df.loc[(df['project'] == project_id.split('_')[0]) & (df['bug_id'] == int(project_id.split('_')[1])), 'summary']
         if not desc.empty:
             return desc.iloc[0]
     
    # Fallback: Use diff as description if no text summary
    diff = df.loc[(df['project'] == project_id.split('_')[0]) & (df['bug_id'] == int(project_id.split('_')[1])), 'diff']
    if not diff.empty:
        return f"Fix description (from diff):\n{diff.iloc[0][:500]}"
    
    return "No description available for this bug."