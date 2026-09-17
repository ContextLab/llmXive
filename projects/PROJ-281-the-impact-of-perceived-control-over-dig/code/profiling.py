import argparse
import json
import logging
import resource
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

from code.config import Config, get_config_value, set_seed, CONFIG
from code.services.data_ingestion import run_data_ingestion_pipeline, download_and_validate_dataset
from code.services.anxiety_scoring import run_full_scoring_pipeline
from code.services.proxy_extractor import run_proxy_extraction_pipeline
from code.services.merge_and_save import run_merge_and_save_pipeline
from code.analysis.statistical_test import run_statistical_analysis_pipeline
from code.viz.plot_results import run_visualization_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class RuntimeLimitExceededError(Exception):
    """Raised when the pipeline exceeds the configured runtime limit."""
    pass

class CoverageError(Exception):
    """Raised when coverage validation fails."""
    pass

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0  # Convert KB to GB on Linux/macOS

def get_peak_memory_gb() -> float:
    """Get peak memory usage in GB."""
    return get_memory_usage_gb()

def check_plan_spec_discrepancy() -> bool:
    """Check for known plan/spec discrepancies (placeholder for T045 logic)."""
    # This is a placeholder; actual logic would compare plan.md and spec.md
    return False

def save_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """Save the runtime report to a markdown file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Runtime Performance Report\n\n")
        f.write(f"**Dataset ID**: {report_data.get('dataset_id', 'N/A')}\n")
        f.write(f"**Total Runtime (seconds)**: {report_data.get('total_runtime_seconds', 0):.2f}\n")
        f.write(f"**Total Runtime (hours)**: {report_data.get('total_runtime_seconds', 0) / 3600:.4f}\n")
        f.write(f"**Rows Processed**: {report_data.get('rows_processed', 0)}\n")
        f.write(f"**Milliseconds per Row**: {report_data.get('ms_per_row', 0):.4f}\n")
        f.write(f"**Peak Memory (GB)**: {report_data.get('peak_memory_gb', 0):.4f}\n")
        f.write(f"**Runtime Limit (hours)**: {report_data.get('runtime_limit_hours', 6)}\n")
        f.write(f"**Status**: {report_data.get('status', 'Unknown')}\n\n")
        
        if 'sample_reduction' in report_data:
            f.write("## Sample Reduction Applied\n")
            f.write(f"**Reason**: {report_data['sample_reduction'].get('reason', 'N/A')}\n")
            f.write(f"**Original Count**: {report_data['sample_reduction'].get('original_count', 0)}\n")
            f.write(f"**Reduced Count**: {report_data['sample_reduction'].get('reduced_count', 0)}\n")
            f.write(f"**Reduction Factor**: {report_data['sample_reduction'].get('reduction_factor', 0):.2f}\n\n")
        
        f.write("## Stage Timings\n")
        f.write("| Stage | Time (s) | % of Total |\n")
        f.write("|-------|----------|------------|\n")
        for stage, timing in report_data.get('stage_timings', {}).items():
            pct = (timing / report_data.get('total_runtime_seconds', 1)) * 100 if report_data.get('total_runtime_seconds', 0) > 0 else 0
            f.write(f"| {stage} | {timing:.2f} | {pct:.1f}% |\n")
        
        f.write("\n## Notes\n")
        f.write(f"- Runtime limit enforced: {report_data.get('runtime_limit_hours', 6)} hours\n")
        f.write(f"- Contingency triggered: {report_data.get('contingency_triggered', False)}\n")
        if report_data.get('contingency_triggered'):
            f.write("- Action taken: Sample size reduction\n")

def run_profiling_pipeline(sample_size: Optional[int] = None, enforce_limit: bool = True) -> Dict[str, Any]:
    """
    Run the full pipeline with performance profiling.
    
    Args:
        sample_size: If provided, limit the dataset to this many rows for testing.
        enforce_limit: If True, raise RuntimeLimitExceededError if limit is exceeded.
    
    Returns:
        Dictionary containing profiling results.
    """
    start_time = time.time()
    report = {
        'dataset_id': 'cardiffnlp/tweet_sentiment_extraction',
        'runtime_limit_hours': CONFIG.RUNTIME_LIMIT_HOURS,
        'stage_timings': {},
        'contingency_triggered': False,
        'sample_reduction': None,
        'status': 'unknown'
    }
    
    try:
        # Stage 1: Data Ingestion
        logger.info("Starting Stage 1: Data Ingestion")
        t1_start = time.time()
        
        # If sample_size is specified, we need to handle it here
        # The data ingestion pipeline currently loads the full dataset
        # We'll handle sampling after ingestion
        if sample_size:
            logger.info(f"Sampling dataset to {sample_size} rows after ingestion")
        
        run_data_ingestion_pipeline()
        t1_end = time.time()
        report['stage_timings']['data_ingestion'] = t1_end - t1_start
        logger.info(f"Stage 1 completed in {t1_end - t1_start:.2f}s")
        
        # Apply sampling if requested
        if sample_size:
            raw_data_path = Path(CONFIG.RAW_DATA_DIR) / 'social_media.csv'
            if raw_data_path.exists():
                df = pd.read_csv(raw_data_path)
                original_count = len(df)
                if original_count > sample_size:
                    logger.info(f"Reducing dataset from {original_count} to {sample_size} rows")
                    df_sampled = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
                    df_sampled.to_csv(raw_data_path, index=False)
                    report['sample_reduction'] = {
                        'reason': 'Performance testing',
                        'original_count': original_count,
                        'reduced_count': sample_size,
                        'reduction_factor': original_count / sample_size
                    }
                    report['contingency_triggered'] = True
                else:
                    logger.info(f"Dataset already has {original_count} rows, no sampling needed")
        
        # Stage 2: Preprocessing & Scoring
        logger.info("Starting Stage 2: Preprocessing & Anxiety Scoring")
        t2_start = time.time()
        run_full_scoring_pipeline()
        t2_end = time.time()
        report['stage_timings']['preprocessing_scoring'] = t2_end - t2_start
        logger.info(f"Stage 2 completed in {t2_end - t2_start:.2f}s")
        
        # Stage 3: Proxy Extraction
        logger.info("Starting Stage 3: Proxy Extraction")
        t3_start = time.time()
        run_proxy_extraction_pipeline()
        t3_end = time.time()
        report['stage_timings']['proxy_extraction'] = t3_end - t3_start
        logger.info(f"Stage 3 completed in {t3_end - t3_start:.2f}s")
        
        # Stage 4: Merge & Validation
        logger.info("Starting Stage 4: Merge & Validation")
        t4_start = time.time()
        run_merge_and_save_pipeline()
        t4_end = time.time()
        report['stage_timings']['merge_validation'] = t4_end - t4_start
        logger.info(f"Stage 4 completed in {t4_end - t4_start:.2f}s")
        
        # Stage 5: Statistical Analysis
        logger.info("Starting Stage 5: Statistical Analysis")
        t5_start = time.time()
        run_statistical_analysis_pipeline()
        t5_end = time.time()
        report['stage_timings']['statistical_analysis'] = t5_end - t5_start
        logger.info(f"Stage 5 completed in {t5_end - t5_start:.2f}s")
        
        # Stage 6: Visualization
        logger.info("Starting Stage 6: Visualization")
        t6_start = time.time()
        run_visualization_pipeline()
        t6_end = time.time()
        report['stage_timings']['visualization'] = t6_end - t6_start
        logger.info(f"Stage 6 completed in {t6_end - t6_start:.2f}s")
        
        # Calculate total runtime
        end_time = time.time()
        total_runtime = end_time - start_time
        report['total_runtime_seconds'] = total_runtime
        report['peak_memory_gb'] = get_peak_memory_gb()
        
        # Check runtime limit
        runtime_hours = total_runtime / 3600
        if enforce_limit and runtime_hours > CONFIG.RUNTIME_LIMIT_HOURS:
            raise RuntimeLimitExceededError(
                f"Pipeline exceeded runtime limit of {CONFIG.RUNTIME_LIMIT_HOURS} hours "
                f"(actual: {runtime_hours:.2f} hours)"
            )
        
        # Calculate metrics
        # Count rows from final analysis file
        final_analysis_path = Path(CONFIG.PROCESSED_DATA_DIR) / 'final_analysis.csv'
        if final_analysis_path.exists():
            final_df = pd.read_csv(final_analysis_path)
            report['rows_processed'] = len(final_df)
            if len(final_df) > 0:
                report['ms_per_row'] = (total_runtime * 1000) / len(final_df)
            else:
                report['ms_per_row'] = 0
        else:
            report['rows_processed'] = 0
            report['ms_per_row'] = 0
        
        report['status'] = 'success'
        logger.info(f"Pipeline completed successfully in {total_runtime:.2f}s")
        
    except RuntimeLimitExceededError as e:
        report['status'] = 'runtime_limit_exceeded'
        report['error'] = str(e)
        logger.error(f"Runtime limit exceeded: {e}")
        raise
    except Exception as e:
        report['status'] = 'failed'
        report['error'] = str(e)
        logger.error(f"Pipeline failed: {e}")
        raise
    
    return report

def main():
    """Main entry point for the profiling script."""
    parser = argparse.ArgumentParser(description='Run performance profiling for the pipeline')
    parser.add_argument('--sample-size', type=int, default=None,
                      help='Limit dataset to this many rows for performance testing')
    parser.add_argument('--no-enforce-limit', action='store_true',
                      help='Do not enforce the runtime limit')
    args = parser.parse_args()
    
    try:
        report = run_profiling_pipeline(
            sample_size=args.sample_size,
            enforce_limit=not args.no_enforce_limit
        )
        
        # Save report
        state_dir = Path('state')
        state_dir.mkdir(exist_ok=True)
        report_path = state_dir / 'runtime_report.md'
        save_report(report, report_path)
        
        logger.info(f"Performance report saved to {report_path}")
        print(json.dumps(report, indent=2, default=str))
        
    except RuntimeLimitExceededError:
        logger.error("Pipeline halted due to runtime limit")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()