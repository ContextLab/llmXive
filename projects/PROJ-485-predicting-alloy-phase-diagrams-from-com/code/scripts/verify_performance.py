"""
Script to verify performance optimizations are working correctly.
Runs the pipeline with optimized components and compares metrics.
"""
import os
import sys
import json
import time
import argparse
from typing import Dict, Any
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from utils.performance_optimizer import run_performance_benchmark, OptimizedResourceMonitor

logger = get_logger(__name__)

def run_optimized_pipeline_test(
    data_path: str,
    props_path: str,
    benchmark_output: str = "data/artifacts/performance_benchmark.json",
    resource_output: str = "data/artifacts/resource_log.json"
) -> Dict[str, Any]:
    """
    Run the pipeline with optimized components and verify performance.
    Returns a report with performance metrics and optimization status.
    """
    logger.info("Starting optimized pipeline verification")
    
    report = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'PENDING',
        'metrics': {},
        'optimizations_applied': [],
        'issues': []
    }
    
    # Initialize resource monitor
    monitor = OptimizedResourceMonitor(max_memory_gb=7.0, max_time_seconds=14400)
    monitor.start_monitoring()
    
    try:
        # Run performance benchmark
        logger.info("Running performance benchmark...")
        benchmark_results = run_performance_benchmark(data_path, props_path, benchmark_output)
        
        if not benchmark_results.get('components'):
            report['issues'].append("No benchmark components recorded")
            report['status'] = 'FAILED'
            return report
        
        report['optimizations_applied'].extend(benchmark_results.get('components', {}).keys())
        
        # Extract metrics
        metrics = {}
        for component, data in benchmark_results.get('components', {}).items():
            if 'execution_time_seconds' in data:
                metrics[f'{component}_time'] = data['execution_time_seconds']
            if 'memory_gb' in data:
                metrics[f'{component}_memory_gb'] = data['memory_gb']
        
        report['metrics'] = metrics
        
        # Check resource limits
        if monitor.check_limits():
            report['status'] = 'FAILED'
            report['issues'].append("Resource limits exceeded")
            log_error(ErrorCode.RESOURCE_LIMIT_EXCEEDED, "Pipeline exceeded resource limits")
        else:
            # Log resource usage
            monitor.log_resource_usage(resource_output)
            report['metrics']['peak_memory_gb'] = monitor.get_peak_memory_gb()
            report['metrics']['execution_time_seconds'] = monitor.get_execution_time_seconds()
            
            # Check for memory leaks
            if monitor.check_memory_leak(window_minutes=5, threshold_percent=10.0):
                report['status'] = 'WARNING'
                report['issues'].append("Potential memory leak detected")
                log_warning(ErrorCode.POTENTIAL_MEMORY_LEAK, "Memory leak detected during verification")
            else:
                report['status'] = 'PASSED'
                log_info("PERFORMANCE_VERIFIED", "All performance checks passed")
        
    except Exception as e:
        report['status'] = 'FAILED'
        report['issues'].append(f"Verification failed: {str(e)}")
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Verification error: {str(e)}")
    
    return report

def main():
    """Main entry point for performance verification."""
    parser = argparse.ArgumentParser(description="Verify performance optimizations")
    parser.add_argument('--data', default='data/processed/descriptors.csv', help='Input data path')
    parser.add_argument('--props', default='data/raw/elemental_properties.csv', help='Elemental properties path')
    parser.add_argument('--benchmark-output', default='data/artifacts/performance_benchmark.json', help='Benchmark output path')
    parser.add_argument('--resource-output', default='data/artifacts/resource_log.json', help='Resource log output path')
    
    args = parser.parse_args()
    
    # Check input files exist
    if not os.path.exists(args.data):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Data file not found: {args.data}")
        print(f"Error: Data file not found: {args.data}")
        sys.exit(1)
    
    if not os.path.exists(args.props):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Properties file not found: {args.props}")
        print(f"Error: Properties file not found: {args.props}")
        sys.exit(1)
    
    # Run verification
    report = run_optimized_pipeline_test(
        args.data,
        args.props,
        args.benchmark_output,
        args.resource_output
    )
    
    # Output report
    print(json.dumps(report, indent=2))
    
    # Exit with appropriate code
    if report['status'] == 'FAILED':
        sys.exit(1)
    elif report['status'] == 'WARNING':
        sys.exit(0)  # Warning is acceptable
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
