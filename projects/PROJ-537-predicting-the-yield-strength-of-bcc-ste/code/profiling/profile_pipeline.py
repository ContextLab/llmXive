"""
Pipeline profiling and optimization module.

This script profiles the execution of the full pipeline to identify
bottlenecks and optimize memory/CPU usage to ensure < 6h runtime on 2 CPU cores.

Usage:
    python code/profiling/profile_pipeline.py
    
Output:
    - data/provenance/profile_results.json: Detailed profiling data
    - data/provenance/memory_snapshot.json: Memory usage snapshots
    - data/provenance/cpu_usage.json: CPU utilization metrics
    - data/provenance/optimization_report.txt: Recommendations
"""

import os
import sys
import json
import time
import logging
import resource
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import CONFIG
from utils.logging import get_logger, log_provenance_event
from main import run_full_pipeline

# Configure logging
logger = get_logger(__name__)

class PipelineProfiler:
    """Profiles pipeline execution for memory, CPU, and time."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.memory_snapshots: List[Dict[str, Any]] = []
        self.cpu_snapshots: List[Dict[str, Any]] = []
        self.phase_timings: Dict[str, float] = {}
        self.process: psutil.Process = psutil.Process()
        
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        mem_info = self.process.memory_info()
        return {
            "timestamp": datetime.now().isoformat(),
            "rss_mb": mem_info.rss / (1024 * 1024),
            "vms_mb": mem_info.vms / (1024 * 1024),
            "percent": self.process.memory_percent()
        }
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get current CPU usage information."""
        return {
            "timestamp": datetime.now().isoformat(),
            "percent": self.process.cpu_percent(interval=0.1),
            "num_threads": self.process.num_threads()
        }
    
    def _take_snapshots(self, duration: float = 1.0, interval: float = 0.1):
        """Take periodic snapshots of memory and CPU usage."""
        iterations = int(duration / interval)
        for _ in range(iterations):
            self.memory_snapshots.append(self._get_memory_info())
            self.cpu_snapshots.append(self._get_cpu_info())
            time.sleep(interval)
    
    @contextmanager
    def profile_phase(self, phase_name: str):
        """Context manager to profile a specific phase."""
        logger.info(f"Starting phase: {phase_name}")
        phase_start = time.time()
        
        # Take initial snapshots
        self._take_snapshots(duration=0.5, interval=0.1)
        
        try:
            yield
        finally:
            phase_end = time.time()
            duration = phase_end - phase_start
            self.phase_timings[phase_name] = duration
            logger.info(f"Completed phase: {phase_name} in {duration:.2f}s")
            
            # Take final snapshots
            self._take_snapshots(duration=0.5, interval=0.1)
    
    def run_profiling(self) -> Dict[str, Any]:
        """Run the full pipeline with profiling."""
        logger.info("Starting pipeline profiling")
        self.start_time = time.time()
        
        # Initial snapshots
        self._take_snapshots(duration=1.0, interval=0.2)
        
        try:
            with self.profile_phase("ingestion"):
                # Run ingestion pipeline
                from main import run_ingestion_pipeline
                run_ingestion_pipeline()
            
            with self.profile_phase("modeling"):
                # Run modeling pipeline
                from main import run_modeling_pipeline
                run_modeling_pipeline()
            
            with self.profile_phase("interpretability"):
                # Run interpretability pipeline
                from main import run_interpretability_pipeline
                run_interpretability_pipeline()
                
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
        finally:
            self.end_time = time.time()
            
        # Final snapshots
        self._take_snapshots(duration=1.0, interval=0.2)
        
        # Calculate totals
        total_time = self.end_time - self.start_time
        max_memory = max([s["rss_mb"] for s in self.memory_snapshots]) if self.memory_snapshots else 0
        avg_cpu = sum([s["percent"] for s in self.cpu_snapshots]) / len(self.cpu_snapshots) if self.cpu_snapshots else 0
        
        return {
            "total_time_seconds": total_time,
            "total_time_hours": total_time / 3600,
            "max_memory_mb": max_memory,
            "avg_cpu_percent": avg_cpu,
            "phase_timings": self.phase_timings,
            "memory_snapshots": self.memory_snapshots[-10:],  # Last 10 snapshots
            "cpu_snapshots": self.cpu_snapshots[-10:],
            "status": "success" if total_time < 6 * 3600 else "exceeded_target"
        }
    
    def save_results(self, results: Dict[str, Any]):
        """Save profiling results to disk."""
        provenance_dir = CONFIG.PROVENANCE_DIR
        provenance_dir.mkdir(parents=True, exist_ok=True)
        
        # Save detailed results
        results_path = provenance_dir / "profile_results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        
        # Save memory snapshots
        memory_path = provenance_dir / "memory_snapshot.json"
        with open(memory_path, "w") as f:
            json.dump(self.memory_snapshots, f, indent=2)
        
        # Save CPU snapshots
        cpu_path = provenance_dir / "cpu_usage.json"
        with open(cpu_path, "w") as f:
            json.dump(self.cpu_snapshots, f, indent=2)
        
        # Generate optimization report
        report = self._generate_optimization_report(results)
        report_path = provenance_dir / "optimization_report.txt"
        with open(report_path, "w") as f:
            f.write(report)
        
        logger.info(f"Profiling results saved to {provenance_dir}")
        
        return {
            "profile_results": str(results_path),
            "memory_snapshot": str(memory_path),
            "cpu_usage": str(cpu_path),
            "optimization_report": str(report_path)
        }
    
    def _generate_optimization_report(self, results: Dict[str, Any]) -> str:
        """Generate an optimization recommendations report."""
        report_lines = [
            "=" * 80,
            "PIPELINE OPTIMIZATION REPORT",
            "=" * 80,
            "",
            "EXECUTION SUMMARY",
            "-" * 40,
            f"Total Runtime: {results['total_time_hours']:.2f} hours",
            f"Target Runtime: < 6.0 hours",
            f"Status: {'PASS' if results['status'] == 'success' else 'EXCEEDED TARGET'}",
            f"Peak Memory: {results['max_memory_mb']:.2f} MB",
            f"Average CPU: {results['avg_cpu_percent']:.2f}%",
            "",
            "PHASE BREAKDOWN",
            "-" * 40,
        ]
        
        for phase, duration in results["phase_timings"].items():
            percentage = (duration / results["total_time_seconds"]) * 100
            report_lines.append(f"  {phase}: {duration:.2f}s ({percentage:.1f}%)")
        
        report_lines.extend([
            "",
            "OPTIMIZATION RECOMMENDATIONS",
            "-" * 40,
        ])
        
        recommendations = []
        
        # Check for CPU bottlenecks
        if results["avg_cpu_percent"] > 80:
            recommendations.append(
                "1. CPU-bound: Consider parallelizing data loading and model training. "
                "Use joblib or multiprocessing for independent tasks."
            )
        
        # Check for memory bottlenecks
        if results["max_memory_mb"] > 4000:  # 4GB threshold
            recommendations.append(
                "2. Memory-bound: Consider processing data in chunks. "
                "Use generator-based data loaders instead of loading entire datasets into memory."
            )
        
        # Check phase-specific issues
        if "modeling" in results["phase_timings"]:
            modeling_time = results["phase_timings"]["modeling"]
            if modeling_time > 1800:  # 30 minutes
                recommendations.append(
                    "3. Modeling phase is slow: Consider reducing cross-validation folds "
                    "or using fewer trees in Random Forest for initial runs. "
                    "Enable joblib caching for repeated operations."
                )
        
        if "interpretability" in results["phase_timings"]:
            interp_time = results["phase_timings"]["interpretability"]
            if interp_time > 1800:
                recommendations.append(
                    "4. Interpretability phase is slow: SHAP calculations are computationally expensive. "
                    "Consider sampling fewer data points for SHAP or using a faster explainer "
                    "like TreeExplainer with reduced sample size."
                )
        
        # General recommendations
        recommendations.extend([
            "5. Enable multi-threading for NumPy/SciPy operations by setting OMP_NUM_THREADS=2",
            "6. Use efficient data formats (Parquet instead of CSV for intermediate data)",
            "7. Consider using joblib.Memory for caching expensive function calls",
            "8. Profile individual functions with cProfile for fine-grained optimization"
        ])
        
        for rec in recommendations:
            report_lines.append(rec)
        
        report_lines.extend([
            "",
            "CONCLUSION",
            "-" * 40,
        ])
        
        if results["status"] == "success":
            report_lines.append(
                "The pipeline meets the < 6h runtime target on 2 CPU cores. "
                "Continue monitoring for regressions as data size increases."
            )
        else:
            report_lines.append(
                "The pipeline exceeds the 6h target. Implement the recommended optimizations "
                "above to reduce runtime. Focus on the slowest phases first."
            )
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)

def main():
    """Main entry point for profiling."""
    logger.info("Starting pipeline profiling")
    
    profiler = PipelineProfiler()
    
    try:
        results = profiler.run_profiling()
        output_files = profiler.save_results(results)
        
        # Log provenance event
        log_provenance_event(
            event_type="pipeline_profile",
            details={
                "total_time_hours": results["total_time_hours"],
                "max_memory_mb": results["max_memory_mb"],
                "status": results["status"],
                "output_files": output_files
            }
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("PROFILING COMPLETE")
        print("=" * 60)
        print(f"Total Runtime: {results['total_time_hours']:.2f} hours")
        print(f"Target: < 6.0 hours")
        print(f"Status: {results['status'].upper()}")
        print(f"Peak Memory: {results['max_memory_mb']:.2f} MB")
        print(f"Average CPU: {results['avg_cpu_percent']:.2f}%")
        print("=" * 60)
        
        if results["status"] == "success":
            print("✓ Pipeline meets performance targets")
        else:
            print("⚠ Pipeline exceeds target - see optimization_report.txt")
        
        return 0
        
    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
