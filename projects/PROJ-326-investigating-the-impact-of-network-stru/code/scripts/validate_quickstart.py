"""
Task T048: Run quickstart.md validation.

This script validates that the project setup, generation, simulation, and analysis
pipelines work end-to-end as described in the project's quickstart documentation.
It verifies:
1. Project structure exists (Phase 1)
2. Dependencies can be imported (Phase 2)
3. Batch generation produces valid graphs (US1)
4. Simulation runs successfully on generated graphs (US2)
5. Analysis produces results and figures (US3)
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.utils.config import load_config
from code.src.generators.batch_runner import generate_batch
from code.src.generators.aggregate_batch import main as aggregate_main
from code.src.simulation.run_simulation import main as simulation_main
from code.src.analysis.run_analysis import main as analysis_main
from code.src.analysis.plotting import generate_all_figures
from code.src.analysis.verify_report import main as verify_report_main
from code.src.analysis.power import main as power_main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_project_structure() -> Tuple[bool, List[str]]:
    """Verify Phase 1: Project directories and files exist."""
    required_paths = [
        "code/src/generators",
        "code/src/simulation",
        "code/src/analysis",
        "code/src/utils",
        "code/tests",
        "data/raw",
        "data/analysis",
        "paper",
        "code/requirements.txt",
        "code/config.yaml",
        "code/README.md"
    ]
    
    missing = []
    for path_str in required_paths:
        full_path = project_root / path_str
        if not full_path.exists():
            missing.append(path_str)
    
    return len(missing) == 0, missing

def check_dependencies() -> Tuple[bool, List[str]]:
    """Verify Phase 2: Core dependencies can be imported."""
    required_modules = [
        "networkx", "numpy", "scipy", "matplotlib", "seaborn", 
        "pandas", "pytest", "yaml", "statsmodels", "sklearn"
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError as e:
            missing.append(f"{module}: {str(e)}")
    
    return len(missing) == 0, missing

def run_batch_generation() -> Tuple[bool, str]:
    """Verify US1: Generate a small batch of networks."""
    logger.info("Running batch generation test...")
    
    # Create a minimal config for testing
    config_path = project_root / "code" / "config.yaml"
    if not config_path.exists():
        return False, "config.yaml not found"
    
    try:
        config = load_config(config_path)
        # Override for quick test
        test_config = {
            "topology": "erdos_renyi",
            "n_nodes": 50,
            "edge_probability": 0.1,
            "batch_size": 5,
            "seed": 42,
            "output_dir": str(project_root / "data" / "raw" / "test_batch")
        }
        
        output_dir = Path(test_config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate batch
        generate_batch(
            topology=test_config["topology"],
            n_nodes=test_config["n_nodes"],
            edge_probability=test_config["edge_probability"],
            batch_size=test_config["batch_size"],
            seed=test_config["seed"],
            output_dir=str(output_dir)
        )
        
        # Verify output
        graph_files = list(output_dir.glob("graph_*.gpickle"))
        if len(graph_files) < test_config["batch_size"]:
            return False, f"Expected {test_config['batch_size']} graphs, found {len(graph_files)}"
        
        logger.info(f"Successfully generated {len(graph_files)} test graphs")
        return True, "Batch generation successful"
    except Exception as e:
        return False, f"Batch generation failed: {str(e)}"

def run_simulation_test() -> Tuple[bool, str]:
    """Verify US2: Run simulation on generated graphs."""
    logger.info("Running simulation test...")
    
    # Find test batch graphs
    test_batch_dir = project_root / "data" / "raw" / "test_batch"
    if not test_batch_dir.exists():
        return False, "Test batch directory not found. Run generation first."
    
    graph_files = list(test_batch_dir.glob("graph_*.gpickle"))
    if not graph_files:
        return False, "No graph files found in test batch"
    
    try:
        # Run simulation on first graph
        output_file = project_root / "data" / "analysis" / "test_simulation_results.json"
        
        # Prepare args for simulation
        args = argparse.Namespace(
            input_dir=str(test_batch_dir),
            output_file=str(output_file),
            seed=42,
            n_steps=10,
            temperature=1.0,
            topology_class="test"
        )
        
        simulation_main(args)
        
        # Verify output
        if not output_file.exists():
            return False, "Simulation results file not created"
        
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        if not isinstance(results, list) or len(results) == 0:
            return False, "Simulation results empty or invalid"
        
        logger.info(f"Simulation completed: {len(results)} results saved")
        return True, "Simulation successful"
    except Exception as e:
        return False, f"Simulation failed: {str(e)}"

def run_analysis_test() -> Tuple[bool, str]:
    """Verify US3: Run analysis pipeline."""
    logger.info("Running analysis test...")
    
    simulation_results = project_root / "data" / "analysis" / "test_simulation_results.json"
    if not simulation_results.exists():
        return False, "Simulation results not found. Run simulation first."
    
    try:
        # Run analysis
        args = argparse.Namespace(
            simulation_results=str(simulation_results),
            output_file=str(project_root / "data" / "analysis" / "test_final_results.json"),
            sensitivity_output=str(project_root / "data" / "analysis" / "test_sensitivity_sweep.json"),
            figures_dir=str(project_root / "figures"),
            report_output=str(project_root / "paper" / "test_report.txt")
        )
        
        analysis_main(args)
        
        # Verify outputs
        required_outputs = [
            "data/analysis/test_final_results.json",
            "data/analysis/test_sensitivity_sweep.json",
            "figures",
            "paper/test_report.txt"
        ]
        
        missing = []
        for path_str in required_outputs:
            full_path = project_root / path_str
            if not full_path.exists():
                missing.append(path_str)
        
        if missing:
            return False, f"Missing analysis outputs: {', '.join(missing)}"
        
        logger.info("Analysis pipeline completed successfully")
        return True, "Analysis successful"
    except Exception as e:
        return False, f"Analysis failed: {str(e)}"

def run_report_verification() -> Tuple[bool, str]:
    """Verify report contains required disclaimers."""
    logger.info("Verifying report content...")
    
    report_file = project_root / "paper" / "test_report.txt"
    if not report_file.exists():
        return False, "Report file not found"
    
    try:
        args = argparse.Namespace(
            report_file=str(report_file)
        )
        
        verify_report_main(args)
        return True, "Report verification passed"
    except Exception as e:
        return False, f"Report verification failed: {str(e)}"

def run_power_analysis() -> Tuple[bool, str]:
    """Verify power analysis module."""
    logger.info("Running power analysis test...")
    
    try:
        args = argparse.Namespace(
            output_file=str(project_root / "data" / "analysis" / "test_power_analysis_report.json")
        )
        
        power_main(args)
        
        output_file = project_root / "data" / "analysis" / "test_power_analysis_report.json"
        if not output_file.exists():
            return False, "Power analysis report not created"
        
        logger.info("Power analysis completed successfully")
        return True, "Power analysis successful"
    except Exception as e:
        return False, f"Power analysis failed: {str(e)}"

def main():
    """Run all validation checks."""
    logger.info("Starting Quickstart Validation (T048)...")
    
    tests = [
        ("Project Structure", check_project_structure),
        ("Dependencies", check_dependencies),
        ("Batch Generation", lambda: (True, run_batch_generation()[1]) if run_batch_generation()[0] else (False, run_batch_generation()[1])),
        ("Simulation", lambda: (True, run_simulation_test()[1]) if run_simulation_test()[0] else (False, run_simulation_test()[1])),
        ("Analysis", lambda: (True, run_analysis_test()[1]) if run_analysis_test()[0] else (False, run_analysis_test()[1])),
        ("Report Verification", lambda: (True, run_report_verification()[1]) if run_report_verification()[0] else (False, run_report_verification()[1])),
        ("Power Analysis", lambda: (True, run_power_analysis()[1]) if run_power_analysis()[0] else (False, run_power_analysis()[1]))
    ]
    
    results = []
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"Running: {test_name}")
        try:
            passed, message = test_func()
            results.append((test_name, passed, message))
            status = "PASS" if passed else "FAIL"
            logger.info(f"  {test_name}: {status} - {message}")
            if not passed:
                all_passed = False
        except Exception as e:
            results.append((test_name, False, f"Exception: {str(e)}"))
            logger.error(f"  {test_name}: FAIL - Exception: {str(e)}")
            all_passed = False
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*50)
    
    for test_name, passed, message in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
        if not passed:
            logger.info(f"       Reason: {message}")
    
    if all_passed:
        logger.info("\n✓ All quickstart validation checks passed!")
        return 0
    else:
        logger.info("\n✗ Some quickstart validation checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())