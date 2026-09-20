"""
Reproducibility Audit Script for llmXive Co-Evolving Pipeline.

This script verifies that re-running the entire pipeline with the exact same seeds
from data/batch_config.json produces bit-for-bit identical checksums and final metrics.
"""

import json
import os
import sys
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import load_config, Config
from src.utils.checksums import compute_file_sha256, load_checksums, save_checksums
from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator
from src.generators.test_generator import TestInstanceGenerator
from src.generators.data_writer import write_dataset, register_checksum
from src.agents.sequential_agent import SequentialAgent
from src.agents.mixed_agent import MixedAgent
from src.agents.coevolving_agent import CoevolvingAgent
from src.analysis.forgetting_metrics import compute_forgetting_metrics, compute_retention_metrics
from src.analysis.statistical_tests import run_statistical_analysis
from src.analysis.report_generator import generate_final_report
from src.analysis.data_aggregator import collect_results_from_directory, aggregate_batch_results

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReproducibilityError(Exception):
    """Raised when reproducibility check fails."""
    pass

def load_batch_config() -> Dict[str, Any]:
    """Load the batch configuration containing seeds."""
    config_path = PROJECT_ROOT / "data" / "batch_config.json"
    if not config_path.exists():
        raise ReproducibilityError(f"Batch config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def get_baseline_checksums() -> Dict[str, str]:
    """Load baseline checksums from previous run."""
    checksum_path = PROJECT_ROOT / "data" / "checksums.json"
    if not checksum_path.exists():
        raise ReproducibilityError(f"Baseline checksums not found: {checksum_path}")
    
    return load_checksums(checksum_path)

def get_baseline_metrics() -> Dict[str, Any]:
    """Load baseline forgetting analysis results."""
    metrics_path = PROJECT_ROOT / "data" / "results" / "forgetting_analysis.json"
    if not metrics_path.exists():
        raise ReproducibilityError(f"Baseline metrics not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def regenerate_data(config: Config, seeds: List[int]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Regenerate all data using provided seeds and return checksums."""
    logger.info("Regenerating training data...")
    
    # Logic proofs
    logic_gen = LogicProofGenerator(config)
    proofs_data = []
    for i, seed in enumerate(seeds):
        random.seed(seed)
        proofs = logic_gen.generate_proofs(count=10, seed=seed)
        proofs_data.extend(proofs)
    
    # Grid worlds
    grid_gen = GridWorldGenerator(config)
    grids_data = []
    for i, seed in enumerate(seeds):
        random.seed(seed + 1000000)  # Offset to ensure different seeds
        grids = grid_gen.generate_grids(count=10, seed=seed)
        grids_data.extend(grids)
    
    # Test instances
    test_gen = TestInstanceGenerator(config)
    random.seed(config.TEST_SEED_START)
    test_instances = test_gen.generate_test_instances(count=50)
    
    # Write data
    proofs_path = PROJECT_ROOT / "data" / "generated_proofs_repro.json"
    grids_path = PROJECT_ROOT / "data" / "generated_grids_repro.json"
    test_path = PROJECT_ROOT / "data" / "test_instances_repro.json"
    
    write_dataset(proofs_data, proofs_path)
    write_dataset(grids_data, grids_path)
    write_dataset(test_instances, test_path)
    
    # Calculate checksums
    checksums = {
        "generated_proofs_repro.json": compute_file_sha256(proofs_path),
        "generated_grids_repro.json": compute_file_sha256(grids_path),
        "test_instances_repro.json": compute_file_sha256(test_path),
    }
    
    return {
        "proofs": proofs_data,
        "grids": grids_data,
        "test_instances": test_instances
    }, checksums

def run_training(data: Dict[str, Any], config: Config, seeds: List[int]) -> Dict[str, Any]:
    """Run training for all three conditions."""
    logger.info("Running training for all conditions...")
    
    results = {}
    
    # Sequential
    logger.info("Training SequentialAgent...")
    seq_agent = SequentialAgent(config)
    seq_agent.train(data["proofs"][:100], data["grids"][:100], seeds=seeds[:30])
    results["sequential"] = seq_agent.get_state()
    
    # Mixed
    logger.info("Training MixedAgent...")
    mixed_agent = MixedAgent(config)
    mixed_agent.train(data["proofs"][:100], data["grids"][:100], seeds=seeds[:30])
    results["mixed"] = mixed_agent.get_state()
    
    # Co-evolving
    logger.info("Training CoevolvingAgent...")
    coevo_agent = CoevolvingAgent(config)
    coevo_agent.train(data["proofs"][:100], data["grids"][:100], seeds=seeds[:30])
    results["coevolving"] = coevo_agent.get_state()
    
    return results

def evaluate_agents(
    agent_states: Dict[str, Any], 
    test_instances: List[Dict[str, Any]], 
    config: Config
) -> Dict[str, Any]:
    """Evaluate all agents and compute metrics."""
    logger.info("Evaluating agents...")
    
    forgetting_results = {}
    retention_results = {}
    
    for condition, state in agent_states.items():
        logger.info(f"Evaluating {condition}...")
        
        # Load agent state (simulated)
        forgetting_result = compute_forgetting_metrics(
            state, 
            test_instances, 
            config
        )
        forgetting_results[condition] = forgetting_result
        
        retention_result = compute_retention_metrics(
            state,
            test_instances,
            config
        )
        retention_results[condition] = retention_result
    
    return {
        "forgetting": forgetting_results,
        "retention": retention_results
    }

def run_statistical_analysis(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Run full statistical analysis."""
    logger.info("Running statistical analysis...")
    
    # Prepare data for analysis
    forgetting_data = metrics["forgetting"]
    retention_data = metrics["retention"]
    
    # Run ANOVA and Tukey tests
    anova_result = run_statistical_analysis(forgetting_data, retention_data)
    
    return anova_result

def generate_final_report(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate final report."""
    logger.info("Generating final report...")
    
    report = generate_final_report(analysis)
    
    # Save report
    report_path = PROJECT_ROOT / "data" / "results" / "forgetting_analysis_repro.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report

def verify_reproducibility(
    baseline_checksums: Dict[str, str],
    new_checksums: Dict[str, str],
    baseline_metrics: Dict[str, Any],
    new_metrics: Dict[str, Any]
) -> bool:
    """Verify that new run matches baseline."""
    logger.info("Verifying reproducibility...")
    
    # Check checksums
    for file_name, expected_hash in baseline_checksums.items():
        if file_name not in new_checksums:
            raise ReproducibilityError(f"Missing file in new run: {file_name}")
        
        new_hash = new_checksums[file_name]
        if new_hash != expected_hash:
            raise ReproducibilityError(
                f"Checksum mismatch for {file_name}:\n"
                f"  Baseline: {expected_hash}\n"
                f"  New:      {new_hash}"
            )
    
    # Check metrics (allowing for minor floating point differences)
    def compare_dicts(d1: Dict, d2: Dict, path: str = "") -> bool:
        if set(d1.keys()) != set(d2.keys()):
            raise ReproducibilityError(
                f"Key mismatch at {path}: {set(d1.keys())} vs {set(d2.keys())}"
            )
        
        for key in d1.keys():
            current_path = f"{path}.{key}" if path else key
            val1, val2 = d1[key], d2[key]
            
            if isinstance(val1, dict) and isinstance(val2, dict):
                if not compare_dicts(val1, val2, current_path):
                    return False
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Allow small floating point tolerance
                if abs(float(val1) - float(val2)) > 1e-10:
                    raise ReproducibilityError(
                        f"Value mismatch at {current_path}: {val1} vs {val2}"
                    )
            else:
                if val1 != val2:
                    raise ReproducibilityError(
                        f"Value mismatch at {current_path}: {val1} vs {val2}"
                    )
        
        return True
    
    if not compare_dicts(baseline_metrics, new_metrics):
        return False
    
    return True

def main():
    """Main reproducibility audit function."""
    logger.info("=" * 60)
    logger.info("Starting Reproducibility Audit")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        config = load_config()
        
        # Load batch config
        batch_config = load_batch_config()
        seeds = batch_config.get("seeds", [])
        
        if not seeds:
            raise ReproducibilityError("No seeds found in batch_config.json")
        
        logger.info(f"Loaded {len(seeds)} seeds from batch_config.json")
        
        # Load baseline data
        baseline_checksums = get_baseline_checksums()
        baseline_metrics = get_baseline_metrics()
        
        logger.info("Loaded baseline data")
        
        # Regenerate data
        data, new_checksums = regenerate_data(config, seeds)
        
        # Run training
        agent_states = run_training(data, config, seeds)
        
        # Evaluate agents
        metrics = evaluate_agents(agent_states, data["test_instances"], config)
        
        # Run statistical analysis
        analysis = run_statistical_analysis(metrics)
        
        # Generate final report
        new_metrics = generate_final_report(analysis)
        
        # Verify reproducibility
        is_reproducible = verify_reproducibility(
            baseline_checksums,
            new_checksums,
            baseline_metrics,
            new_metrics
        )
        
        if is_reproducible:
            logger.info("✓ Reproducibility check PASSED")
            logger.info("All checksums and metrics match baseline exactly.")
            return 0
        else:
            raise ReproducibilityError("Reproducibility check failed")
            
    except ReproducibilityError as e:
        logger.error(f"✗ Reproducibility check FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup temporary files
        for temp_file in [
            "data/generated_proofs_repro.json",
            "data/generated_grids_repro.json", 
            "data/test_instances_repro.json",
            "data/results/forgetting_analysis_repro.json"
        ]:
            temp_path = PROJECT_ROOT / temp_file
            if temp_path.exists():
                temp_path.unlink()
                logger.info(f"Cleaned up: {temp_file}")

if __name__ == "__main__":
    sys.exit(main())
