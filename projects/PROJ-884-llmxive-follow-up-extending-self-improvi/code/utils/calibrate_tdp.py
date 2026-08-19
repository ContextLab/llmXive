import json
import os
import time
import subprocess
import sys
import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure we can import from the project root if run as a module
# The project structure assumes 'code' is in the PYTHONPATH or we run from root
try:
    from utils.logger import setup_logging
except ImportError:
    # Fallback for direct execution or different import context
    import logging as stdlib_logging
    setup_logging = lambda: stdlib_logging.getLogger(__name__)

class CalibrationError(Exception):
    """Custom exception for TDP calibration failures."""
    pass

def get_cpu_base_frequency() -> float:
    """
    Attempts to detect the CPU base frequency in GHz.
    Falls back to a safe default (2.0 GHz) if detection fails.
    """
    # Linux: /proc/cpuinfo
    if sys.platform.startswith('linux'):
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'cpu MHz' in line:
                        # Take the first value found as an approximation
                        freq = float(line.split(':')[1].strip())
                        return freq / 1000.0
        except (IOError, ValueError, IndexError):
            pass
    # macOS: sysctl
    elif sys.platform == 'darwin':
        try:
            result = subprocess.run(['sysctl', '-n', 'hw.cpufrequency'],
                                    capture_output=True, text=True, check=True)
            freq = float(result.stdout.strip())
            return freq / 1000000000.0
        except (subprocess.CalledProcessError, ValueError):
            pass
    # Windows: wmic (requires admin or specific permissions, might fail in containers)
    elif sys.platform == 'win32':
        try:
            result = subprocess.run(['wmic', 'cpu', 'get', 'MaxClockSpeed'],
                                    capture_output=True, text=True, check=True)
            # Output format: MaxClockSpeed\n<value>\n
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                freq = float(lines[1].strip())
                return freq  # Usually in MHz
        except (subprocess.CalledProcessError, ValueError, IndexError):
            pass

    # Default fallback
    logging.warning("Could not determine CPU base frequency. Defaulting to 2.0 GHz.")
    return 2.0

def get_cpu_utilization() -> float:
    """
    Measures CPU utilization percentage over a short interval.
    Uses psutil if available, otherwise falls back to a simple shell command.
    Returns a float between 0.0 and 100.0.
    """
    try:
        import psutil
        # psutil.cpu_percent(interval=1) blocks for 1 second to get accurate reading
        return psutil.cpu_percent(interval=1.0)
    except ImportError:
        logging.warning("psutil not found. Using fallback CPU usage estimation.")
        # Fallback: read /proc/stat (Linux only)
        if sys.platform.startswith('linux'):
            try:
                def get_cpu_times():
                    with open('/proc/stat', 'r') as f:
                        line = f.readline()
                    parts = line.split()
                    # user, nice, system, idle, iowait, irq, softirq, steal
                    return [int(p) for p in parts[1:]]

                t1 = get_cpu_times()
                time.sleep(1.0)
                t2 = get_cpu_times()

                diff = [t2[i] - t1[i] for i in range(len(t1))]
                total = sum(diff)
                idle = diff[3]  # idle is index 3

                if total == 0:
                    return 0.0
                usage = (1.0 - (idle / total)) * 100.0
                return usage
            except Exception as e:
                logging.error(f"Failed to read CPU stats: {e}")
                return 0.0
        else:
            # Generic fallback: 0% (safe assumption if we can't measure)
            return 0.0

def run_calibration_workload(duration_seconds: float = 5.0) -> Dict[str, Any]:
    """
    Runs a deterministic, CPU-intensive workload for the specified duration.
    The workload is a fixed matrix multiplication to ensure reproducibility.
    Returns metrics: start_time, end_time, duration, cpu_percent, workload_type.
    """
    import numpy as np
    import time

    logging.info(f"Starting calibration workload for {duration_seconds} seconds...")

    # 1. Warm up (avoid cold start effects)
    _ = np.random.rand(500, 500)
    _ = np.dot(_, _)

    # 2. Main workload
    start_time = time.time()
    end_time = start_time + duration_seconds
    
    # We will sample CPU usage during the loop
    cpu_samples = []
    workload_active = True

    try:
        # Create a deterministic matrix
        np.random.seed(42)
        size = 1000
        matrix_a = np.random.rand(size, size)
        matrix_b = np.random.rand(size, size)

        while time.time() < end_time:
            # Perform a heavy operation
            _ = np.dot(matrix_a, matrix_b)
            
            # Sample CPU usage periodically (every 0.5s roughly)
            if time.time() % 0.5 < 0.1:
                cpu_samples.append(get_cpu_utilization())

        elapsed = time.time() - start_time
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0

        return {
            "workload_type": "matrix_multiplication_deterministic",
            "start_time": start_time,
            "end_time": time.time(),
            "duration": elapsed,
            "cpu_percent": avg_cpu,
            "matrix_size": size,
            "seed": 42
        }

    except Exception as e:
        raise CalibrationError(f"Workload execution failed: {e}")

def estimate_tdp_from_frequency(cpu_percent: float, base_freq_ghz: float) -> float:
    """
    Estimates TDP (Thermal Design Power) in Watts based on CPU utilization and frequency.
    
    This is a simplified model:
    Power ∝ Frequency * Voltage^2
    Voltage roughly correlates with Frequency.
    Power ∝ Frequency^3
    
    We assume a base TDP of 65W for a standard desktop CPU at 100% load at base frequency.
    We scale based on observed utilization and frequency deviation.
    
    Note: This is an estimation heuristic as direct power measurement requires hardware sensors
    (RAPL, IPMI) which may not be available in all environments (e.g., GitHub Actions).
    """
    # Heuristic constants
    BASE_TDP_WATTS = 65.0  # Assumed base TDP for the reference CPU
    
    # If we can't get accurate frequency, assume base frequency
    if base_freq_ghz <= 0:
        base_freq_ghz = 2.0

    # Normalize CPU percent to 0-1
    load_factor = cpu_percent / 100.0

    # Estimate power: P = P_base * (Load) * (Freq_ratio)^3
    # Since we don't know the exact turbo boost, we assume load factor captures the thermal impact
    # and frequency is roughly proportional to load in this calibration context.
    # A simpler linear approximation for estimation in constrained envs:
    estimated_power = BASE_TDP_WATTS * load_factor

    # Add a small offset for idle power (approx 10W) to avoid 0W at low load
    # But for calibration, we want the delta. Let's stick to the load-based estimate.
    # If the runner is a cloud VM, the "TDP" is effectively the allocated power budget.
    
    # Refine: If we are running at 100% load, we are hitting the thermal limit.
    # If the environment is a container on a shared host, 'cpu_percent' might be capped.
    # We return the calculated estimate.
    
    return estimated_power

def calibrate_tdp(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main calibration function.
    1. Runs the workload.
    2. Measures CPU usage.
    3. Estimates TDP.
    4. Saves the result to JSON.
    """
    if output_path is None:
        output_path = "data/processed/calibration_run.json"
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        # Run workload
        result = run_calibration_workload(duration_seconds=5.0)
        
        # Get base frequency
        base_freq = get_cpu_base_frequency()
        
        # Estimate TDP
        estimated_tdp = estimate_tdp_from_frequency(result["cpu_percent"], base_freq)
        
        # Prepare final output
        calibration_result = {
            "workload_type": result["workload_type"],
            "cpu_percent": round(result["cpu_percent"], 2),
            "duration": round(result["duration"], 3),
            "estimated_tdp_watts": round(estimated_tdp, 2),
            "cpu_base_frequency_ghz": round(base_freq, 2),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # Write to file
        with open(output_path, 'w') as f:
            json.dump(calibration_result, f, indent=2)
        
        logging.info(f"Calibration complete. Results saved to {output_path}")
        logging.info(f"Estimated TDP: {calibration_result['estimated_tdp_watts']} W")
        
        return calibration_result

    except Exception as e:
        logging.error(f"Calibration failed: {e}")
        raise CalibrationError(f"TDP calibration failed: {e}")

def main():
    """Entry point for the script."""
    # Setup logging
    logger = setup_logging()
    logger.setLevel(logging.INFO)
    
    # Check for required dependencies
    try:
        import numpy
    except ImportError:
        logger.error("numpy is required for the calibration workload. Please install it.")
        sys.exit(1)
    
    try:
        result = calibrate_tdp()
        print(json.dumps(result, indent=2))
    except CalibrationError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()