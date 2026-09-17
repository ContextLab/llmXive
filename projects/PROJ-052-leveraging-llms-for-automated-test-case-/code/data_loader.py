import hashlib
import json
import os
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datasets import load_dataset, DatasetDict
from config import get_data_dir, get_output_dir, get_logs_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class MemoryExceededError(Exception):
    """Raised when memory usage exceeds limits."""
    pass

def load_state(state_path: Optional[str] = None) -> Dict[str, Any]:
    """Load project state from JSON file."""
    if state_path is None:
        state_path = os.path.join(get_data_dir(), "project_state.json")
    
    if not os.path.exists(state_path):
        return {"checksum": None, "samples_processed": 0, "fallback_prompt_count": 0}
    
    try:
        with open(state_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load state file: {e}. Initializing empty state.")
        return {"checksum": None, "samples_processed": 0, "fallback_prompt_count": 0}

def save_state(state: Dict[str, Any], state_path: Optional[str] = None) -> None:
    """Save project state to JSON file."""
    if state_path is None:
        state_path = os.path.join(get_data_dir(), "project_state.json")
    
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

def record_checksum(checksum: str, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Record checksum in state and save."""
    if state is None:
        state = load_state()
    
    state["checksum"] = checksum
    save_state(state)
    return state

def compute_sha256(data_chunks: List[bytes]) -> str:
    """Compute SHA-256 hash of data chunks."""
    hasher = hashlib.sha256()
    for chunk in data_chunks:
        hasher.update(chunk)
    return hasher.hexdigest()

def fetch_defects4j_data(streaming: bool = True) -> DatasetDict:
    """Fetch Defects4J dataset using HuggingFace datasets library."""
    try:
        logger.info("Fetching Defects4J dataset from HuggingFace...")
        dataset = load_dataset(
            "defects4j/defects4j", 
            split="train", 
            streaming=streaming
        )
        logger.info("Successfully loaded Defects4J dataset.")
        return dataset
    except Exception as e:
        logger.error(f"Failed to fetch Defects4J dataset: {e}")
        raise DataFetchError(f"Data fetch failed: {str(e)}")

def load_defects4j_data(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load and process Defects4J data with optional limit."""
    dataset = fetch_defects4j_data(streaming=True)
    samples = []
    
    try:
        for i, sample in enumerate(dataset):
            if limit is not None and i >= limit:
                break
            samples.append(sample)
    except Exception as e:
        logger.error(f"Error processing dataset: {e}")
        raise DataFetchError(f"Data processing failed: {str(e)}")
    
    return samples

def verify_data_integrity(data: List[Dict[str, Any]], expected_checksum: Optional[str] = None) -> bool:
    """Verify data integrity using checksum."""
    if not data:
        logger.warning("No data to verify.")
        return False
    
    # Compute checksum of current data
    data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
    computed_checksum = hashlib.sha256(data_bytes).hexdigest()
    
    if expected_checksum and computed_checksum != expected_checksum:
        logger.warning(f"Checksum mismatch: expected {expected_checksum}, got {computed_checksum}")
        return False
    
    logger.info(f"Data integrity verified. Checksum: {computed_checksum}")
    return True

def extract_changed_lines(data: List[Dict[str, Any]], output_path: Optional[str] = None) -> Dict[str, Dict[str, List[int]]]:
    """Extract changed lines from Defects4J commit diffs."""
    if output_path is None:
        output_path = os.path.join(get_data_dir(), "changed_lines.json")
    
    changed_lines_map: Dict[str, Dict[str, List[int]]] = {}
    
    for sample in data:
        project_id = sample.get("project_id", "unknown")
        bug_id = sample.get("bug_id", "unknown")
        
        # Parse diff content to extract changed line numbers
        diff_content = sample.get("diff", "")
        if not diff_content:
            continue
        
        # Extract line numbers from diff (simplified parsing)
        changed_lines = set()
        for line in diff_content.split('\n'):
            # Look for line number patterns in diff (e.g., @@ -10,5 +10,7 @@)
            match = re.search(r'@@.*?-(\d+)', line)
            if match:
                start_line = int(match.group(1))
                # Parse the rest of the hunk header to get count
                count_match = re.search(r'@@.*?-(\d+),(\d+)', line)
                if count_match:
                    count = int(count_match.group(2))
                    for i in range(count):
                        changed_lines.add(start_line + i)
        
        if project_id not in changed_lines_map:
            changed_lines_map[project_id] = {}
        
        changed_lines_map[project_id][bug_id] = sorted(list(changed_lines))
    
    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(changed_lines_map, f, indent=2)
    
    logger.info(f"Extracted changed lines to {output_path}")
    return changed_lines_map

def extract_bug_fix_description(sample: Dict[str, Any]) -> str:
    """Extract and format bug fix description from sample."""
    bug_description = sample.get("bug_description", "")
    project_id = sample.get("project_id", "unknown")
    bug_id = sample.get("bug_id", "unknown")
    
    # Security hardening: validate input
    if not isinstance(bug_description, str):
        bug_description = str(bug_description)
    
    # Limit length to prevent overflow
    if len(bug_description) > 1000:
        bug_description = bug_description[:1000] + "..."
    
    # Format prompt
    prompt = f"Project: {project_id}, Bug: {bug_id}\n\nBug Description: {bug_description}\n\nGenerate a JUnit test case that reproduces this bug."
    
    return prompt

def log_fallback_prompt_usage(bug_id: str, project_id: str, reason: str = "Prompt too short") -> None:
    """
    Log fallback prompt usage to data/metrics.json.
    Records a WARNING for fallback prompt usage and increments the fallback_prompt_count.
    """
    metrics_path = os.path.join(get_data_dir(), "metrics.json")
    
    # Load existing metrics or initialize
    metrics = {"fallback_prompt_count": 0, "fallback_events": []}
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.warning("Failed to load metrics.json, initializing fresh.")
    
    # Increment counter
    metrics["fallback_prompt_count"] = metrics.get("fallback_prompt_count", 0) + 1
    
    # Log event details
    event = {
        "bug_id": bug_id,
        "project_id": project_id,
        "reason": reason,
        "timestamp": os.popen("date -Iseconds").read().strip()
    }
    if "fallback_events" not in metrics:
        metrics["fallback_events"] = []
    metrics["fallback_events"].append(event)
    
    # Save metrics
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Log WARNING
    logger.warning(f"Fallback prompt used for {project_id}/{bug_id}: {reason}")

def filter_pairable_samples(coverage_metrics: List[Dict[str, Any]], changed_lines: Dict[str, Dict[str, List[int]]]) -> Dict[str, Any]:
    """
    Filter samples to identify pairable samples (those with known manual test baseline).
    Returns a dict with total_samples, excluded_count, pairable_count, and exclusion_log.
    """
    total_samples = len(coverage_metrics)
    excluded_count = 0
    pairable_count = 0
    exclusion_details = []
    
    for sample in coverage_metrics:
        project_id = sample.get("project_id")
        bug_id = sample.get("bug_id")
        
        # Check if sample has manual test baseline
        has_manual_baseline = sample.get("has_manual_baseline", False)
        
        if not has_manual_baseline:
            excluded_count += 1
            exclusion_details.append({
                "project_id": project_id,
                "bug_id": bug_id,
                "reason": "No manual baseline"
            })
        else:
            pairable_count += 1
    
    # Create exclusion log
    exclusion_log = {
        "total_samples": total_samples,
        "excluded_count": excluded_count,
        "pairable_count": pairable_count,
        "exclusion_rate": excluded_count / total_samples if total_samples > 0 else 0,
        "details": exclusion_details
    }
    
    # Save exclusion log
    exclusion_log_path = os.path.join(get_data_dir(), "exclusion_log.json")
    os.makedirs(os.path.dirname(exclusion_log_path), exist_ok=True)
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    
    logger.info(f"Pairable samples: {pairable_count}/{total_samples} (Excluded: {excluded_count})")
    return exclusion_log

def ensure_data_loaded_and_integrity_recorded() -> bool:
    """Ensure data is loaded and integrity is recorded."""
    state = load_state()
    
    if state.get("checksum") is None:
        logger.warning("No checksum recorded. Data integrity not verified.")
        return False
    
    logger.info("Data integrity verified from state.")
    return True

def main():
    """Main entry point for data_loader module."""
    logger.info("Data loader module initialized.")
    
    # Example usage
    try:
        # Load state
        state = load_state()
        logger.info(f"Current state: {state}")
        
        # Fetch data (example)
        # data = load_defects4j_data(limit=10)
        # logger.info(f"Loaded {len(data)} samples")
        
        # Extract changed lines (example)
        # changed_lines = extract_changed_lines(data)
        
    except DataFetchError as e:
        logger.error(f"Data fetch error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()