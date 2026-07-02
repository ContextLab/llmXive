"""
Runner script to execute T004: Fetch COD sample IDs and save to data/raw/cod_sample_ids.txt.
This script ensures the artifact is generated on disk as required by the task.
"""
import os
import sys
from pathlib import Path

# Add the project root to the path to allow imports from code/utils
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.data_loaders import fetch_cod_sample_ids

def main():
    output_file = project_root / "data" / "raw" / "cod_sample_ids.txt"
    
    print(f"Fetching COD sample IDs from canonical URL...")
    print(f"Output will be written to: {output_file}")
    
    try:
        ids = fetch_cod_sample_ids(str(output_file))
        
        if not output_file.exists():
            raise FileNotFoundError(f"Output file {output_file} was not created.")
        
        line_count = len(output_file.read_text().splitlines())
        
        print(f"Success! Downloaded {len(ids)} IDs.")
        print(f"File saved to: {output_file}")
        print(f"Verification: File contains {line_count} lines.")
        
        if line_count < 100:
            print("WARNING: File contains fewer than 100 lines. Task verification may fail.")
            sys.exit(1)
            
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
