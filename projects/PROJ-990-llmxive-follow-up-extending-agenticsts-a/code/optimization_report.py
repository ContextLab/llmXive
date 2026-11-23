import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('optimization_report')

def load_benchmark_data(benchmark_path: str) -> Dict[str, Any]:
    """
    Load benchmark data from the specified JSON file.
    
    Args:
        benchmark_path: Path to the benchmark_log.json file.
        
    Returns:
        Dictionary containing benchmark data.
        
    Raises:
        FileNotFoundError: If the benchmark file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = Path(benchmark_path)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {benchmark_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded benchmark data from {benchmark_path}")
    return data

def analyze_bottlenecks(benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze benchmark data to identify performance bottlenecks.
    
    Args:
        benchmark_data: Dictionary containing benchmark results.
        
    Returns:
        Dictionary containing analysis results.
    """
    analysis = {
        'total_runtime_ms': benchmark_data.get('total_runtime', 0),
        'phase_timings': benchmark_data.get('phase_timings', {}),
        'slowest_phase': None,
        'slowest_phase_time_ms': 0,
        'recommendations': []
    }
    
    phase_timings = analysis['phase_timings']
    if phase_timings:
        # Find the slowest phase
        slowest_phase = max(phase_timings, key=phase_timings.get)
        analysis['slowest_phase'] = slowest_phase
        analysis['slowest_phase_time_ms'] = phase_timings[slowest_phase]
        
        # Calculate percentage of total runtime
        total_time = sum(phase_timings.values())
        if total_time > 0:
            slowest_percentage = (analysis['slowest_phase_time_ms'] / total_time) * 100
            analysis['slowest_phase_percentage'] = round(slowest_percentage, 2)
            
            # Generate recommendations based on the slowest phase
            if slowest_phase == 'parser':
                analysis['recommendations'].append(
                    "Parser phase is the bottleneck. Consider implementing streaming/parsing in chunks "
                    "to reduce memory pressure and improve throughput."
                )
            elif slowest_phase == 'ablation':
                analysis['recommendations'].append(
                    "Ablation study is the bottleneck. Consider caching engine results or "
                    "parallelizing the ablation runs across multiple cores."
                )
            elif slowest_phase == 'simulation':
                analysis['recommendations'].append(
                    "Simulation phase is the bottleneck. Consider optimizing the engine runner "
                    "or batching trajectory processing."
                )
            elif slowest_phase == 'classifier':
                analysis['recommendations'].append(
                    "Classifier training is the bottleneck. The model is lightweight, so this "
                    "may indicate data loading overhead. Verify efficient data loading."
                )
            elif slowest_phase == 'stats':
                analysis['recommendations'].append(
                    "Statistical analysis is the bottleneck. Ensure vectorized operations are used "
                    "and avoid unnecessary loops in aggregation."
                )
            else:
                analysis['recommendations'].append(
                    f"Phase '{slowest_phase}' is the slowest. Review implementation for optimization opportunities."
                )
    
    return analysis

def generate_markdown_report(analysis: Dict[str, Any], output_path: str) -> None:
    """
    Generate a markdown report documenting the runtime analysis.
    
    Args:
        analysis: Dictionary containing analysis results.
        output_path: Path where the markdown report will be saved.
    """
    report_lines = [
        "# Optimization Report: Benchmark Analysis",
        "",
        "## Summary",
        "",
        f"- **Total Runtime**: {analysis['total_runtime_ms']} ms",
        f"- **Slowest Phase**: {analysis.get('slowest_phase', 'N/A')}",
    ]
    
    if 'slowest_phase_time_ms' in analysis:
        report_lines.append(f"- **Slowest Phase Duration**: {analysis['slowest_phase_time_ms']} ms")
    
    if 'slowest_phase_percentage' in analysis:
        report_lines.append(f"- **Percentage of Total Runtime**: {analysis['slowest_phase_percentage']}%")
    
    report_lines.extend([
        "",
        "## Phase Breakdown",
        "",
        "| Phase | Runtime (ms) |",
        "|-------|--------------|",
    ])
    
    phase_timings = analysis.get('phase_timings', {})
    for phase, time_ms in phase_timings.items():
        report_lines.append(f"| {phase} | {time_ms} |")
    
    report_lines.extend([
        "",
        "## Recommendations",
        "",
    ])
    
    recommendations = analysis.get('recommendations', [])
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
    else:
        report_lines.append("No specific recommendations. All phases completed within expected parameters.")
    
    report_lines.extend([
        "",
        "## Conclusion",
        "",
    ])
    
    total_runtime = analysis['total_runtime_ms']
    if total_runtime > 6 * 3600 * 1000:  # 6 hours in ms
        report_lines.append(
            "⚠️ **WARNING**: Total runtime exceeds 6 hours. Refactoring is **REQUIRED** "
            "to meet performance constraints. Focus on the slowest phase identified above."
        )
    elif total_runtime > 3 * 3600 * 1000:  # 3 hours in ms
        report_lines.append(
            "⚠️ **CAUTION**: Total runtime exceeds 3 hours. Consider optimization, "
            "but the pipeline may still be acceptable depending on resource constraints."
        )
    else:
        report_lines.append(
            "✅ **STATUS**: Total runtime is within acceptable limits (< 3 hours). "
            "Refactoring is **NOT REQUIRED** at this time."
        )
    
    report_lines.extend([
        "",
        "### Refactoring Decision",
        "",
    ])
    
    if total_runtime > 6 * 3600 * 1000:
        report_lines.append("Decision: **REFACTOR REQUIRED**")
    else:
        report_lines.append("Decision: **NO REFACTORING NEEDED**")
    
    # Write the report
    report_content = '\n'.join(report_lines)
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Optimization report generated at {output_path}")

def main():
    """
    Main entry point for the optimization report generation.
    """
    # Define paths
    project_root = Path(__file__).parent.parent
    benchmark_path = project_root / 'data' / 'processed' / 'benchmark_log.json'
    output_path = project_root / 'data' / 'processed' / 'optimization_report.md'
    
    try:
        # Load benchmark data
        logger.info("Starting optimization analysis...")
        benchmark_data = load_benchmark_data(str(benchmark_path))
        
        # Analyze bottlenecks
        analysis = analyze_bottlenecks(benchmark_data)
        
        # Generate report
        generate_markdown_report(analysis, str(output_path))
        
        logger.info("Optimization analysis completed successfully.")
        
        # Print summary to console
        print(f"\nOptimization Report Generated: {output_path}")
        print(f"Total Runtime: {analysis['total_runtime_ms']} ms")
        if analysis.get('slowest_phase'):
            print(f"Slowest Phase: {analysis['slowest_phase']} ({analysis['slowest_phase_time_ms']} ms)")
        
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        print("Ensure that code/benchmark.py has been run successfully to generate benchmark_log.json")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in benchmark file: {e}")
        print(f"Error: Invalid JSON in benchmark file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during optimization analysis: {e}")
        print(f"Error: Unexpected error during optimization analysis: {e}")
        raise

if __name__ == '__main__':
    main()
