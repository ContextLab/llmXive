"""
Script to generate synthetic traces and write them to data/raw/ as JSON files.
This script implements Task T015: Write generated traces to data/raw/ as JSON files with ground-truth slide states.
"""
import sys
from pathlib import Path
from config import Config
from generators.synthetic_trace import generate_synthetic_traces

def main():
    """Generate synthetic traces and save to disk."""
    # Ensure we are running from the project root
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) != str(Path.cwd()):
        print(f"Warning: Running from {Path.cwd()}, expected {project_root}")
    
    config = Config()
    output_dir = str(config.data_raw_dir)
    
    print(f"Generating synthetic traces to: {output_dir}")
    print(f"Configuration seed: {config.seed}")
    
    # Generate 20 traces for initial dataset
    num_traces = 20
    generated_files = generate_synthetic_traces(
        output_dir=output_dir,
        num_traces=num_traces,
        seed=config.seed
    )
    
    print(f"Successfully generated {len(generated_files)} trace files:")
    for file_path in generated_files:
        print(f"  - {file_path}")
    
    # Verify files exist
    missing = []
    for file_path in generated_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"ERROR: The following files were not created: {missing}")
        sys.exit(1)
    
    print("Verification complete: All files exist on disk.")

if __name__ == "__main__":
    main()