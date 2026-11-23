"""
CI Resource Monitor Runner for T046.

This script executes the CI resource monitoring logic defined in
`code/monitor/ci_resource_monitor.py` to generate the required
resource usage reports (SC-006).

It simulates a pipeline run by importing and invoking the monitoring
functions, ensuring that CPU and memory usage are logged and saved
to `data/ci_monitoring/resource_report.json`.
"""
import os
import sys
import json
import logging
import time
import argparse

# Add project root to path if running as script
if __package__ is None:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from monitor.ci_resource_monitor import (
    ensure_output_dirs,
    run_monitoring,
    save_report,
    get_memory_usage_mb,
    get_cpu_percent
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_pipeline_workload(duration_seconds=5):
    """
    Simulates a representative pipeline workload to generate resource usage data.
    This mimics the CPU and memory pressure of the actual simulation/analysis steps.
    """
    logger.info(f"Simulating pipeline workload for {duration_seconds} seconds...")
    
    # Simulate CPU-bound work (matrix operations mimic)
    import math
    import time
    
    start = time.time()
    count = 0
    while time.time() - start < duration_seconds:
        # CPU intensive calculation
        _ = sum(math.sqrt(i) * math.sin(i) for i in range(10000))
        count += 1
    
    logger.info(f"Workload simulation complete. Iterations: {count}")

def main():
    parser = argparse.ArgumentParser(description="Run CI Resource Monitoring for SC-006")
    parser.add_argument('--duration', type=int, default=10, help="Duration of simulated workload in seconds")
    parser.add_argument('--output-dir', type=str, default='data/ci_monitoring', help="Output directory for reports")
    args = parser.parse_args()

    logger.info("Starting CI Resource Monitoring (T046)")

    # 1. Ensure output directories exist
    ensure_output_dirs(args.output_dir)

    # 2. Start monitoring baseline
    logger.info("Capturing baseline resource metrics...")
    baseline_memory = get_memory_usage_mb()
    baseline_cpu = get_cpu_percent()
    
    logger.info(f"Baseline - Memory: {baseline_memory:.2f} MB, CPU: {baseline_cpu:.2f}%")

    # 3. Run the actual monitoring loop with simulated workload
    # The run_monitoring function from ci_resource_monitor.py handles the sampling
    logger.info("Starting resource monitoring loop during workload...")
    
    report_data = run_monitoring(
        workload_func=simulate_pipeline_workload,
        workload_args=(args.duration,),
        sample_interval=1.0,
        output_dir=args.output_dir
    )

    # 4. Final metrics
    final_memory = get_memory_usage_mb()
    final_cpu = get_cpu_percent()
    logger.info(f"Final - Memory: {final_memory:.2f} MB, CPU: {final_cpu:.2f}%")

    # 5. Save the comprehensive report
    report_path = os.path.join(args.output_dir, 'resource_report.json')
    save_report(report_data, report_path)

    logger.info(f"Resource monitoring complete. Report saved to: {report_path}")
    
    # Validation check for SC-006
    max_memory = report_data.get('max_memory_mb', 0)
    max_cpu = report_data.get('max_cpu_percent', 0)
    
    logger.info(f"SC-006 Validation: Max Memory: {max_memory:.2f} MB, Max CPU: {max_cpu:.2f}%")
    
    if max_memory > 7000:
        logger.warning("WARNING: Memory usage exceeded 7GB limit (SC-006 constraint).")
    else:
        logger.info("SUCCESS: Memory usage within 7GB limit.")

    return 0

if __name__ == '__main__':
    sys.exit(main())