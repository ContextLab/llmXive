"""
Wrapper script to ensure `data/raw/dense_baseline_frames.npy` is produced.
Invokes the download logic and ensures the file exists.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from eval.download_dense_baseline import main as download_main
from config import get_raw_dir, ensure_directories

def main():
    print("Ensuring Dense Baseline Data Exists...")
    ensure_directories()
    
    # The download script handles fetching and saving to the correct path
    try:
        download_main()
    except Exception as e:
        print(f"Failed to download dense baseline: {e}")
        # If download fails, we cannot proceed with dense metrics.
        # We log this but do not crash the whole pipeline if sparse is the focus,
        # though for full validation this is critical.
        return False
    
    raw_dir = get_raw_dir()
    target_file = raw_dir / "dense_baseline_frames.npy"
    
    if target_file.exists():
        print(f"Success: {target_file} exists.")
        return True
    else:
        print(f"Error: {target_file} was not created by download script.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
