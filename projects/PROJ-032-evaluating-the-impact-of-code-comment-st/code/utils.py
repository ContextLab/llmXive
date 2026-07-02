import logging
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator, List, Any, Optional
import threading
import random
from datetime import datetime

def configure_logging(log_path: str = "logs/pipeline.log") -> logging.Logger:
    """Set up file and console handlers with INFO/ERROR levels."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    fh_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_format)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    ch_format = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(ch_format)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

class BatchIterator:
    """Iterator with semaphore logic to enforce max concurrent clones."""
    def __init__(self, items: List[Any], max_concurrent: int = 10):
        self.items = items
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(max_concurrent)
        self._index = 0
        self._lock = threading.Lock()

    def __iter__(self) -> Iterator[Any]:
        return self

    def __next__(self) -> Any:
        with self._lock:
            if self._index >= len(self.items):
                raise StopIteration
            item = self.items[self._index]
            self._index += 1

        self.semaphore.acquire()
        return item

    def release(self):
        """Call this after processing an item to release the semaphore."""
        self.semaphore.release()

class MemoryMonitor:
    """Monitor memory usage using psutil."""
    def __init__(self):
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            raise ImportError("psutil is required for MemoryMonitor. Install with 'pip install psutil'.")

    def check_limit(self, limit_gb: float = 7) -> bool:
        """Check if current memory usage exceeds limit_gb. Raises MemoryError if exceeded."""
        process = self.psutil.Process(os.getpid())
        mem_info = process.memory_info()
        current_gb = mem_info.rss / (1024 ** 3)

        if current_gb > limit_gb:
            raise MemoryError(f"Memory limit exceeded: {current_gb:.2f} GB > {limit_gb} GB")
        return True

    def check_and_log(self, limit_gb: float = 7, logger_name: str = "llmXive") -> bool:
        """Check memory limit and log the current usage. Returns True if within limit.
        
        Args:
            limit_gb: Maximum allowed memory in GB.
            logger_name: Name of the logger to use for reporting.
        
        Returns:
            True if memory is within limits, False otherwise.
        
        Raises:
            MemoryError: If memory limit is exceeded.
        """
        logger = logging.getLogger(logger_name)
        process = self.psutil.Process(os.getpid())
        mem_info = process.memory_info()
        current_gb = mem_info.rss / (1024 ** 3)
        
        logger.info(f"Current memory usage: {current_gb:.2f} GB (Limit: {limit_gb} GB)")
        
        if current_gb > limit_gb:
            raise MemoryError(f"Memory limit exceeded: {current_gb:.2f} GB > {limit_gb} GB")
        return True

class CommitSampler:
    """Select representative commits for static analysis."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the sampler.
        
        Args:
            seed: Random seed for reproducibility.
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def sample_commits(self, commits: List[Any], n: int = 10) -> List[Any]:
        """Select representative commits for static analysis.
        
        Args:
            commits: List of commit objects (e.g., from git log).
            n: Number of commits to sample.
            
        Returns:
            List of n sampled commits.
            
        Raises:
            ValueError: If n is greater than the number of available commits.
        """
        if not commits:
            return []
        
        if n <= 0:
            return []
        
        if n > len(commits):
            raise ValueError(f"Cannot sample {n} commits from a list of {len(commits)} commits.")
        
        # If we have fewer commits than requested, return all unique commits
        if len(commits) <= n:
            return list(commits)
        
        # Stratified sampling logic could be added here if commit metadata
        # (e.g., date, author, size) is available. For now, we use random sampling
        # to ensure representativeness across the commit history.
        sampled = random.sample(commits, n)
        return sampled

def generate_manual_labels(output_path: str = "data/manual_labels.csv") -> None:
    """Generate a CSV file with manual labels for commit quality.
    
    This function simulates manual labeling by using commit message keywords
    to classify commits as 'bug_fix' or 'not_bug_fix' for automation purposes.
    
    Args:
        output_path: Path to save the CSV file.
    """
    import csv
    from pathlib import Path
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Keywords that typically indicate a bug fix
    bug_fix_keywords = [
        'fix', 'bug', 'error', 'issue', 'patch', 'resolve', 'correct',
        'repair', 'defect', 'crash', 'exception', 'failure'
    ]
    
    # This is a placeholder for real data loading logic.
    # In a real implementation, this would iterate over actual commits
    # from the cloned repositories and apply the keyword heuristic.
    # For now, we create an empty CSV with headers as a structural placeholder
    # until real commit data is available from T013/T014.
    
    headers = ['commit_hash', 'repo_id', 'label', 'confidence']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
    
    logging.getLogger("llmXive").info(f"Generated manual labels structure at {output_path}")

def run_metric_aggregation_with_memory_monitor(
    metric_functions: List,
    repo_paths: List[str],
    limit_gb: float = 7.0,
    output_path: str = "data/processed/metrics.csv"
) -> None:
    """Aggregate metrics from multiple repositories while monitoring memory usage.
    
    This function ensures that MemoryMonitor is active during metric aggregation
    to stay within acceptable RAM limits. It processes repositories in batches
    and checks memory usage before and after each batch.
    
    Args:
        metric_functions: List of metric calculation functions to apply.
        repo_paths: List of paths to repository directories.
        limit_gb: Maximum allowed memory in GB.
        output_path: Path to save the aggregated metrics CSV.
        
    Raises:
        MemoryError: If memory usage exceeds the limit during processing.
    """
    import csv
    from pathlib import Path
    
    logger = logging.getLogger("llmXive")
    monitor = MemoryMonitor()
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting metric aggregation for {len(repo_paths)} repositories with {len(metric_functions)} metrics")
    logger.info(f"Memory limit set to {limit_gb} GB")
    
    # Check initial memory state
    monitor.check_and_log(limit_gb)
    
    results = []
    headers = ['repo_id'] + [func.__name__ for func in metric_functions]
    
    batch_size = 5
    for i in range(0, len(repo_paths), batch_size):
        batch = repo_paths[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(repo_paths)-1)//batch_size + 1}")
        
        # Check memory before processing batch
        monitor.check_and_log(limit_gb)
        
        for repo_path in batch:
            try:
                repo_id = os.path.basename(repo_path)
                row = {'repo_id': repo_id}
                
                for func in metric_functions:
                    # Check memory periodically during metric calculation
                    if len(results) % 10 == 0:
                        monitor.check_and_log(limit_gb)
                    
                    try:
                        value = func(repo_path)
                        row[func.__name__] = round(value, 2) if isinstance(value, float) else value
                    except Exception as e:
                        logger.warning(f"Error calculating {func.__name__} for {repo_id}: {e}")
                        row[func.__name__] = None
                
                results.append(row)
            except Exception as e:
                logger.error(f"Error processing repository {repo_path}: {e}")
        
        # Check memory after processing batch
        monitor.check_and_log(limit_gb)
    
    # Write results to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Metric aggregation complete. Results saved to {output_path}")
    logger.info(f"Processed {len(results)} repositories")