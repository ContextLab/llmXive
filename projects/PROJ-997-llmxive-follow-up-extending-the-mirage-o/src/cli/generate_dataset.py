"""
Wrapper task for generating the training dataset.
Orchestrates T015a (streaming), T015b (core logic), and T015c (monitoring).
"""
import logging
import time
import json
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import threading

from src.cli.generate_dataset_stream import load_dataset_streaming
from src.cli.generate_dataset_core import run_generation_pipeline, SampleResult
from src.cli.monitor_runtime import RuntimeMonitor
from src.config.logging_config import setup_logger, log_sample_progress
from src.config.env_config import load_config

logger = logging.getLogger(__name__)

@dataclass
class GenerationStats:
    """Statistics from the generation run."""
    total_samples: int
    success_count: int
    partial_count: int
    failed_count: int
    elapsed_time_seconds: float
    output_path: str
    levels_processed: Optional[Dict[str, int]] = None

class GenerationOrchestrator:
    """Orchestrates the dataset generation pipeline."""
    
    def __init__(
        self,
        output_path: str,
        max_runtime_hours: float = 5.5,
        min_sample_floor: int = 300,
        quantization_levels: list = None
    ):
        """
        Initialize the orchestrator.
        
        Args:
            output_path: Path to save the output dataset.
            max_runtime_hours: Maximum runtime in hours (reserving time for validation).
            min_sample_floor: Minimum number of samples required before early stop.
            quantization_levels: List of quantization levels to process.
        """
        self.output_path = output_path
        self.max_runtime_hours = max_runtime_hours
        self.min_sample_floor = min_sample_floor
        self.quantization_levels = quantization_levels or ["INT4", "INT8", "FP8"]
        self.monitor = RuntimeMonitor(max_runtime_hours=max_runtime_hours)
        self.should_stop = False
        self.sample_count = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True
    
    def run(self) -> GenerationStats:
        """
        Run the generation pipeline with monitoring.
        
        Returns:
            GenerationStats object with run statistics.
        """
        logger.info("Starting dataset generation with runtime monitoring")
        logger.info(f"Max runtime: {self.max_runtime_hours} hours")
        logger.info(f"Minimum sample floor: {self.min_sample_floor}")
        logger.info(f"Quantization levels: {self.quantization_levels}")
        
        start_time = time.time()
        
        # Check if runtime monitor should trigger early stop
        def check_runtime():
            while not self.should_stop:
                if self.monitor.should_stop(self.sample_count, self.min_sample_floor):
                    logger.info("Runtime limit approaching, initiating early stop...")
                    self.should_stop = True
                    break
                time.sleep(60)  # Check every minute
        
        # Start runtime monitoring thread
        monitor_thread = threading.Thread(target=check_runtime, daemon=True)
        monitor_thread.start()
        
        try:
            # Run the generation pipeline
            stats = run_generation_pipeline(
                output_path=self.output_path,
                max_samples=None,  # We control stopping via monitor
                quantization_levels=self.quantization_levels,
                sample_size=None  # We control stopping via monitor
            )
            
            # Update sample count from stats
            self.sample_count = stats.get("total_samples", 0)
            
        except Exception as e:
            logger.error(f"Generation pipeline failed: {e}")
            raise
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Calculate per-level statistics if available
        levels_processed = None
        if self.output_path:
            try:
                import pandas as pd
                df = pd.read_parquet(self.output_path)
                if "quantization_levels" in df.columns:
                    levels_processed = {}
                    for level in self.quantization_levels:
                        count = df["quantization_levels"].apply(lambda x: level in x if isinstance(x, list) else False).sum()
                        levels_processed[level] = int(count)
            except Exception as e:
                logger.warning(f"Could not calculate per-level statistics: {e}")
        
        final_stats = GenerationStats(
            total_samples=self.sample_count,
            success_count=stats.get("success_count", 0),
            partial_count=stats.get("partial_count", 0),
            failed_count=stats.get("failed_count", 0),
            elapsed_time_seconds=elapsed_time,
            output_path=self.output_path,
            levels_processed=levels_processed
        )
        
        logger.info(f"Generation completed successfully")
        logger.info(f"Final stats: {asdict(final_stats)}")
        
        return final_stats

def run_generation_pipeline(
    output_path: str,
    max_runtime_hours: float = 5.5,
    min_sample_floor: int = 300,
    quantization_levels: list = None
) -> GenerationStats:
    """
    Run the full generation pipeline with monitoring.
    
    Args:
        output_path: Path to save the output dataset.
        max_runtime_hours: Maximum runtime in hours.
        min_sample_floor: Minimum sample count before early stop.
        quantization_levels: List of quantization levels to process.
        
    Returns:
        GenerationStats object.
    """
    orchestrator = GenerationOrchestrator(
        output_path=output_path,
        max_runtime_hours=max_runtime_hours,
        min_sample_floor=min_sample_floor,
        quantization_levels=quantization_levels
    )
    return orchestrator.run()

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate training dataset with monitoring")
    parser.add_argument("--output", type=str, default="data/processed/training_sample.parquet",
                      help="Output path for the generated dataset")
    parser.add_argument("--max-runtime-hours", type=float, default=5.5,
                      help="Maximum runtime in hours")
    parser.add_argument("--min-sample-floor", type=int, default=300,
                      help="Minimum sample count before early stop")
    parser.add_argument("--levels", type=str, nargs="+", default=["INT4", "INT8", "FP8"],
                      help="Quantization levels to process")
    
    args = parser.parse_args()
    
    setup_logger()
    
    try:
        stats = run_generation_pipeline(
            output_path=args.output,
            max_runtime_hours=args.max_runtime_hours,
            min_sample_floor=args.min_sample_floor,
            quantization_levels=args.levels
        )
        
        print(f"Dataset generation complete.")
        print(f"Total samples: {stats.total_samples}")
        print(f"Success: {stats.success_count}, Partial: {stats.partial_count}, Failed: {stats.failed_count}")
        print(f"Elapsed time: {stats.elapsed_time_seconds:.2f} seconds")
        print(f"Output: {stats.output_path}")
        
        if stats.levels_processed:
            print("Per-level counts:")
            for level, count in stats.levels_processed.items():
                print(f"  {level}: {count}")
        
    except Exception as e:
        logger.error(f"Dataset generation failed: {e}")
        raise
