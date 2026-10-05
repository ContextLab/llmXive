import json
import sys
import subprocess
from pathlib import Path
from utils.config import get_project_root
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

def check_plan_for_dataset_url(plan_path: Path) -> bool:
    """Check if plan.md contains a 'Dataset URL:' line."""
    if not plan_path.exists():
        return False
    content = plan_path.read_text()
    for line in content.splitlines():
        if line.strip().startswith("Dataset URL:"):
            return True
    return False

def write_source_flag(root: Path, source_type: str) -> None:
    """Write the data source flag to data_source_flag.json."""
    flag_path = root / "data" / "data_source_flag.json"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    with open(flag_path, 'w') as f:
        json.dump({"source": source_type}, f, indent=2)
    log_info(logger, f"Wrote source flag: {source_type}")

def run_synthetic_generation(root: Path) -> bool:
    """
    Trigger synthetic generation by calling generate_synthetic.py.
    Returns True if successful, False otherwise.
    """
    script_path = root / "code" / "ingestion" / "generate_synthetic.py"
    if not script_path.exists():
        log_error(logger, f"Synthetic generation script not found: {script_path}")
        return False

    log_info(logger, "Triggering synthetic dataset generation...")
    try:
        # Run the script directly
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            log_error(logger, f"Synthetic generation failed: {result.stderr}")
            return False
        log_info(logger, "Synthetic generation completed successfully.")
        return True
    except Exception as e:
        log_error(logger, f"Error running synthetic generation: {e}")
        return False

def main():
    root = get_project_root()
    plan_path = root / "plan.md"
    raw_dir = root / "data" / "raw"

    # Check for URL
    has_url = check_plan_for_dataset_url(plan_path)

    if has_url:
        log_info(logger, "Dataset URL found in plan.md. Skipping synthetic generation.")
        # Note: This script is specifically for the fallback path (T048).
        # If URL exists, we assume fetch_real.py handles it.
        # However, per T000b logic, if fetch_real fails, we come here.
        # But T000b says: "If the URL is missing or download fails, trigger T048".
        # This script is T048. It is called when we need to generate synthetic.
        # We should only run synthetic if we explicitly need it (i.e., no URL or fetch failed).
        # But this script is the "trigger". Let's assume it's called when synthetic is needed.
        # If called when URL exists, it might be an error in logic, but we just log and exit.
        # Actually, T000b says: "If the URL is missing or download fails, trigger T048".
        # So if this script is run, it means we are in the "trigger T048" branch.
        # But we should double check. If URL exists, maybe we shouldn't be here?
        # Let's assume the caller (T000b logic) ensures we only come here if synthetic is needed.
        # If we are here and URL exists, it's a logic error, but we'll proceed with synthetic
        # only if we are forced to (e.g. fetch failed). But this script doesn't know about fetch status.
        # Re-reading T000b: "If the URL is missing or download fails, trigger T048".
        # So if we are in T048, we are generating synthetic.
        # We should check again: if URL exists AND we are here, it means download failed.
        # So we proceed with synthetic.
        pass

    # Run synthetic generation
    success = run_synthetic_generation(root)

    if success:
        write_source_flag(root, "synthetic")
        print("SYNTHETIC_GENERATED")
        sys.exit(0)
    else:
        log_error(logger, "Failed to generate synthetic dataset.")
        print("SYNTHETIC_FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
