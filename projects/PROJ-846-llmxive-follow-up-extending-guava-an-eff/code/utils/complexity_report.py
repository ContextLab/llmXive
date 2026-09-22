"""
Complexity Analysis Script for llmXive Project

This script uses the radon tool to identify high-complexity functions
in the logger.py module and generates a detailed report.

Usage:
    python code/utils/complexity_report.py
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports if running as script
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from radon.complexity import cc_visit
    from radon.raw import analyze as raw_analyze
except ImportError:
    print("Error: radon is not installed. Please install it with: pip install radon")
    sys.exit(1)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
LOGGER_FILE = PROJECT_ROOT / "utils" / "logger.py"
REPORT_OUTPUT = PROJECT_ROOT.parent / "data" / "artifacts" / "complexity_report.json"
COMPLEXITY_THRESHOLD = 10  # Functions with CC >= 10 are considered high complexity

def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single Python file for complexity metrics."""
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Cyclomatic Complexity Analysis
    results = cc_visit(source_code)
    
    # Raw Metrics Analysis
    raw_metrics = raw_analyze(source_code)

    high_complexity_functions = []
    
    for result in results:
        # Skip nested functions if desired, but include all for thoroughness
        if result.complexity >= COMPLEXITY_THRESHOLD:
            high_complexity_functions.append({
                "name": result.name,
                "filename": result.filename,
                "complexity": result.complexity,
                "start": result.lineno,
                "end": result.end,
                "signature": result.signature,
                "docstring": result.docstring
            })

    return {
        "file": str(file_path),
        "raw_metrics": {
            "loc": raw_metrics.loc,
            "blank": raw_metrics.blank,
            "code": raw_metrics.code,
            "comments": raw_metrics.comments,
            "multi": raw_metrics.multi,
            "single": raw_metrics.single
        },
        "total_functions": len(results),
        "high_complexity_count": len(high_complexity_functions),
        "high_complexity_functions": sorted(high_complexity_functions, key=lambda x: x["complexity"], reverse=True),
        "all_functions": [
            {
                "name": r.name,
                "complexity": r.complexity,
                "start": r.lineno,
                "end": r.end
            }
            for r in results
        ]
    }

def generate_report(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a structured report from the analysis result."""
    timestamp = os.popen("date -u +\"%Y-%m-%dT%H:%M:%SZ\"").read().strip()
    
    report = {
        "metadata": {
            "tool": "radon",
            "threshold": COMPLEXITY_THRESHOLD,
            "analyzed_file": analysis_result.get("file", "Unknown"),
            "timestamp": timestamp
        },
        "summary": {
            "total_lines_of_code": analysis_result.get("raw_metrics", {}).get("loc", 0),
            "total_functions": analysis_result.get("total_functions", 0),
            "high_complexity_functions": analysis_result.get("high_complexity_count", 0),
            "average_complexity": 0.0  # Will be calculated below
        },
        "recommendations": []
    }

    # Calculate average complexity
    if analysis_result.get("all_functions"):
        complexities = [f["complexity"] for f in analysis_result["all_functions"]]
        report["summary"]["average_complexity"] = sum(complexities) / len(complexities)

    # Generate recommendations
    if analysis_result.get("high_complexity_functions"):
        report["recommendations"].append(
            f"Found {len(analysis_result['high_complexity_functions'])} functions with complexity >= {COMPLEXITY_THRESHOLD}. "
            "These should be refactored to improve maintainability and testability."
        )
        
        for func in analysis_result["high_complexity_functions"]:
            report["recommendations"].append(
                f"- Refactor '{func['name']}' (CC: {func['complexity']}, Line {func['start']})"
            )
    else:
        report["recommendations"].append(
            f"All functions in {analysis_result.get('file', 'the file')} have complexity < {COMPLEXITY_THRESHOLD}. "
            "Good job maintaining low complexity!"
        )

    return report

def main():
    """Main entry point for the complexity analysis."""
    print(f"Analyzing complexity of: {LOGGER_FILE}")
    
    if not LOGGER_FILE.exists():
        print(f"Error: File not found: {LOGGER_FILE}")
        sys.exit(1)

    # Ensure output directory exists
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Perform analysis
    analysis_result = analyze_file(LOGGER_FILE)
    
    if "error" in analysis_result:
        print(f"Error during analysis: {analysis_result['error']}")
        sys.exit(1)

    # Generate report
    report = generate_report(analysis_result)

    # Write report to file
    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Print summary to console
    print("\n" + "="*60)
    print("COMPLEXITY ANALYSIS REPORT")
    print("="*60)
    print(f"File: {report['metadata']['analyzed_file']}")
    print(f"Total Lines of Code: {report['summary']['total_lines_of_code']}")
    print(f"Total Functions: {report['summary']['total_functions']}")
    print(f"Average Complexity: {report['summary']['average_complexity']:.2f}")
    print(f"High Complexity Functions (>= {COMPLEXITY_THRESHOLD}): {report['summary']['high_complexity_functions']}")
    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  {rec}")
    print("\nDetailed report saved to:", REPORT_OUTPUT)
    print("="*60)

    # Exit with error code if high complexity functions found
    if report["summary"]["high_complexity_functions"] > 0:
        sys.exit(1)  # Indicate that refactoring is needed
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()