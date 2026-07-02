"""
Orchestration entry point for the Avian Song Variation prediction pipeline.

This script provides a command-line interface to run the full pipeline or
specific stages (ingestion, EDA, modeling) with configurable arguments.
"""
import argparse
import sys
import logging
from pathlib import Path

from config import Config
from utils import setup_logging
from data_setup import ensure_directory, initialize_checksums_file
# Importing stage scripts to allow them to be run via CLI
# Note: These imports assume the stage scripts (ingestion, eda, modeling) exist
# or will be created. We import the modules, not specific functions, to avoid
# circular dependencies or missing function errors if a stage isn't ready yet.
try:
    import importlib.util
    spec_ing = importlib.util.spec_from_file_location("ingestion", Path(__file__).parent / "ingestion.py")
    spec_ed = importlib.util.spec_from_file_location("eda", Path(__file__).parent / "eda.py")
    spec_mod = importlib.util.spec_from_file_location("modeling", Path(__file__).parent / "modeling.py")
    
    # We don't necessarily need to import them here if they are run as subprocesses,
    # but for a unified CLI, we might want to call their main() directly.
    # For now, we will structure the CLI to call them if they exist, or run them via subprocess.
    # However, the cleanest approach for a single-file entry point is to import and call main().
    # If the files don't exist yet, we handle the ImportError gracefully.
    has_ingestion = spec_ing is not None and spec_ing.loader is not None
    has_eda = spec_ed is not None and spec_ed.loader is not None
    has_modeling = spec_mod is not None and spec_mod.loader is not None
except Exception:
    has_ingestion = False
    has_eda = False
    has_modeling = False

logger = logging.getLogger(__name__)

def run_stage(stage_name: str, args: argparse.Namespace) -> int:
    """
    Dynamically run a specific stage module based on the stage name.
    Returns 0 on success, 1 on failure.
    """
    stage_map = {
        "ingestion": "ingestion",
        "eda": "eda",
        "modeling": "modeling",
        "full": "full"
    }
    
    if stage_name not in stage_map:
        logger.error(f"Unknown stage: {stage_name}")
        return 1

    stage_module_name = stage_map[stage_name]
    stage_path = Path(__file__).parent / f"{stage_module_name}.py"

    if not stage_path.exists():
        logger.error(f"Stage script not found: {stage_path}")
        logger.warning("Ensure the stage scripts (ingestion.py, eda.py, modeling.py) are implemented.")
        return 1

    try:
        # Load and execute the module
        spec = importlib.util.spec_from_file_location(stage_module_name, stage_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {stage_path}")
        
        module = importlib.util.module_from_spec(spec)
        
        # Pass arguments to the module if it expects a main() with args
        # We check if the module has a main function
        spec.loader.exec_module(module)
        
        if hasattr(module, 'main'):
            # If the module has a main function, call it with the parsed args
            # We need to construct a namespace specific to that stage if possible,
            # but for now we pass the global args and let the stage handle what it needs.
            # Alternatively, we can just call main() without args if the stage parses its own.
            # Given the task is "orchestration entry point", the main.py should handle parsing.
            # But to keep it modular, let's assume the stage scripts can also parse their own args
            # OR we pass the relevant subset.
            # For simplicity and robustness in a pipeline, we'll pass the full args namespace.
            module.main(args)
        else:
            # Fallback: run the module's top-level code if no main()
            # This is less ideal for testing but works for simple scripts.
            logger.warning(f"Module {stage_module_name} has no 'main' function. Running top-level code.")
            # This might re-execute if the module has `if __name__ == "__main__":`
            # We rely on the module's internal logic to handle this.
            pass
        
        return 0
    except Exception as e:
        logger.error(f"Error running stage {stage_name}: {e}", exc_info=True)
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="Orchestration entry point for Avian Song Variation Analysis Pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          python code/main.py --stage ingestion --output data/processed/analysis_dataset.csv
          python code/main.py --stage eda --report data/eda_report.json
          python code/main.py --stage modeling --model-dir data/models
          python code/main.py --stage full --output data/processed/analysis_dataset.csv
        """
    )
    
    parser.add_argument(
        "--stage",
        type=str,
        choices=["ingestion", "eda", "modeling", "full"],
        default="full",
        help="Pipeline stage to execute. Default: full"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file. Default: config.yaml"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (debug) logging"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override default output path for the stage result."
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Root directory for data files. Default: data"
    )
    
    parser.add_argument(
        "--code-dir",
        type=str,
        default="code",
        help="Root directory for code files. Default: code"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_file = Path(args.data_dir) / "pipeline.log"
    ensure_directory(log_file.parent)
    
    logger = setup_logging(
        name="avian_pipeline",
        log_file=str(log_file),
        level=log_level,
        console=True
    )
    
    logger.info("Starting Avian Song Variation Pipeline")
    logger.info(f"Stage: {args.stage}")
    logger.info(f"Config: {args.config}")
    logger.info(f"Data Dir: {args.data_dir}")

    # Initialize directories and checksums if not already done
    # This ensures the environment is ready
    try:
        ensure_directory(Path(args.data_dir) / "raw")
        ensure_directory(Path(args.data_dir) / "processed")
        ensure_directory(Path(args.data_dir) / "models")
        initialize_checksums_file(Path(args.data_dir) / "checksums.txt")
    except Exception as e:
        logger.error(f"Failed to initialize directories: {e}")
        sys.exit(1)

    # Execute the stage
    exit_code = run_stage(args.stage, args)

    if exit_code == 0:
        logger.info("Pipeline stage completed successfully.")
    else:
        logger.error("Pipeline stage failed.")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()