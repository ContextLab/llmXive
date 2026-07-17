"""
Main entry point for the llmXive automated science pipeline.
Orchestrates the full execution flow: Generation -> Simulation -> Analysis -> Reporting.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.src.utils.config import load_config, get_global_config
from code.src.utils.reproducibility import inject_seed_to_log
from code.src.generators.batch_runner import main as run_batch_generation
from code.src.generators.aggregate_batch import main as run_batch_aggregation
from code.src.simulation.run_simulation import main as run_simulation
from code.src.analysis.run_analysis import main as run_analysis
from code.src.analysis.power import main as run_power_analysis
from code.src.analysis.sensitivity import main as run_sensitivity
from code.src.analysis.plotting import main as run_plotting
from code.src.analysis.report import main as run_report
from code.src.analysis.verify_report import main as verify_report
from scripts.validate_batch import main as run_validation

def setup_logging(config_path: str):
    """Setup logging configuration."""
    config = load_config(config_path)
    log_level = config.get("log_level", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config.yaml")
    parser.add_argument("--output", type=str, default="data", help="Output directory base")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)

    setup_logging(str(config_path))
    logger = logging.getLogger(__name__)

    try:
        # 1. Inject Seeds (T004b) - Must happen before any generation
        logger.info("Step 1: Injecting seeds into run log for reproducibility...")
        inject_seed_to_log(str(config_path), f"{args.output}/run_log.json")

        # 2. Generate Networks
        logger.info("Step 2: Generating network batches...")
        import sys as sys_module
        sys_module.argv = ['batch_runner', '--config', str(config_path), '--output', args.output]
        run_batch_generation()

        # 3. Aggregate Batches
        logger.info("Step 3: Aggregating batches...")
        sys_module.argv = ['aggregate_batch', '--config', str(config_path), '--output', args.output]
        run_batch_aggregation()

        # 4. Run Simulations
        logger.info("Step 4: Running simulations...")
        sys_module.argv = ['run_simulation', '--config', str(config_path), '--output', args.output]
        run_simulation()

        # 5. Run Analysis
        logger.info("Step 5: Running analysis...")
        sys_module.argv = ['run_analysis', '--config', str(config_path), '--output', args.output]
        run_analysis()

        # 6. Power Analysis
        logger.info("Step 6: Running power analysis...")
        sys_module.argv = ['power', '--config', str(config_path), '--output', args.output]
        run_power_analysis()

        # 7. Sensitivity Sweep
        logger.info("Step 7: Running sensitivity sweep...")
        sys_module.argv = ['sensitivity', '--config', str(config_path), '--output', args.output]
        run_sensitivity()

        # 8. Plotting
        logger.info("Step 8: Generating figures...")
        sys_module.argv = ['plotting', '--config', str(config_path), '--output', args.output]
        run_plotting()

        # 9. Report Generation
        logger.info("Step 9: Generating report...")
        sys_module.argv = ['report', '--config', str(config_path), '--output', args.output]
        run_report()

        # 10. Verify Report
        logger.info("Step 10: Verifying report...")
        sys_module.argv = ['verify_report', '--config', str(config_path), '--output', args.output]
        verify_report()

        # 11. Validation
        logger.info("Step 11: Running validation...")
        sys_module.argv = ['validate_batch', '--config', str(config_path), '--output', args.output]
        run_validation()

        logger.info("Pipeline completed successfully.")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()