"""
Script to initialize the contracts directory and generate schema files.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import schema_generator
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from utils.schema_generator import main as generate_schemas

def main() -> None:
    """Initialize contracts directory and generate schemas."""
    print("Initializing contracts directory...")
    contracts_dir = parent_dir / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = contracts_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Contract schemas for data validation."""\n')
        print(f"Created {init_file}")
    
    print("Generating schema files...")
    generate_schemas()
    print("Done.")

if __name__ == "__main__":
    main()