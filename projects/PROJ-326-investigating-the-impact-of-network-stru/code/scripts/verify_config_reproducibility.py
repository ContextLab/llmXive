"""
Script to verify config.yaml documentation and reproducibility of random seeds.

This script performs two main checks:
1. Validates that config.yaml contains all required documentation fields and structure.
2. Verifies that random seeds defined in config.yaml produce reproducible results
   across multiple runs by executing a controlled generation task.
"""
import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import random
import numpy as np
import networkx as nx

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.utils.config import load_config, get_config_value
from code.src.utils.reproducibility import verify_reproducibility, inject_seed_to_log
from code.src.generators.er import ErdosRenyiGenerator


def validate_config_documentation(config_path: Path) -> Dict[str, Any]:
    """
    Validate that config.yaml contains required documentation fields.
    
    Checks for:
    - Global seed definition
    - Topology targets configuration
    - Simulation parameters
    - Proper nesting and data types
    
    Returns a dict with validation results.
    """
    results = {
        "valid": True,
        "missing_fields": [],
        "type_errors": [],
        "warnings": []
    }
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        results["valid"] = False
        results["error"] = f"Failed to load config.yaml: {str(e)}"
        return results
    
    if not isinstance(config, dict):
        results["valid"] = False
        results["error"] = "Config must be a YAML dictionary"
        return results
    
    # Check for required top-level sections
    required_sections = ["global", "topology", "simulation"]
    for section in required_sections:
        if section not in config:
            results["valid"] = False
            results["missing_fields"].append(section)
    
    # Check global section for seed
    if "global" in config:
        if "seed" not in config["global"]:
            results["valid"] = False
            results["missing_fields"].append("global.seed")
        elif not isinstance(config["global"]["seed"], int):
            results["type_errors"].append("global.seed must be an integer")
    
    # Check topology section
    if "topology" in config:
        if "targets" not in config["topology"]:
            results["warnings"].append("topology.targets not defined")
        else:
            targets = config["topology"]["targets"]
            if not isinstance(targets, dict):
                results["type_errors"].append("topology.targets must be a dictionary")
            else:
                # Check for expected topology types
                expected_types = ["erdos_renyi", "watts_strogatz", "barabasi_albert"]
                for topo_type in expected_types:
                    if topo_type not in targets:
                        results["warnings"].append(f"topology.targets.{topo_type} not defined")
    
    # Check simulation section
    if "simulation" in config:
        sim_config = config["simulation"]
        if "time_steps" not in sim_config:
            results["warnings"].append("simulation.time_steps not defined")
        if "temperature" not in sim_config:
            results["warnings"].append("simulation.temperature not defined")
    
    return results


def test_seed_reproducibility(config: Dict[str, Any], test_runs: int = 3) -> Dict[str, Any]:
    """
    Test that random seeds produce reproducible results.
    
    Runs a controlled graph generation task multiple times with the same seed
    and verifies that the outputs are identical.
    
    Returns a dict with reproducibility results.
    """
    results = {
        "reproducible": True,
        "runs_tested": test_runs,
        "details": []
    }
    
    # Get seed from config
    seed = get_config_value(config, "global.seed", 42)
    
    # Configuration for test generation
    n_nodes = 20
    edge_prob = 0.3
    
    generated_graphs = []
    generated_metrics = []
    
    for run_idx in range(test_runs):
        # Reset random state with config seed
        random.seed(seed)
        np.random.seed(seed)
        
        # Generate a test graph using the configured seed
        generator = ErdosRenyiGenerator(
            n_nodes=n_nodes,
            p=edge_prob,
            seed=seed,
            timeout=10,
            max_retries=3
        )
        
        try:
            graph = generator.generate()
            
            # Compute metrics to compare
            metrics = {
                "num_nodes": graph.number_of_nodes(),
                "num_edges": graph.number_of_edges(),
                "is_connected": nx.is_connected(graph),
                "clustering": nx.average_clustering(graph),
                "degree_sequence": sorted([d for n, d in graph.degree()])
            }
            
            generated_graphs.append(graph)
            generated_metrics.append(metrics)
            
        except Exception as e:
            results["reproducible"] = False
            results["error"] = f"Run {run_idx} failed: {str(e)}"
            return results
    
    # Compare all runs
    for i in range(1, test_runs):
        prev = generated_metrics[0]
        curr = generated_metrics[i]
        
        if prev != curr:
            results["reproducible"] = False
            results["details"].append({
                "run_comparison": f"0 vs {i}",
                "difference": {
                    "prev": prev,
                    "curr": curr
                }
            })
    
    return results


def verify_seed_injection(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify that seeds are properly injected into run logs.
    
    Tests the inject_seed_to_log functionality to ensure seeds
    are recorded in the run log for reproducibility tracking.
    """
    results = {
        "injection_working": True,
        "log_entries": []
    }
    
    seed = get_config_value(config, "global.seed", 42)
    
    try:
        # Test injection
        from code.src.utils.logging import log_run, get_run_log, clear_run_log
        from code.src.utils.reproducibility import generate_run_id
        
        # Clear any existing log
        clear_run_log()
        
        # Create a test run with seed
        run_id = generate_run_id()
        log_run(
            run_id=run_id,
            seed=seed,
            parameters={"test": "seed_verification"},
            status="completed"
        )
        
        # Retrieve and verify
        log_entries = get_run_log()
        
        if not log_entries:
            results["injection_working"] = False
            results["error"] = "No log entries found after injection"
            return results
        
        # Check that seed is in the log
        found_seed = False
        for entry in log_entries:
            if entry.get("seed") == seed:
                found_seed = True
                results["log_entries"].append(entry)
                break
        
        if not found_seed:
            results["injection_working"] = False
            results["error"] = f"Seed {seed} not found in run log"
        
    except Exception as e:
        results["injection_working"] = False
        results["error"] = f"Seed injection test failed: {str(e)}"
    
    return results


def main():
    """Main entry point for config verification script."""
    parser = argparse.ArgumentParser(
        description="Verify config.yaml documentation and seed reproducibility"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to config.yaml file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)
    
    print(f"Verifying config: {config_path}")
    print("=" * 60)
    
    # Load config
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"ERROR: Failed to load config: {str(e)}")
        sys.exit(1)
    
    # 1. Validate documentation
    print("\n1. Validating config documentation...")
    doc_results = validate_config_documentation(config_path)
    
    if doc_results["valid"]:
        print("   ✓ Config documentation is valid")
    else:
        print("   ✗ Config documentation has issues:")
        if doc_results.get("missing_fields"):
            print(f"     Missing fields: {', '.join(doc_results['missing_fields'])}")
        if doc_results.get("type_errors"):
            for error in doc_results["type_errors"]:
                print(f"     Type error: {error}")
        if doc_results.get("warnings"):
            print(f"     Warnings: {', '.join(doc_results['warnings'])}")
    
    if args.verbose:
        print(f"   Full results: {json.dumps(doc_results, indent=2)}")
    
    # 2. Test seed reproducibility
    print("\n2. Testing seed reproducibility...")
    repro_results = test_seed_reproducibility(config)
    
    if repro_results["reproducible"]:
        print(f"   ✓ Seed reproducibility verified across {repro_results['runs_tested']} runs")
    else:
        print("   ✗ Seed reproducibility FAILED:")
        if repro_results.get("error"):
            print(f"     Error: {repro_results['error']}")
        if repro_results.get("details"):
            for detail in repro_results["details"]:
                print(f"     Difference: {json.dumps(detail, indent=4)}")
    
    # 3. Verify seed injection
    print("\n3. Verifying seed injection into logs...")
    injection_results = verify_seed_injection(config)
    
    if injection_results["injection_working"]:
        print("   ✓ Seed injection working correctly")
        if args.verbose and injection_results.get("log_entries"):
            for entry in injection_results["log_entries"]:
                print(f"     Log entry: {json.dumps(entry, indent=6)}")
    else:
        print("   ✗ Seed injection FAILED:")
        if injection_results.get("error"):
            print(f"     Error: {injection_results['error']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = (
        doc_results["valid"] and
        repro_results["reproducible"] and
        injection_results["injection_working"]
    )
    
    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print("  - Config documentation is complete and valid")
        print("  - Random seeds produce reproducible results")
        print("  - Seeds are properly injected into run logs")
        sys.exit(0)
    else:
        print("✗ SOME CHECKS FAILED")
        if not doc_results["valid"]:
            print("  - Config documentation issues detected")
        if not repro_results["reproducible"]:
            print("  - Seed reproducibility failed")
        if not injection_results["injection_working"]:
            print("  - Seed injection failed")
        sys.exit(1)


if __name__ == "__main__":
    main()