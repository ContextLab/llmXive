import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_human_ratings_exist(base_path: Path = None) -> bool:
    """
    Check if the human ratings file exists at the expected location.
    
    Args:
        base_path: Base project path (defaults to current working directory)
        
    Returns:
        True if file exists, False otherwise
    """
    if base_path is None:
        base_path = Path.cwd()
    
    human_ratings_path = base_path / "data" / "raw" / "human_ratings.json"
    return human_ratings_path.exists()

def load_human_ratings(base_path: Path = None) -> dict:
    """
    Load human ratings data if it exists.
    
    Args:
        base_path: Base project path
        
    Returns:
        Dictionary containing human ratings data
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    if base_path is None:
        base_path = Path.cwd()
    
    human_ratings_path = base_path / "data" / "raw" / "human_ratings.json"
    
    if not human_ratings_path.exists():
        raise FileNotFoundError(f"Human ratings file not found at {human_ratings_path}")
    
    with open(human_ratings_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_assumption_validated_flag(status: str, reason: str) -> dict:
    """
    Prepare the status dictionary for the assumption validation.
    
    Args:
        status: Either 'present' or 'missing'
        reason: Explanation for the status
        
    Returns:
        Dictionary with status and reason
    """
    return {
        "status": status,
        "reason": reason
    }

def update_state_with_human_ratings_check(state_path: Path, status: str, reason: str):
    """
    Update the state.yaml file with the human ratings check result.
    
    Args:
        state_path: Path to the state.yaml file
        status: Either 'present' or 'missing'
        reason: Explanation for the status
    """
    import yaml
    
    # Read existing state or create new
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            state_data = yaml.safe_load(f) or {}
    else:
        state_data = {}
    
    # Update with human ratings check result
    if 'human_ratings_check' not in state_data:
        state_data['human_ratings_check'] = {}
    
    state_data['human_ratings_check']['status'] = status
    state_data['human_ratings_check']['reason'] = reason
    state_data['human_ratings_check']['checked_at'] = str(Path.cwd())
    
    # Write updated state
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state.yaml with human ratings check: {status}")

def main():
    """
    Main function to check for human ratings data and write status.
    """
    parser = argparse.ArgumentParser(description='Check for human ratings data existence')
    parser.add_argument('--project-root', type=str, default=None,
                      help='Path to project root (default: current directory)')
    parser.add_argument('--output-dir', type=str, default='data/metrics',
                      help='Directory to write output file (default: data/metrics)')
    parser.add_argument('--state-file', type=str, default='state.yaml',
                      help='Path to state.yaml file (default: state.yaml)')
    
    args = parser.parse_args()
    
    # Set up paths
    if args.project_root:
        base_path = Path(args.project_root)
    else:
        base_path = Path.cwd()
    
    output_dir = base_path / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "human_data_status.json"
    state_file = base_path / args.state_file
    
    # Check for human ratings file
    human_ratings_path = base_path / "data" / "raw" / "human_ratings.json"
    
    if human_ratings_path.exists():
        status = "present"
        reason = f"Human ratings file found at {human_ratings_path}"
        logger.info(f"Human ratings data is present: {human_ratings_path}")
        
        # Optionally load and validate structure
        try:
            data = load_human_ratings(base_path)
            if isinstance(data, dict) and len(data) > 0:
                reason += f" (contains {len(data)} rating entries)"
            else:
                reason += " (file exists but appears empty or invalid)"
        except Exception as e:
            reason += f" (error reading file: {str(e)})"
    else:
        status = "missing"
        reason = f"Human ratings file not found at {human_ratings_path}. Assumption validated: proxy MOS will be used without human correlation check."
        logger.info(f"Human ratings data is missing: {human_ratings_path}")
    
    # Write status to output file
    status_data = prepare_assumption_validated_flag(status, reason)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Wrote human data status to {output_file}")
    
    # Update state.yaml
    if state_file.exists():
        update_state_with_human_ratings_check(state_file, status, reason)
    else:
        logger.warning(f"State file not found at {state_file}. Skipping state update.")
    
    # Print summary
    print(f"\n=== Human Ratings Data Check ===")
    print(f"Status: {status}")
    print(f"Reason: {reason}")
    print(f"Output file: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
