import os
import sys
import time
import logging
import resource
from typing import Callable, Optional, Any, Dict

class PerformanceMonitor:
    """Monitor performance metrics during pipeline execution."""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.metrics = {}
    
    def start(self):
        """Start monitoring."""
        self.start_time = time.time()
        self.start_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        logging.info("Performance monitoring started")
    
    def stop(self):
        """Stop monitoring and record final metrics."""
        end_time = time.time()
        end_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        self.metrics['duration_seconds'] = end_time - self.start_time
        self.metrics['peak_memory_kb'] = end_memory
        self.metrics['memory_increase_kb'] = end_memory - self.start_memory
        
        logging.info(f"Performance monitoring stopped: {self.metrics}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get recorded metrics."""
        return self.metrics

def performance_watchdog(max_duration: float = 3600, max_memory_mb: float = 7000):
    """
    Decorator to watchdog pipeline execution for time and memory limits.
    
    Args:
        max_duration: Maximum allowed duration in seconds
        max_memory_mb: Maximum allowed memory in MB
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert to MB
            
            try:
                result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                end_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
                
                if duration > max_duration:
                    raise TimeoutError(f"Function exceeded max duration: {duration:.2f}s > {max_duration}s")
                
                if end_memory > max_memory_mb:
                    raise MemoryError(f"Function exceeded max memory: {end_memory:.2f}MB > {max_memory_mb}MB")
                
                return result
            except Exception as e:
                logging.error(f"Function failed: {e}")
                raise
        
        return wrapper
    return decorator

def optimize_dataframe_operations(df):
    """
    Optimize dataframe operations for memory efficiency.
    
    Args:
        df: Pandas DataFrame
        
    Returns:
        Optimized DataFrame
    """
    import pandas as pd
    
    # Downcast numeric columns
    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    # Convert object columns to category where appropriate
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:  # If fewer than 50% unique values
            df[col] = df[col].astype('category')
    
    return df

def run_pipeline_with_monitoring(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Run a pipeline function with performance monitoring.
    
    Args:
        func: Function to run
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Dictionary with results and performance metrics
    """
    monitor = PerformanceMonitor()
    monitor.start()
    
    try:
        result = func(*args, **kwargs)
        monitor.stop()
        
        return {
            'result': result,
            'performance': monitor.get_metrics()
        }
    except Exception as e:
        monitor.stop()
        logging.error(f"Pipeline failed: {e}")
        raise

def main():
    """Main entry point for performance monitoring demonstration."""
    logging.basicConfig(level=logging.INFO)
    
    @performance_watchdog(max_duration=300, max_memory_mb=7000)
    def dummy_pipeline():
        time.sleep(1)
        return "Success"
    
    print("Running dummy pipeline with monitoring...")
    result = run_pipeline_with_monitoring(dummy_pipeline)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()