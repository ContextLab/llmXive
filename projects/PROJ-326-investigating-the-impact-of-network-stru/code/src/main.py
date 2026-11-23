import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.utils.config import load_config, set_seed
from code.src.utils.logging import init_logging, log_metric
from code.src.generators.stratified_runner import run_stratified_generation
from code.src.simulation.run_simulation import main as run_simulation_main
from code.src.analysis.run_analysis import main as run_analysis_main
from code.src.analysis.report import main as generate_report_main

def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")
    parser.add_argument("--phase", type=str, required=True, 
                        choices=["generate", "simulate", "analyze", "report", "full"],
                        help="Pipeline phase to execute")
    parser.add_argument("--config", type=str, default="code/config.yaml",
                        help="Path to configuration file")
    parser.add_argument("--log-level", type=str, default="INFO",
                        help="Logging level")
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Initialize logging infrastructure
    init_logging()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {args.config}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Set global seed
    seed = config.get("global_seed", 42)
    set_seed(seed)
    
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        if args.phase == "generate":
            logger.info("Starting Generation Phase")
            log_metric({
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_start",
                "run_id": run_id,
                "seed": seed,
                "status": "starting",
                "duration_seconds": 0.0
            })
            run_stratified_generation(config)
            log_metric({
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_end",
                "run_id": run_id,
                "seed": seed,
                "status": "completed",
                "duration_seconds": 0.0 # Calculated dynamically in real impl
            })
            logger.info("Generation Phase Completed")
        
        elif args.phase == "simulate":
            logger.info("Starting Simulation Phase")
            log_metric({
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_start",
                "run_id": run_id,
                "seed": seed,
                "status": "starting",
                "duration_seconds": 0.0
            })
            run_simulation_main(config)
            log_metric({
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_end",
                "run_id": run_id,
                "seed": seed,
                "status": "completed",
                "duration_seconds": 0.0
            })
            logger.info("Simulation Phase Completed")
        
        elif args.phase == "analyze":
            logger.info("Starting Analysis Phase")
            run_analysis_main(config)
            logger.info("Analysis Phase Completed")
        
        elif args.phase == "report":
            logger.info("Starting Report Generation Phase")
            generate_report_main(config)
            logger.info("Report Generation Phase Completed")
        
        elif args.phase == "full":
            logger.info("Starting Full Pipeline Execution")
            
            # Phase 1: Generate
            log_metric({
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_start",
                "run_id": run_id,
                "seed": seed,
                "status": "starting",
                "duration_seconds": 0.0
            })
            run_stratified_generation(config)
            log_metric({
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_end",
                "run_id": run_id,
                "seed": seed,
                "status": "completed",
                "duration_seconds": 0.0
            })
            
            # Phase 2: Simulate
            log_metric({
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_start",
                "run_id": run_id,
                "seed": seed,
                "status": "starting",
                "duration_seconds": 0.0
            })
            run_simulation_main(config)
            log_metric({
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_end",
                "run_id": run_id,
                "seed": seed,
                "status": "completed",
                "duration_seconds": 0.0
            })
            
            # Phase 3: Analyze
            run_analysis_main(config)
            
            # Phase 4: Report
            generate_report_main(config)
            
            logger.info("Full Pipeline Execution Completed")
    
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        log_metric({
            "timestamp": datetime.now().isoformat(),
            "event_type": "simulation_end",
            "run_id": run_id,
            "seed": seed,
            "status": "failed",
            "duration_seconds": 0.0
        })
        sys.exit(1)

if __name__ == "__main__":
    main()