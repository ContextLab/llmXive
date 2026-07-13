"""
CI Memory Profiler for T043.
Orchestrates memory monitoring for all major pipeline scripts and logs
peak usage to data/artifacts/memory_profile.log.
"""
import os
import sys
import time
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# Add code directory to path for imports if running as script
if __name__ == "__main__":
    code_dir = Path(__file__).parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

from utils.logger import get_logger
from utils.io import ensure_dir

# Configuration
SCRIPTS_TO_PROFILE = [
    "00_data_gate.py",
    "01_download_and_filter.py",
    "02_preprocess_and_parcellate.py",
    "03_compute_graph_metrics.py",
    "04_train_model.py",
    "05_evaluate_model.py",
    "06_runtime_verifier.py",
    "07_sensitivity_analysis.py",
    "09_generate_report.py",
    "10_verify_success_criteria.py",
    "11_external_outcome_check.py",
]

OUTPUT_FILE = "data/artifacts/memory_profile.log"
MAX_DURATION_SECONDS = 3600  # 1 hour max per script for CI safety

logger = get_logger("ci_memory_profiler")

class MemoryMonitor:
    """
    Lightweight memory monitor that samples RSS usage of a process.
    """
    def __init__(self, pid):
        self.pid = pid
        self.peak_memory_bytes = 0
        self.samples = []
        self._stop_event = threading.Event()
        self._thread = None

    def _sample_loop(self):
        import psutil
        try:
            process = psutil.Process(self.pid)
            while not self._stop_event.is_set():
                try:
                    mem_info = process.memory_info()
                    current_rss = mem_info.rss
                    self.samples.append(current_rss)
                    if current_rss > self.peak_memory_bytes:
                        self.peak_memory_bytes = current_rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                time.sleep(0.5)  # Sample every 500ms
        except Exception as e:
            logger.warning(f"Sampling error for PID {self.pid}: {e}")

    def start(self):
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def get_peak_gb(self):
        return self.peak_memory_bytes / (1024 ** 3)

def run_script_with_monitoring(script_name, output_file_path):
    """
    Runs a specific script and monitors its memory usage.
    Returns a dict with results.
    """
    script_path = Path("code") / script_name
    if not script_path.exists():
        logger.warning(f"Script not found: {script_path}")
        return {
            "script": script_name,
            "status": "skipped",
            "reason": "file_not_found",
            "peak_memory_gb": 0.0,
            "duration_seconds": 0.0
        }

    logger.info(f"Profiling {script_name}...")
    start_time = time.time()
    
    # Start the process
    try:
        proc = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        monitor = MemoryMonitor(proc.pid)
        monitor.start()
        
        try:
            stdout, stderr = proc.communicate(timeout=MAX_DURATION_SECONDS)
            exit_code = proc.returncode
            
            # Decode output if needed for logging
            if stdout:
                logger.debug(f"Output from {script_name}: {stdout.decode()[:200]}...")
            if stderr:
                logger.debug(f"Errors from {script_name}: {stderr.decode()[:200]}...")
                
            # Note: We don't fail the profiler if the script fails, 
            # we just log the memory usage up to the crash.
            
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            exit_code = -1
            logger.error(f"Script {script_name} timed out after {MAX_DURATION_SECONDS}s")
        
        monitor.stop()
        end_time = time.time()
        
        duration = end_time - start_time
        peak_gb = monitor.get_peak_gb()
        
        return {
            "script": script_name,
            "status": "completed" if exit_code == 0 else "failed",
            "exit_code": exit_code,
            "peak_memory_gb": round(peak_gb, 4),
            "duration_seconds": round(duration, 2)
        }
        
    except Exception as e:
        logger.error(f"Failed to run {script_name}: {e}")
        return {
            "script": script_name,
            "status": "error",
            "reason": str(e),
            "peak_memory_gb": 0.0,
            "duration_seconds": 0.0
        }

def main():
    """
    Main entry point for the CI memory profiler.
    Runs all scripts and appends results to the log file.
    """
    ensure_dir(Path(OUTPUT_FILE).parent)
    
    results = []
    timestamp = datetime.now().isoformat()
    
    logger.info(f"Starting CI Memory Profiler run at {timestamp}")
    
    for script in SCRIPTS_TO_PROFILE:
        result = run_script_with_monitoring(script, OUTPUT_FILE)
        results.append(result)
        logger.info(f"Finished {script}: Peak={result['peak_memory_gb']:.2f}GB, Status={result['status']}")
    
    # Write results to log file
    log_entry = {
        "timestamp": timestamp,
        "results": results
    }
    
    # Append to log file (JSON lines format or structured log)
    # For this task, we will write a structured JSON block for easy parsing
    # but also a human-readable summary at the end.
    
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"--- Run Started: {timestamp} ---\n")
        for res in results:
            f.write(f"Script: {res['script']}\n")
            f.write(f"  Status: {res['status']}\n")
            f.write(f"  Peak Memory (GB): {res['peak_memory_gb']}\n")
            f.write(f"  Duration (s): {res['duration_seconds']}\n")
            if 'reason' in res:
                f.write(f"  Reason: {res['reason']}\n")
            f.write("\n")
        f.write(f"--- Run Ended ---\n\n")
    
    logger.info(f"Memory profile log written to {OUTPUT_FILE}")
    print(f"Memory profiling complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
