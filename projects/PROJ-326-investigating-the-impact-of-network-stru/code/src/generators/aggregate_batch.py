"""
Aggregation script for combining per-topology-class batches into a global manifest.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def find_batch_files(output_dir: str) -> List[Path]:
    """Find all batch JSON files in the output directory."""
    output_path = Path(output_dir)
    return list(output_path.glob("batch_*.json"))

def load_batch_file(file_path: Path) -> Dict[str, Any]:
    """Load a single batch file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load batch file {file_path}: {e}")
        return {}

def aggregate_batches(batches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate multiple batch records into summary statistics."""
    total_generated = 0
    valid_count = 0
    total_attempts = 0
    failed_graphs = []
    
    for batch in batches:
        total_generated += batch.get("total_generated", 0)
        valid_count += batch.get("valid_count", 0)
        total_attempts += batch.get("total_attempts", 0)
        failed_graphs.extend(batch.get("failed_graphs", []))
        
    success_rate = valid_count / total_generated if total_generated > 0 else 0.0
    
    return {
        "total_generated": total_generated,
        "valid_count": valid_count,
        "success_rate": round(success_rate, 4),
        "total_attempts": total_attempts,
        "failed_graphs": failed_graphs
    }

def generate_manifest(aggregate_data: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    """Generate the global batch manifest structure."""
    return {
        "manifest_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "summary": aggregate_data
    }

def save_manifest(manifest: Dict[str, Any], output_path: str) -> None:
    """Save the manifest to the specified path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Global batch manifest saved to {output_path}")

def verify_threshold(manifest: Dict[str, Any], min_success_rate: float = 0.95) -> bool:
    """Verify if the success rate meets the threshold."""
    success_rate = manifest.get("summary", {}).get("success_rate", 0)
    return success_rate >= min_success_rate

def main():
    """Main entry point for batch aggregation."""
    parser = argparse.ArgumentParser(description="Aggregate batch generation results")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    output_dir = Path(args.output)
    batch_files = find_batch_files(str(output_dir))
    
    if not batch_files:
        logger.warning("No batch files found to aggregate.")
        # Create empty manifest
        manifest = generate_manifest({
            "total_generated": 0,
            "valid_count": 0,
            "success_rate": 0.0,
            "total_attempts": 0,
            "failed_graphs": []
        }, "no_runs")
        save_manifest(manifest, str(output_dir / "global_batch_manifest.json"))
        return
    
    batches = [load_batch_file(f) for f in batch_files]
    aggregate_data = aggregate_batches(batches)
    manifest = generate_manifest(aggregate_data, "batch_aggregation_run")
    
    save_manifest(manifest, str(output_dir / "global_batch_manifest.json"))
    
    if not verify_threshold(manifest):
        logger.warning(f"Success rate {aggregate_data['success_rate']} is below threshold 0.95")
    else:
        logger.info(f"Success rate {aggregate_data['success_rate']} meets threshold")

if __name__ == "__main__":
    main()
