import os
import sys
import json
import logging
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/run_dynamic_simulation.log')
    ]
)
logger = logging.getLogger(__name__)

def check_module_exists(module_name: str, file_path: str) -> bool:
    """Check if a module file exists and is importable."""
    if not os.path.exists(file_path):
        logger.error(f"Module file not found: {file_path}")
        return False
    
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        logger.error(f"Could not load spec for module: {module_name}")
        return False
    
    return True

def load_fallback_flag(flag_path: str) -> Dict[str, Any]:
    """Load the fallback flag configuration."""
    try:
        with open(flag_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded fallback flag: {data}")
        return data
    except FileNotFoundError:
        logger.warning(f"Fallback flag file not found: {flag_path}. Assuming no fallback.")
        return {"fallback": False, "use_heuristic": False}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in fallback flag file: {e}")
        raise

def load_test_set(csv_path: str) -> List[Dict[str, Any]]:
    """Load the test set from CSV (simulated as list of dicts for engine)."""
    import pandas as pd
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Test set file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    # Convert to list of dicts as expected by engine
    records = df.to_dict('records')
    logger.info(f"Loaded {len(records)} test trajectories from {csv_path}")
    return records

def run_engine_simulation(test_data: List[Dict[str, Any]], output_path: str, mode: str) -> None:
    """
    Invoke the agenticsts-engine for dynamic simulation.
    
    Since we cannot import the engine directly (it's a CLI tool), we construct
    the command and execute it. However, for this task, we assume the engine
    logic is encapsulated in code/engine_runner.py or similar.
    
    We will simulate the call by importing the engine runner logic if available,
    or constructing the CLI command.
    
    Given the constraints, we will assume the engine is run via a subprocess
    call to the CLI, or we simulate the outcome based on the test data if the
    engine is not actually runnable in this environment.
    
    IMPORTANT: The task requires real execution. If the engine is not runnable,
    we must fail loudly.
    """
    import subprocess
    import sys

    # Prepare the command
    # Assuming the engine is invoked as: python -m agenticsts_engine --input <file> --policy dynamic --output <output_file>
    # However, the task says to use code/engine_runner.py. Let's assume engine_runner.py has a main that does this.
    
    # We need to pass the test data. Since engine_runner.py expects a file, we write test_data to a temp file.
    temp_input_path = "data/processed/temp_test_input.json"
    with open(temp_input_path, 'w') as f:
        json.dump(test_data, f)

    cmd = [
        sys.executable, "-m", "agenticsts_engine",
        "--input", temp_input_path,
        "--policy", "dynamic",
        "--output", output_path
    ]

    logger.info(f"Running engine simulation: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Engine simulation completed successfully.")
        logger.info(f"Engine stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"Engine stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Engine simulation failed with return code {e.returncode}")
        logger.error(f"Engine stdout: {e.stdout}")
        logger.error(f"Engine stderr: {e.stderr}")
        raise RuntimeError(f"Engine simulation failed: {e.stderr}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)

def main():
    """Main entry point for T017: Execute Dynamic Simulation."""
    logger.info("Starting T017: Execute Dynamic Simulation")

    # Paths
    base_path = Path(__file__).parent.parent
    processed_dir = base_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    test_set_path = processed_dir / "test_set.csv"
    fallback_flag_path = processed_dir / "fallback_flag.json"
    output_path = processed_dir / "simulation_logs_dynamic.json"

    # 1. Check dependencies
    if not test_set_path.exists():
        raise FileNotFoundError(f"Test set file not found: {test_set_path}. T014a must run first.")
    
    # 2. Load fallback flag
    fallback_config = load_fallback_flag(str(fallback_flag_path))
    use_heuristic = fallback_config.get("use_heuristic", False)
    mode = "heuristic" if use_heuristic else "dynamic"
    logger.info(f"Running in mode: {mode} (heuristic={use_heuristic})")

    # 3. Load test set
    test_data = load_test_set(str(test_set_path))
    if not test_data:
        raise ValueError("Test set is empty. Cannot run simulation.")

    # 4. Run simulation
    # Note: The task says to invoke via T018 (engine_runner.py).
    # We assume engine_runner.py can be called via CLI or imported.
    # Given the execution failure context, we try to run it as a module.
    try:
        run_engine_simulation(test_data, str(output_path), mode)
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise

    # 5. Verify output
    if not output_path.exists():
        raise FileNotFoundError(f"Output file not created: {output_path}")
    
    with open(output_path, 'r') as f:
        output_data = json.load(f)
    
    if not isinstance(output_data, list) and not isinstance(output_data, dict):
        raise ValueError(f"Invalid output format in {output_path}: expected list or dict")
    
    # Ensure mode is logged in output
    if isinstance(output_data, dict):
        output_data["mode"] = mode
    elif isinstance(output_data, list) and len(output_data) > 0:
        # If list of results, add mode to each or as metadata
        # Assuming the engine output structure includes metadata
        # If not, we might need to wrap it
        pass

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Dynamic simulation completed. Output written to {output_path}")
    return output_data

if __name__ == "__main__":
    main()