import sys
import argparse
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.pipeline.manifest import generate_manifest, write_manifest
from src.pipeline.state_updater import update_state_with_manifest

def main():
    parser = argparse.ArgumentParser(description="Generate Manifest and Update State")
    parser.add_argument('--root', type=str, default='code', help='Root directory to hash (default: code)')
    parser.add_argument('--data-dir', type=str, default='data/processed', help='Data directory to hash (default: data/processed)')
    parser.add_argument('--output', type=str, default='data/processed/manifest.json', help='Output manifest path')
    parser.add_argument('--state-file', type=str, default='state/projects/PROJ-829-llmxive-follow-up-extending-fashionchame.yaml', help='State file to update')
    args = parser.parse_args()

    # 1. Generate manifest for code/
    print(f"Generating manifest for code/...")
    code_manifest = generate_manifest(args.root)
    
    # 2. Generate manifest for data/processed/
    print(f"Generating manifest for {args.data_dir}...")
    data_manifest = generate_manifest(args.data_dir)

    # 3. Merge manifests
    merged_manifest = {
        "metadata": {
            "generated_at": code_manifest.get("metadata", {}).get("generated_at"),
            "sources": [args.root, args.data_dir]
        },
        "files": {
            **code_manifest.get("files", {}),
            **data_manifest.get("files", {})
        }
    }

    # 4. Write combined manifest
    write_manifest(merged_manifest, args.output)

    # 5. Update state file with the manifest checksums
    print(f"Updating state file {args.state_file}...")
    update_state_with_manifest(args.output, args.state_file)

    print("Task T038 completed: Manifest generated and state updated.")

if __name__ == '__main__':
    main()
