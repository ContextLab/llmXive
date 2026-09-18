"""Orchestrate baseline generation for multiple seeds."""
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.llmxive.baseline_generator import generate_baseline_manifest

logger = logging.getLogger(__name__)

class BaselineOrchestrator:
    """Orchestrates baseline generation across seeds."""
    
    def __init__(self, output_dir: str = "data/processed/baseline_manifests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_baseline_for_seed(
        self,
        model_id: str,
        seed: int,
        baseline_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run baseline generation for a single seed."""
        manifest = generate_baseline_manifest(
            model_id=model_id,
            seed=seed,
            stats=baseline_stats,
            is_stable=True  # Assume stable for orchestrator
        )
        
        # Save manifest
        manifest_path = self.output_dir / f"{model_id}_{seed}.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Saved baseline manifest: {manifest_path}")
        return manifest
    
    def orchestrate_all_seeds(
        self,
        model_id: str,
        seeds: List[int],
        stats_map: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Orchestrate baseline generation for all seeds."""
        manifests = []
        for seed in seeds:
            if seed in stats_map:
                manifest = self.run_baseline_for_seed(model_id, seed, stats_map[seed])
                manifests.append(manifest)
        return manifests

def main():
    """Main entry point for baseline orchestrator."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Baseline orchestrator module loaded")
