import cProfile
import pstats
import io
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Import the main pipeline runner
try:
    from main import run_pipeline
except ImportError:
    # Fallback for testing if run from code directory directly
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from main import run_pipeline


def profile_pipeline_entrypoint():
    """
    Profiles the entire pipeline execution using cProfile.
    Returns the raw stats object and execution time.
    """
    profiler = cProfile.Profile()
    start_time = time.time()
    
    try:
        # Run the main pipeline logic
        # We wrap it to ensure it's captured in the profile
        profiler.enable()
        result = run_pipeline()
        profiler.disable()
    except Exception as e:
        profiler.disable()
        # Re-raise the error after profiling so the pipeline status is known
        # but we still capture the time up to the crash
        raise e
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return profiler, total_time


def save_profile_results(profiler: cProfile.Profile, total_time: float, output_path: Path):
    """
    Saves the profiling results to a markdown file.
    Analyzes bottlenecks and checks against the 15-minute threshold.
    """
    # Create string stream for stats
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Print top 20 functions
    
    stats_output = s.getvalue()
    
    # Determine pass/fail status
    threshold_seconds = 15 * 60  # 15 minutes
    status = "PASS" if total_time < threshold_seconds else "FAIL"
    time_minutes = total_time / 60.0
    
    report_lines = [
        "# Pipeline Runtime Profile Report",
        "",
        f"**Status**: {status}",
        f"**Total Runtime**: {total_time:.2f} seconds ({time_minutes:.2f} minutes)",
        f"**Threshold**: {threshold_seconds} seconds (15 minutes)",
        "",
        "## Top 20 Cumulative Time Functions",
        "",
        "```",
        stats_output,
        "```",
        "",
        "## Bottleneck Analysis",
        ""
    ]
    
    if status == "FAIL":
        report_lines.append("The pipeline exceeded the 15-minute limit. Consider optimizing the top cumulative functions listed above.")
    else:
        report_lines.append("The pipeline completed within the 15-minute limit.")
        
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
        
    print(f"Profile report saved to {output_path}")
    print(f"Total runtime: {total_time:.2f}s")


def run_profiler():
    """
    Main entry point for the profiler script.
    """
    parser = argparse.ArgumentParser(description="Profile the research pipeline runtime.")
    parser.add_argument('--output', type=str, default='data/logs/profile_report.md',
                        help='Path to save the profile report.')
    args = parser.parse_args()
    
    output_path = Path(args.output)
    
    try:
        profiler, total_time = profile_pipeline_entrypoint()
        save_profile_results(profiler, total_time, output_path)
        
        # Exit with code 1 if threshold exceeded, 0 otherwise
        if total_time >= 15 * 60:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Profiling failed with error: {e}")
        # Even if the pipeline crashes, we should try to save what we have
        # if the profiler captured any time
        sys.exit(2)


def main():
    run_profiler()


if __name__ == '__main__':
    main()
