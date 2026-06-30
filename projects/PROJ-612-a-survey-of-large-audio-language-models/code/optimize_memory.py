import os
import sys
import gc
import time
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import existing utilities from the project
from config import load_config, get_audio_config
from setup_logging import get_logger, init_logging
from runtime_guard import check_aborted, get_abort_reason

# Initialize logger
logger = get_logger("optimize_memory")

# Configuration constants for optimization
DEFAULT_BATCH_SIZE = 1
DEFAULT_MAX_AUDIO_LENGTH_SEC = 10
DEFAULT_SAMPLE_RATE = 16000
MEMORY_THRESHOLD_GB = 6.0  # Conservative limit for 7GB RAM machine
MAX_DURATION_HOURS = 4.5  # Threshold to trigger optimization
TARGET_DURATION_HOURS = 5.0  # Target maximum duration

class MemoryOptimizer:
    """
    Implements batch size reduction and memory-efficient loading strategies
    to ensure the pipeline completes within the 5-hour target duration.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path) if config_path else load_config()
        self.audio_config = get_audio_config(self.config)
        self.batch_size = self.audio_config.get("batch_size", DEFAULT_BATCH_SIZE)
        self.max_length = self.audio_config.get("max_length_sec", DEFAULT_MAX_AUDIO_LENGTH_SEC)
        self.sample_rate = self.audio_config.get("sample_rate", DEFAULT_SAMPLE_RATE)
        
        # Optimization flags
        self.use_torch_cpu_only = True
        self.enable_gc_during_batch = True
        self.memory_limit_gb = MEMORY_THRESHOLD_GB

    def get_memory_usage_gb(self) -> float:
        """
        Estimate current memory usage in GB.
        Uses resource module on Unix or fallback on Windows.
        """
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On Linux, ru_maxrss is in KB; on macOS it's in KB.
            # On Windows, we need to use psutil or similar, but resource isn't available.
            # Fallback to a safe estimate if resource fails or on Windows.
            if sys.platform != "win32":
                return usage / (1024 * 1024)  # Convert KB to GB
            else:
                # Windows fallback: assume low usage if we can't measure
                return 0.0
        except Exception as e:
            logger.warning(f"Could not measure memory usage: {e}")
            return 0.0

    def adjust_batch_size(self, current_duration_hours: float) -> Tuple[int, bool]:
        """
        Adjust batch size based on observed duration.
        If duration > MAX_DURATION_HOURS, reduce batch size to 1 and enable aggressive GC.
        Returns (new_batch_size, was_optimized).
        """
        if current_duration_hours <= MAX_DURATION_HOURS:
            logger.info(f"Duration {current_duration_hours:.2f}h <= {MAX_DURATION_HOURS}h. No optimization needed.")
            return self.batch_size, False

        logger.warning(f"Duration {current_duration_hours:.2f}h > {MAX_DURATION_HOURS}h. Triggering optimization.")
        
        # Reduce batch size to 1 for maximum memory safety
        new_batch_size = 1
        self.batch_size = new_batch_size
        
        # Force garbage collection immediately
        gc.collect()
        
        logger.info(f"Optimized: batch_size set to {new_batch_size}, GC forced.")
        return new_batch_size, True

    def load_sample_memory_efficient(self, audio_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load a single audio sample with memory-efficient practices:
        - Stream loading if possible (not fully supported by librosa, but we limit size)
        - Immediate cleanup of temporary buffers
        - Enforce max length to prevent large allocations
        """
        try:
            import librosa
            
            # Load only the necessary portion
            # librosa.load loads the whole file into memory, so we limit duration
            y, sr = librosa.load(
                str(audio_path),
                sr=self.sample_rate,
                duration=self.max_length,
                mono=True
            )
            
            # Immediate cleanup of any large local variables
            result = {
                "audio": y,
                "sample_rate": sr,
                "path": str(audio_path)
            }
            
            # Force GC if memory is high
            if self.enable_gc_during_batch:
                current_mem = self.get_memory_usage_gb()
                if current_mem > self.memory_limit_gb * 0.8:
                    logger.debug("Memory high during load, forcing GC.")
                    gc.collect()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to load sample {audio_path}: {e}")
            return None

    def process_batch(self, samples: List[Path]) -> List[Optional[Dict[str, Any]]]:
        """
        Process a batch of samples with memory-efficient loading.
        Returns list of results, where None indicates failure for that sample.
        """
        results = []
        for i, sample_path in enumerate(samples):
            if check_aborted():
                reason = get_abort_reason()
                logger.critical(f"Pipeline aborted: {reason}")
                sys.exit(1)
            
            result = self.load_sample_memory_efficient(sample_path)
            results.append(result)
            
            # Clean up after each sample to prevent accumulation
            if self.enable_gc_during_batch:
                current_mem = self.get_memory_usage_gb()
                if current_mem > self.memory_limit_gb * 0.9:
                    logger.warning("Memory critical during batch processing, forcing GC.")
                    gc.collect()
            
            # Small sleep to allow OS to reclaim memory
            if i % 10 == 0 and i > 0:
                time.sleep(0.1)
        
        return results

    def run_optimization_check(self, benchmark_results_path: Path) -> Dict[str, Any]:
        """
        Read benchmark results, check duration, and apply optimization if needed.
        Returns a report of the optimization action taken.
        """
        if not benchmark_results_path.exists():
            logger.error(f"Benchmark results not found at {benchmark_results_path}")
            return {"status": "error", "message": "Benchmark results not found"}

        try:
            with open(benchmark_results_path, 'r') as f:
                benchmark_data = json.load(f)
            
            duration_hours = benchmark_data.get("duration_hours", 0)
            original_batch_size = benchmark_data.get("original_batch_size", self.batch_size)
            
            optimized_batch, was_optimized = self.adjust_batch_size(duration_hours)
            
            report = {
                "original_duration_hours": duration_hours,
                "original_batch_size": original_batch_size,
                "optimized_batch_size": optimized_batch,
                "was_optimized": was_optimized,
                "target_duration_hours": TARGET_DURATION_HOURS,
                "status": "optimized" if was_optimized else "no_action_needed"
            }
            
            if was_optimized:
                logger.info(f"Optimization applied. New batch size: {optimized_batch}")
            else:
                logger.info("No optimization required.")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to process benchmark results: {e}")
            return {"status": "error", "message": str(e)}

def main():
    """
    Main entry point for the memory optimization task.
    Reads benchmark results from T033a, applies optimization if needed,
    and writes an optimization report.
    """
    init_logging()
    
    # Define paths
    project_root = Path(__file__).parent.parent
    benchmark_path = project_root / "results" / "benchmark_duration.json"
    optimization_report_path = project_root / "results" / "optimization_report.json"
    
    optimizer = MemoryOptimizer()
    
    # Run optimization check
    report = optimizer.run_optimization_check(benchmark_path)
    
    # Save report
    with open(optimization_report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Optimization report saved to {optimization_report_path}")
    print(json.dumps(report, indent=2))
    
    return report

if __name__ == "__main__":
    main()
