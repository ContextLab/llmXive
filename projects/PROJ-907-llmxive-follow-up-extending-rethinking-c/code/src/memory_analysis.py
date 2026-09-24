import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/memory_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
GITHUB_ACTIONS_MEMORY_LIMIT_GB = 7.0
RESULTS_DIR = Path("data/results")
RAW_LOG_PATH = RESULTS_DIR / "memory_profile_raw.jsonl"
PROFILE_JSON_PATH = RESULTS_DIR / "memory_profile.json"
REPORT_MD_PATH = Path("docs/memory_report.md")

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB.
    Uses psutil if available, otherwise falls back to /proc/self/status on Linux.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)  # Convert to GB
    except ImportError:
        logger.warning("psutil not found, attempting /proc/self/status fallback")
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        rss_kb = int(line.split()[1])
                        return rss_kb / (1024 * 1024)  # Convert to GB
        except Exception as e:
            logger.error(f"Could not determine memory usage: {e}")
            return 0.0
    return 0.0

def parse_memory_log(log_path: Path) -> List[Dict[str, Any]]:
    """
    Parse the memory profile raw log file (JSONL format).
    Returns a list of log entries.
    """
    entries = []
    if not log_path.exists():
        logger.error(f"Memory log file not found: {log_path}")
        return entries

    with open(log_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON on line {line_num}: {e}")

    return entries

def compute_memory_statistics(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute statistics from the parsed memory log entries.
    Returns a dictionary with peak memory, average memory, and status.
    """
    if not entries:
        logger.warning("No memory log entries found. Generating empty report.")
        return {
            "peak_memory_gb": 0.0,
            "average_memory_gb": 0.0,
            "min_memory_gb": 0.0,
            "entry_count": 0,
            "had_oom_error": False,
            "within_limit": True, # Default to true if no data, but status will be FAIL
            "status": "FAIL",
            "limit_gb": GITHUB_ACTIONS_MEMORY_LIMIT_GB
        }

    memory_values = []
    has_oom = False

    for entry in entries:
        # Check for OOM/MemoryError events
        if entry.get("status") == "MemoryError" or "MemoryError" in str(entry.get("message", "")):
            has_oom = True
            continue

        # Extract memory usage if present
        mem_gb = entry.get("peak_memory_gb") or entry.get("memory_usage_gb")
        if mem_gb is not None:
            try:
                memory_values.append(float(mem_gb))
            except (ValueError, TypeError):
                continue

    if not memory_values:
        # If we only have errors or no data
        return {
            "peak_memory_gb": 0.0,
            "average_memory_gb": 0.0,
            "min_memory_gb": 0.0,
            "entry_count": len(entries),
            "had_oom_error": has_oom,
            "within_limit": False,
            "status": "FAIL",
            "limit_gb": GITHUB_ACTIONS_MEMORY_LIMIT_GB
        }

    peak = max(memory_values)
    avg = sum(memory_values) / len(memory_values)
    min_val = min(memory_values)

    within_limit = peak < GITHUB_ACTIONS_MEMORY_LIMIT_GB
    status = "PASS" if (within_limit and not has_oom) else "FAIL"

    return {
        "peak_memory_gb": round(peak, 4),
        "average_memory_gb": round(avg, 4),
        "min_memory_gb": round(min_val, 4),
        "entry_count": len(entries),
        "had_oom_error": has_oom,
        "within_limit": within_limit,
        "status": status,
        "limit_gb": GITHUB_ACTIONS_MEMORY_LIMIT_GB
    }

def generate_markdown_report(stats: Dict[str, Any], log_path: Path) -> str:
    """
    Generate a Markdown report summarizing memory usage.
    """
    report_lines = [
        "# Memory Analysis Report",
        "",
        f"**Generated:** {__import__('datetime').datetime.now().isoformat()}",
        f"**GitHub Actions Memory Limit:** {stats['limit_gb']} GB",
        "",
        "## Summary",
        "",
        f"- **Status:** {stats['status']}",
        f"- **Peak Memory Usage:** {stats['peak_memory_gb']:.4f} GB",
        f"- **Average Memory Usage:** {stats['average_memory_gb']:.4f} GB",
        f"- **Minimum Memory Usage:** {stats['min_memory_gb']:.4f} GB",
        f"- **Entries Processed:** {stats['entry_count']}",
        f"- **OOM Errors Detected:** {'Yes' if stats['had_oom_error'] else 'No'}",
        "",
        "## OOM Prevention Efficacy",
        "",
    ]

    if stats['status'] == "PASS":
        report_lines.append(
            f"The memory usage remained within the {stats['limit_gb']} GB limit. "
            "The `memory_guard` mechanism successfully prevented out-of-memory crashes."
        )
    else:
        if stats['had_oom_error']:
            report_lines.append(
                "A `MemoryError` was logged during execution. "
                "This indicates the memory limit was breached or the guard failed to trigger in time."
            )
        else:
            report_lines.append(
                f"Peak memory usage ({stats['peak_memory_gb']:.4f} GB) exceeded the limit of {stats['limit_gb']} GB."
            )

    report_lines.extend([
        "",
        "## Detailed Log Source",
        "",
        f"- Raw Log Path: `{log_path}`",
        "",
        "## Methodology",
        "",
        "Memory usage was tracked at key processing steps (e.g., per image in the trace set). "
        "The `memory_guard` function was invoked before processing each unit to ensure "
        f"RAM usage did not exceed {stats['limit_gb']} GB. This report aggregates the "
        "recorded values from `memory_profile_raw.jsonl`.",
        ""
    ])

    return "\n".join(report_lines)

def save_json_profile(stats: Dict[str, Any], output_path: Path) -> None:
    """
    Save the computed statistics to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Memory profile JSON saved to: {output_path}")

def run_memory_analysis() -> Dict[str, Any]:
    """
    Main entry point to run the full memory analysis pipeline.
    """
    logger.info("Starting memory analysis...")

    # Ensure output directories exist
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(parents=True, exist_ok=True)

    # Parse logs
    entries = parse_memory_log(RAW_LOG_PATH)

    # Compute stats
    stats = compute_memory_statistics(entries)

    # Save JSON profile
    save_json_profile(stats, PROFILE_JSON_PATH)

    # Generate and save Markdown report
    md_content = generate_markdown_report(stats, RAW_LOG_PATH)
    with open(REPORT_MD_PATH, 'w') as f:
        f.write(md_content)
    logger.info(f"Markdown report saved to: {REPORT_MD_PATH}")

    logger.info(f"Analysis complete. Status: {stats['status']}, Peak: {stats['peak_memory_gb']} GB")
    return stats

def main():
    """
    CLI entry point.
    """
    try:
        stats = run_memory_analysis()
        # Exit with error code if status is FAIL to facilitate CI checks
        if stats['status'] == "FAIL":
            logger.error("Memory analysis failed. Check logs for details.")
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error during memory analysis: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
