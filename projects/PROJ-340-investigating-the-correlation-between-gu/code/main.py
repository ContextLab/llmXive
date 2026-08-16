import sys
import os
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('main')

def setup_paths(project_root=None):
    """Setup standard paths."""
    if project_root is None:
        project_root = Path(__file__).parent.parent
    return {
        'raw': project_root / 'data' / 'raw',
        'processed': project_root / 'data' / 'processed',
        'results': project_root / 'data' / 'results',
        'metadata': project_root / 'data' / 'metadata',
        'config': project_root / 'data' / 'config',
        'state': project_root / 'state' / 'projects'
    }

def estimate_ram_usage(df):
    """Estimate RAM usage of dataframe."""
    return df.memory_usage(deep=True).sum()

def determine_compute_strategy(df):
    """Determine compute strategy based on data size."""
    ram_bytes = estimate_ram_usage(df)
    ram_gb = ram_bytes / (1024 ** 3)

    if ram_gb < 4:
        return {'strategy': 'local', 'ram_gb': ram_gb, 'parallel': False}
    elif ram_gb < 16:
        return {'strategy': 'local', 'ram_gb': ram_gb, 'parallel': True}
    else:
        return {'strategy': 'distributed', 'ram_gb': ram_gb, 'parallel': True}

def save_compute_strategy(strategy, output_path='data/metadata/compute_strategy.json'):
    """Save compute strategy to disk."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(strategy, f, indent=2)

def check_validation_mode():
    """Check if validation mode (synthetic) is active."""
    flag_path = 'data/metadata/validation_mode_flag.json'
    if os.path.exists(flag_path):
        with open(flag_path, 'r') as f:
            config = json.load(f)
        return config.get('active', False)
    return False

def run_ingestion_and_validation(input_path, output_dir):
    """Run ingestion and validation steps."""
    from ingest import main as ingest_main
    import sys

    # Prepare args for ingest
    sys.argv = ['ingest', '--input', input_path, '--output', output_dir, '--mode', 'synthetic' if check_validation_mode() else 'real']
    ingest_main()

def run_analysis(input_path, output_dir):
    """Run analysis steps."""
    from analysis import main as analysis_main
    import sys

    sys.argv = ['analysis', '--input', input_path, '--output', output_dir]
    analysis_main()

def run_diagnostics(input_path, output_dir):
    """Run diagnostics steps."""
    from diagnostics import main as diagnostics_main
    import sys

    sys.argv = ['diagnostics', '--input', input_path, '--output', output_dir]
    diagnostics_main()

def main():
    """Main pipeline orchestration."""
    parser = argparse.ArgumentParser(description='Run the full analysis pipeline')
    parser.add_argument('--input', type=str, required=True, help='Input data file')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    parser.add_argument('--mode', type=str, default='auto', help='Pipeline mode')
    args = parser.parse_args()

    start_time = time.time()
    paths = setup_paths()

    # Ensure directories exist
    os.makedirs(paths['results'], exist_ok=True)
    os.makedirs(paths['metadata'], exist_ok=True)

    logger.info(f"Starting pipeline at {datetime.now().isoformat()}")
    logger.info(f"Input: {args.input}, Output: {args.output}")

    # Run ingestion
    logger.info("Running ingestion and validation...")
    run_ingestion_and_validation(args.input, str(paths['processed']))

    # Run analysis
    logger.info("Running analysis...")
    run_analysis(args.input, str(paths['results']))

    # Run diagnostics
    logger.info("Running diagnostics...")
    run_diagnostics(args.input, str(paths['results']))

    end_time = time.time()
    duration_hours = (end_time - start_time) / 3600

    # Check timing constraint
    timing_evidence = {
        'start_time': datetime.fromtimestamp(start_time).isoformat(),
        'end_time': datetime.fromtimestamp(end_time).isoformat(),
        'duration_hours': duration_hours,
        'status': 'PASS' if duration_hours < 6.0 else 'FAIL',
        'limit_hours': 6.0
    }

    timing_path = os.path.join(paths['results'], 'timing_evidence.json')
    with open(timing_path, 'w') as f:
        json.dump(timing_evidence, f, indent=2)

    logger.info(f"Pipeline completed in {duration_hours:.2f} hours")
    if duration_hours >= 6.0:
        logger.error("Pipeline exceeded 6-hour time limit")
        sys.exit(1)

    logger.info("Pipeline execution successful")

if __name__ == '__main__':
    main()
