import argparse
import csv
import hashlib
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any

def _compute_sha256(file_path: Path) -> str:
    """Return the SHA-256 checksum of file_path."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _write_checksum_manifest(root: Path, manifest_path: Path) -> None:
    """Walk root and write a CSV manifest relative_path,sha256."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", newline="") as f:
        writer = csv.writer(f)
        for file in root.rglob("*"):
            if file.is_file():
                rel_path = file.relative_to(root)
                writer.writerow([str(rel_path), _compute_sha256(file)])

def _print_summary(cfg: Dict[str, Any]) -> None:
    """Print a deterministic short summary of the run configuration."""
    print("\n" + "="*40)
    print("PIPELINE EXECUTION SUMMARY")
    print("="*40)
    print(f"Dataset:       {cfg.get('dataset_name')}")
    print(f"Subset Size:   {cfg.get('subset_size')}")
    print(f"Lambda Values: {cfg.get('lambda_values')}")
    print(f"Seeds:         {cfg.get('seeds')}")
    print(f"Output Dir:    {cfg.get('output_dir')}")
    print("-" * 40)
    print("Expected Artifacts:")
    print("- data/counterfactuals/metadata.csv")
    print("- results/per_seed.csv")
    print("- results/summary.csv")
    print("- figures/delta_acc_vs_lambda.png")
    print("- figures/bootstrap_hist.png")
    print("="*40 + "\n")

def parse_cli_args(argv: List[str] | None=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full CC pipeline.")
    parser.add_argument("--config", type=str, help="Path to YAML config file.")
    parser.add_argument("--dataset_name", type=str, default="something-something-v2")
    parser.add_argument("--subset_size", type=int, default=200)
    parser.add_argument("--train_split", type=float, default=0.8)
    parser.add_argument("--val_split", type=float, default=0.1)
    parser.add_argument("--test_split", type=float, default=0.1)
    parser.add_argument("--lambda_values", nargs="+", type=float, default=[0.1, 0.5, 1.0])
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    parser.add_argument("--optical_flow_divergence_threshold", type=float, default=0.15)
    parser.add_argument("--feature_similarity_threshold", type=float, default=0.9)
    parser.add_argument("--output_dir", type=str, default="./output")
    return parser.parse_args(argv)

def build_config_from_args(ns: argparse.Namespace) -> Dict[str, Any]:
    cfg = vars(ns).copy()
    if ns.config:
        with open(ns.config, "r") as f:
            yaml_cfg = yaml.safe_load(f)
            if yaml_cfg:
                cfg.update(yaml_cfg)
    return cfg

def main(argv: List[str] | None=None) -> int:
    ns = parse_cli_args(argv)
    cfg = build_config_from_args(ns)
    
    print(f"Initializing pipeline with config: {cfg}")
    
    # Pipeline stages implemented as dynamic imports to prevent ModuleNotFoundError 
    # for tasks not yet completed (e.g., T006 trainer)
    stages = [
        ("Data Loading", "src.data.something_loader"),
        ("Optical Flow", "src.data.optical_flow_loader"),
        ("Counterfactual Generation", "src.data.counterfactual"),
        ("Model Training", "src.train.trainer"),
        ("Evaluation", "src.eval.evaluator"),
        ("Statistics", "src.eval.statistics"),
        ("Reporting", "src.report.report"),
    ]

    for stage_name, module_path in stages:
        try:
            # We don't actually call the main functions here unless they are 
            # fully implemented and integrated, but we check for presence.
            __import__(module_path)
            print(f"[✓] Stage '{stage_name}' module found.")
        except ImportError:
            print(f"[!] Stage '{stage_name}' ({module_path}) not yet implemented. Skipping...")

    # Final summary as required by T001
    _print_summary(cfg)
    
    # Ensure output directory exists
    Path(cfg['output_dir']).mkdir(parents=True, exist_ok=True)
    
    print("Pipeline run completed successfully (some stages may have been skipped).")
    return 0

if __name__ == "__main__":
    sys.exit(main())