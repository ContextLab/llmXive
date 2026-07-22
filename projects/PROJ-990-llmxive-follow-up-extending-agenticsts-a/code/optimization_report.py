import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging for the analysis script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_benchmark_data(benchmark_path: str) -> Optional[Dict[str, Any]]:
    """
    Load the benchmark log from the specified JSON file.
    
    Args:
        benchmark_path: Path to the benchmark_log.json file.
        
    Returns:
        Dictionary containing benchmark data, or None if file not found/error.
    """
    path = Path(benchmark_path)
    if not path.exists():
        logger.error(f"Benchmark file not found: {benchmark_path}")
        return None
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded benchmark data from {benchmark_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse benchmark JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading benchmark data: {e}")
        return None

def analyze_bottlenecks(benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the benchmark data to identify bottlenecks and performance issues.
    
    Args:
        benchmark_data: Dictionary containing benchmark results.
        
    Returns:
        Dictionary containing analysis results.
    """
    if not benchmark_data:
        return {"error": "No benchmark data provided"}
    
    analysis = {
        "total_runtime_seconds": benchmark_data.get("total_runtime_seconds", 0),
        "phases": {},
        "bottlenecks": [],
        "recommendations": []
    }
    
    phases = benchmark_data.get("phases", {})
    if not phases:
        logger.warning("No phase data found in benchmark results")
        return analysis
    
    # Analyze each phase
    total_phase_time = sum(p.get("duration_seconds", 0) for p in phases.values())
    
    for phase_name, phase_data in phases.items():
        duration = phase_data.get("duration_seconds", 0)
        memory_mb = phase_data.get("memory_mb", 0)
        
        phase_analysis = {
            "duration_seconds": duration,
            "memory_mb": memory_mb,
            "percentage_of_total": (duration / total_phase_time * 100) if total_phase_time > 0 else 0
        }
        analysis["phases"][phase_name] = phase_analysis
        
        # Identify bottlenecks (phases taking > 20% of total time)
        if duration > 0 and total_phase_time > 0:
            percentage = (duration / total_phase_time) * 100
            if percentage > 20:
                analysis["bottlenecks"].append({
                    "phase": phase_name,
                    "duration_seconds": duration,
                    "percentage": percentage
                })
    
    # Sort bottlenecks by duration
    analysis["bottlenecks"].sort(key=lambda x: x["duration_seconds"], reverse=True)
    
    # Generate recommendations based on analysis
    if analysis["total_runtime_seconds"] > 6 * 3600:  # > 6 hours
        analysis["recommendations"].append(
            "Total runtime exceeds 6 hours. Consider parallelizing independent phases or optimizing bottlenecks."
        )
    
    if analysis["bottlenecks"]:
        top_bottleneck = analysis["bottlenecks"][0]
        analysis["recommendations"].append(
            f"Focus optimization efforts on '{top_bottleneck['phase']}' phase which consumes "
            f"{top_bottleneck['percentage']:.1f}% of total runtime."
        )
    
    # Check for memory issues
    high_memory_phases = [
        phase for phase, data in analysis["phases"].items()
        if data["memory_mb"] > 7000  # > 7GB
    ]
    if high_memory_phases:
        analysis["recommendations"].append(
            f"High memory usage detected in phases: {', '.join(high_memory_phases)}. "
            "Consider streaming data or reducing batch sizes."
        )
    
    # Determine if refactoring is needed
    analysis["refactoring_needed"] = (
        analysis["total_runtime_seconds"] > 6 * 3600 or
        len(analysis["bottlenecks"]) > 2 or
        len(high_memory_phases) > 0
    )
    
    return analysis

def generate_markdown_report(analysis: Dict[str, Any], output_path: str) -> None:
    """
    Generate a markdown report documenting the runtime analysis.
    
    Args:
        analysis: Dictionary containing analysis results.
        output_path: Path to write the markdown report.
    """
    if "error" in analysis:
        logger.error(f"Cannot generate report: {analysis['error']}")
        return
    
    lines = []
    lines.append("# Optimization Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Total Runtime**: {analysis['total_runtime_seconds'] / 3600:.2f} hours")
    lines.append(f"- **Refactoring Needed**: {'Yes' if analysis['refactoring_needed'] else 'No'}")
    lines.append("")
    
    if analysis["bottlenecks"]:
        lines.append("### Identified Bottlenecks")
        lines.append("")
        lines.append("| Phase | Duration (s) | % of Total |")
        lines.append("|-------|--------------|------------|")
        for bottleneck in analysis["bottlenecks"]:
            lines.append(
                f"| {bottleneck['phase']} | {bottleneck['duration_seconds']:.2f} | "
                f"{bottleneck['percentage']:.1f}% |"
            )
        lines.append("")
    
    lines.append("### Phase Breakdown")
    lines.append("")
    lines.append("| Phase | Duration (s) | Memory (MB) | % of Total |")
    lines.append("|-------|--------------|-------------|------------|")
    for phase_name, phase_data in analysis["phases"].items():
        lines.append(
            f"| {phase_name} | {phase_data['duration_seconds']:.2f} | "
            f"{phase_data['memory_mb']:.2f} | {phase_data['percentage_of_total']:.1f}% |"
        )
    lines.append("")
    
    if analysis["recommendations"]:
        lines.append("### Recommendations")
        lines.append("")
        for i, rec in enumerate(analysis["recommendations"], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")
    
    lines.append("## Conclusion")
    lines.append("")
    if analysis["refactoring_needed"]:
        lines.append("**Action Required**: The current implementation requires optimization. "
                   "Please review the recommendations above and proceed with T031c to refactor "
                   "the codebase to reduce runtime below the 6-hour threshold.")
    else:
        lines.append("**Status**: The pipeline performance is within acceptable limits. "
                   "No immediate refactoring is required.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated from benchmark data analysis*")
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Optimization report written to {output_path}")

def main():
    """Main entry point for the optimization report generation."""
    # Define paths
    project_root = Path(__file__).parent.parent
    benchmark_path = project_root / "data" / "processed" / "benchmark_log.json"
    output_path = project_root / "data" / "processed" / "optimization_report.md"
    
    logger.info("Starting benchmark analysis...")
    
    # Load benchmark data
    benchmark_data = load_benchmark_data(str(benchmark_path))
    if not benchmark_data:
        logger.error("Failed to load benchmark data. Aborting.")
        return 1
    
    # Analyze bottlenecks
    analysis = analyze_bottlenecks(benchmark_data)
    
    # Generate report
    generate_markdown_report(analysis, str(output_path))
    
    logger.info("Analysis complete.")
    return 0

if __name__ == "__main__":
    exit(main())