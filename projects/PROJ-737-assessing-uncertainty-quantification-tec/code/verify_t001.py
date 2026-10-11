import yaml
import pathlib
import sys
from create_skeleton import main as skeleton_main

def main():
    """
    Implements the verification logic for T001 as specified in tasks.md.
    1. Ensures project skeleton (directories and schema) is created.
    2. Verifies the schema contains the required columns.
    3. Verifies the required directories exist.
    """
    # Step 1: Create/Verify skeleton
    # This calls the existing create_skeleton.main() which handles directory creation
    # and writing the schema file.
    skeleton_main()

    # Step 2: Schema verification
    schema_path = pathlib.Path('specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml')
    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        sys.exit(1)

    try:
        schema = yaml.safe_load(schema_path.read_text())
        cols = {c['name'] for c in schema['columns']}
        required = {'sample_id', 'dataset', 'method', 'prediction', 'lower_bound', 'upper_bound', 'ground_truth', 'abs_error'}
        
        if cols != required:
            print(f"Schema mismatch. Missing columns: {required - cols}. Extra columns: {cols - required}")
            sys.exit(1)
    except Exception as e:
        print(f"Error parsing schema YAML: {e}")
        sys.exit(1)

    # Step 3: Directory verification
    # The verification snippet specifically checks these three
    for d in ['data/processed', 'data/results', 'figures']:
        if not pathlib.Path(d).is_dir():
            print(f"Missing required directory: {d}")
            sys.exit(1)

    print("Schema and directory verification passed")

if __name__ == "__main__":
    main()