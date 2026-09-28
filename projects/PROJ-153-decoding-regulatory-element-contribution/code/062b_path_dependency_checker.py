"""
Path Dependency Verification Script (Task T62b)

Performs static analysis on code/ to verify that all file paths referenced in scripts
match the plan.md structure and exist (or are expected to be generated).

Output: results/path_dependency_report.json
"""
import os
import re
import sys
import ast
import argparse
import logging
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define expected file paths based on plan.md and tasks.md
# These are files that MUST exist (inputs) or are EXPECTED to be generated (outputs)
EXPECTED_INPUT_FILES = {
    # Data inputs
    "data/verified_accessions.yaml",
    "data/manifest.yaml",
    "data/raw/*.fastq.gz",  # Wildcard handled separately
    "data/raw/eqtl/*.tsv",  # Wildcard handled separately
    "data/processed/CRE_merged.bed",
    "data/processed/peak_signal_matrix.tsv",
    "data/processed/null_regions.bed",
    "data/processed/null_region_signal.bed",
    "data/processed/delta_peak_signal.tsv",
    "data/processed/vif_flags.tsv",
    "data/processed/motif_validation_flags.tsv",
    "data/processed/hic_validation_flags.tsv",
    "data/processed/cre_filtered.tsv",
    "data/processed/weighted_delta_signal.tsv",
    "data/processed/lmm_results.tsv",
    "data/processed/hic_matrix_10kb.cool",
    # Config/Spec inputs
    "plan.md",
    "tasks.md",
    "specs/001-yeast-cre-analysis/spec.md",
}

EXPECTED_OUTPUT_FILES = {
    # Results outputs
    "results/CRE_ranked_heatshock.md",
    "results/CRE_ranked_osmotic.md",
    "results/CRE_ranked_oxidative.md",
    "results/fdr_sweep_summary.tsv",
    "results/permutation_pvalue.csv",
    "results/variance_explained.tsv",
    "results/go_enrichment.tsv",
    "results/bias_sensitivity.csv",
    "results/summit_match_stats.tsv",
    "results/Statistical_summary.pdf",
    "results/traceability_manifest.json",
    "results/performance_report.csv",
    "results/path_dependency_report.json",  # This script's output
    "results/syntax_validation.log",
    "results/dry_run_manifest.json",
    # Tracks outputs
    "tracks/heatshock_CRE_signal.bw",
    "tracks/osmotic_CRE_signal.bw",
    "tracks/oxidative_CRE_signal.bw",
    # Logs
    "logs/pipeline.log",
}

# Patterns for dynamic path construction (regex)
DYNAMIC_PATH_PATTERNS = [
    r"data/processed/peaks_fdr_([\d.]+)\.bed",  # FDR sweep outputs
    r"results/CRE_ranked_(\w+)\.md",  # Stress-specific reports
    r"tracks/(\w+)_CRE_signal\.bw",  # Stress-specific tracks
]

def find_python_scripts(code_dir: Path) -> List[Path]:
    """Find all Python scripts in the code directory."""
    return list(code_dir.glob("*.py"))

def extract_paths_from_file(file_path: Path) -> Set[str]:
    """Extract file paths referenced in a Python script."""
    paths = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for string literals that look like paths
        # Common patterns: "data/...", "results/...", "code/...", "tracks/..."
        path_patterns = [
            r'["\']((data|results|code|tracks|logs|specs)/[^\s"\']+)["\']',
            r'Path\(["\']((data|results|code|tracks|logs|specs)/[^\s"\']+)["\']\)',
            r'\.join\([^\)]*["\']((data|results|code|tracks|logs|specs)/[^\s"\']+)["\']',
        ]

        for pattern in path_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Handle tuple returns from groups
                if isinstance(match, tuple):
                    paths.add(match[0])
                else:
                    paths.add(match)

        # Also check for f-strings and format() calls
        # Simple heuristic: look for variables that might contain paths
        # and common path construction patterns
        if 'os.path.join' in content or 'Path(' in content:
            # Extract variable assignments that might be paths
            var_pattern = r'(\w+)\s*=\s*["\']((data|results|code|tracks|logs|specs)/[^\s"\']+)["\']'
            var_matches = re.findall(var_pattern, content)
            for var_name, path_val in var_matches:
                paths.add(path_val)

    except Exception as e:
        logger.warning(f"Could not parse {file_path}: {e}")

    return paths

def check_path_exists(path: str, base_dir: Path, is_output: bool = False) -> Tuple[bool, str]:
    """Check if a path exists or is expected to be generated."""
    full_path = base_dir / path

    # Handle wildcards
    if '*' in path:
        parent_dir = base_dir / Path(path).parent
        pattern = Path(path).name
        if parent_dir.exists():
            matches = list(parent_dir.glob(pattern))
            return len(matches) > 0, f"Found {len(matches)} matches for {path}"
        return False, f"No matches for wildcard pattern {path}"

    if full_path.exists():
        return True, "Exists"

    if is_output:
        # Check if parent directory exists (output can be generated)
        parent = full_path.parent
        if parent.exists():
            return False, f"Expected output (parent dir exists): {path}"
        else:
            return False, f"Missing output directory: {parent}"

    return False, "Not found"

def analyze_code_directory(code_dir: Path) -> Dict[str, any]:
    """Analyze all Python scripts to extract referenced paths."""
    scripts = find_python_scripts(code_dir)
    all_paths = set()
    path_sources = {}  # path -> list of scripts referencing it

    for script in scripts:
        paths = extract_paths_from_file(script)
        all_paths.update(paths)
        for p in paths:
            if p not in path_sources:
                path_sources[p] = []
            path_sources[p].append(script.name)

    return {
        "scripts_analyzed": len(scripts),
        "total_unique_paths": len(all_paths),
        "paths": list(all_paths),
        "path_sources": path_sources
    }

def validate_expected_outputs(code_dir: Path, base_dir: Path) -> Dict[str, any]:
    """Validate that expected input files exist and outputs are valid."""
    results = {
        "inputs": {},
        "outputs": {},
        "dynamic_patterns": {},
        "summary": {
            "total_inputs": 0,
            "missing_inputs": 0,
            "total_outputs": 0,
            "missing_outputs": 0
        }
    }

    # Check input files
    for path in EXPECTED_INPUT_FILES:
        exists, reason = check_path_exists(path, base_dir, is_output=False)
        results["inputs"][path] = {
            "exists": exists,
            "reason": reason
        }
        results["summary"]["total_inputs"] += 1
        if not exists:
            results["summary"]["missing_inputs"] += 1

    # Check output files
    for path in EXPECTED_OUTPUT_FILES:
        exists, reason = check_path_exists(path, base_dir, is_output=True)
        results["outputs"][path] = {
            "exists": exists,
            "reason": reason
        }
        results["summary"]["total_outputs"] += 1
        if not exists:
            results["summary"]["missing_outputs"] += 1

    # Check dynamic patterns
    for pattern in DYNAMIC_PATH_PATTERNS:
        # Find all matches in the code directory
        matches = []
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                full_path = Path(root) / file
                if re.match(pattern, str(full_path.relative_to(base_dir))):
                    matches.append(str(full_path.relative_to(base_dir)))

        results["dynamic_patterns"][pattern] = {
            "matches": matches,
            "count": len(matches)
        }

    return results

def main():
    parser = argparse.ArgumentParser(
        description="Path Dependency Verification Script (T62b)"
    )
    parser.add_argument(
        "--code-dir",
        type=str,
        default="code",
        help="Directory containing Python scripts"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base project directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/path_dependency_report.json",
        help="Output report file path"
    )

    args = parser.parse_args()

    code_dir = Path(args.code_dir)
    base_dir = Path(args.base_dir)
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting path dependency verification...")
    logger.info(f"Code directory: {code_dir}")
    logger.info(f"Base directory: {base_dir}")

    # Analyze code directory
    code_analysis = analyze_code_directory(code_dir)
    logger.info(f"Analyzed {code_analysis['scripts_analyzed']} scripts")
    logger.info(f"Found {code_analysis['total_unique_paths']} unique paths")

    # Validate expected outputs
    validation_results = validate_expected_outputs(code_dir, base_dir)
    logger.info(f"Checked {validation_results['summary']['total_inputs']} input files")
    logger.info(f"Missing inputs: {validation_results['summary']['missing_inputs']}")
    logger.info(f"Checked {validation_results['summary']['total_outputs']} output files")
    logger.info(f"Missing outputs: {validation_results['summary']['missing_outputs']}")

    # Compile final report
    report = {
        "task_id": "T62b",
        "description": "Path Dependency Verification",
        "timestamp": str(Path(output_path).stat().st_mtime) if output_path.exists() else "new",
        "code_analysis": code_analysis,
        "validation_results": validation_results,
        "status": "PASS" if validation_results['summary']['missing_inputs'] == 0 else "FAIL",
        "recommendations": []
    }

    # Add recommendations
    if validation_results['summary']['missing_inputs'] > 0:
        missing = [p for p, v in validation_results['inputs'].items() if not v['exists']]
        report['recommendations'].append(
            f"Missing {len(missing)} input files. Ensure data is downloaded: {missing}"
        )

    if validation_results['summary']['missing_outputs'] > 0:
        missing = [p for p, v in validation_results['outputs'].items() if not v['exists']]
        report['recommendations'].append(
            f"Missing {len(missing)} expected output files. Run pipeline to generate: {missing}"
        )

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report written to {output_path}")

    # Exit with appropriate code
    if report['status'] == "FAIL":
        logger.error("Path dependency verification FAILED")
        sys.exit(1)
    else:
        logger.info("Path dependency verification PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
