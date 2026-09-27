import os
import re
import sys
import ast
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Expected project structure based on plan.md and tasks.md
EXPECTED_DIRECTORIES = {
    'code',
    'data',
    'data/raw',
    'data/processed',
    'results',
    'tracks',
    'tests',
    'tests/unit',
    'tests/contract',
    'tests/integration',
    'specs',
    'logs'
}

# Expected output files from tasks.md
EXPECTED_OUTPUT_FILES = {
    # From T008/T03_annotate
    'data/processed/CRE_merged.bed',
    # From T007c
    'data/processed/peak_signal_matrix.tsv',
    # From T009a
    'data/processed/null_regions.bed',
    # From T009b
    'data/processed/null_region_signal.bed',
    # From T043
    'data/processed/delta_peak_signal.tsv',
    # From T04_filter_impl
    'data/processed/weights.tsv',
    'data/processed/cre_all_vif_filtered.tsv',
    'data/processed/motif_validation_flags.tsv',
    'data/processed/hic_validation_flags.tsv',
    'data/processed/vif_flags.tsv',
    # From T05_weights_impl
    'data/processed/weighted_delta_signal.tsv',
    # From T06_lmm_impl
    'data/processed/lmm_results.tsv',
    # From T018/T07_report_impl
    'results/CRE_ranked_heatshock.md',
    'results/CRE_ranked_osmotic.md',
    'results/CRE_ranked_oxidative.md',
    'results/Statistical_summary.pdf',
    'results/permutation_pvalue.csv',
    'results/bias_sensitivity.csv',
    'results/fdr_sweep_summary.tsv',
    'results/summit_match_stats.tsv',
    'results/traceability_manifest.json',
    'results/performance_report.csv',
    # From T08_visualize_impl
    'tracks/heatshock_CRE_signal.bw',
    'tracks/osmotic_CRE_signal.bw',
    'tracks/oxidative_CRE_signal.bw',
    # From T05_validate_cre_gating_impl
    'data/processed/CRE_validated.bed',
    'data/processed/cre_validation_log.yaml',
    # From T007_sweep
    'results/cre_intersections.tsv',
    'results/fdr_overlap_stats.csv',
    # From T005/T01_download
    'data/extracted_accessions.yaml',
    'data/validation_log.yaml',
    'data/verified_accessions.yaml',
    'manifest.yaml',
    # From T045
    'data/raw/eqtl_dataset.parquet',  # or similar
    # Logs
    'logs/pipeline.log',
}

# Patterns to detect file path references in code
PATH_PATTERNS = [
    # Direct string literals with paths
    r'["\']([^"\']*\/[^"\']+)["\']',
    # f-strings with path components
    r'f["\']([^"\']*)["\']',
    # Path construction with os.path.join
    r'os\.path\.join\s*\(\s*["\']([^"\']+)["\']',
    # Path construction with Path
    r'Path\s*\(\s*["\']([^"\']+)["\']',
    # Input/output file arguments in argparse
    r'--output\s+["\']([^"\']+)["\']',
    r'--input\s+["\']([^"\']+)["\']',
]

def extract_paths_from_file(file_path: Path) -> List[str]:
    """Extract all file path references from a Python or R script."""
    paths = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # For Python files, use AST for more accurate extraction
        if file_path.suffix == '.py':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        val = node.value
                        if '/' in val and ('.tsv' in val or '.bed' in val or '.csv' in val or '.yaml' in val or '.json' in val or '.bw' in val or '.pdf' in val or '.md' in val):
                            paths.append(val)
                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == 'Path':
                            for arg in node.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    paths.append(arg.value)
                        elif isinstance(node.func, ast.Attribute) and node.func.attr == 'join':
                            for arg in node.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    paths.append(arg.value)
            except SyntaxError:
                logger.warning(f"Syntax error in {file_path}, falling back to regex")
        
        # Fallback to regex for all files
        for pattern in PATH_PATTERNS:
            matches = re.findall(pattern, content)
            paths.extend(matches)
        
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    
    return paths

def check_path_exists(path: str, base_dir: Path) -> Tuple[bool, str]:
    """Check if a path exists or is expected to be generated."""
    full_path = base_dir / path
    
    if full_path.exists():
        return True, "exists"
    
    # Check if it's in the expected outputs list
    if path in EXPECTED_OUTPUT_FILES:
        return False, "expected_output"
    
    # Check if parent directory exists (might be generated later)
    if full_path.parent.exists():
        return False, "parent_exists"
    
    return False, "missing"

def analyze_code_directory(code_dir: Path) -> Dict:
    """Analyze all scripts in the code directory for path references."""
    results = {
        'total_files': 0,
        'files_with_paths': 0,
        'path_references': {},
        'issues': []
    }
    
    for py_file in code_dir.glob('*.py'):
        results['total_files'] += 1
        paths = extract_paths_from_file(py_file)
        
        if paths:
            results['files_with_paths'] += 1
            results['path_references'][str(py_file.relative_to(code_dir))] = list(set(paths))
            
            # Validate each path
            for path in set(paths):
                exists, status = check_path_exists(path, code_dir.parent)
                if not exists and status != "expected_output":
                    results['issues'].append({
                        'file': str(py_file.relative_to(code_dir)),
                        'path': path,
                        'status': status
                    })
    
    return results

def validate_expected_outputs(project_root: Path) -> Dict:
    """Validate that all expected output files are accounted for."""
    validation = {
        'total_expected': len(EXPECTED_OUTPUT_FILES),
        'found': [],
        'missing': [],
        'details': {}
    }
    
    for expected_path in EXPECTED_OUTPUT_FILES:
        full_path = project_root / expected_path
        if full_path.exists():
            validation['found'].append(expected_path)
            validation['details'][expected_path] = 'exists'
        else:
            # Check if it's a generated file (not yet produced)
            parent = full_path.parent
            if parent.exists():
                validation['missing'].append(expected_path)
                validation['details'][expected_path] = 'not_yet_generated'
            else:
                validation['missing'].append(expected_path)
                validation['details'][expected_path] = 'parent_missing'
    
    return validation

def main():
    parser = argparse.ArgumentParser(
        description='Verify file path dependencies in code/ against plan.md structure'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path('.'),
        help='Path to project root directory'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Output report file (JSON)'
    )
    
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    code_dir = project_root / 'code'
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)
    
    logger.info(f"Analyzing code directory: {code_dir}")
    
    # Analyze code files
    code_analysis = analyze_code_directory(code_dir)
    
    # Validate expected outputs
    output_validation = validate_expected_outputs(project_root)
    
    # Compile report
    report = {
        'status': 'pass' if not code_analysis['issues'] else 'fail',
        'code_analysis': code_analysis,
        'output_validation': output_validation,
        'summary': {
            'total_scripts': code_analysis['total_files'],
            'scripts_with_paths': code_analysis['files_with_paths'],
            'total_path_references': sum(len(v) for v in code_analysis['path_references'].values()),
            'total_expected_outputs': output_validation['total_expected'],
            'outputs_found': len(output_validation['found']),
            'outputs_missing': len(output_validation['missing']),
            'path_issues': len(code_analysis['issues'])
        }
    }
    
    # Print summary
    print("\n" + "="*60)
    print("PATH DEPENDENCY VERIFICATION REPORT")
    print("="*60)
    print(f"Status: {report['status'].upper()}")
    print(f"Total scripts analyzed: {report['summary']['total_scripts']}")
    print(f"Scripts with path references: {report['summary']['scripts_with_paths']}")
    print(f"Total path references found: {report['summary']['total_path_references']}")
    print(f"Expected outputs: {report['summary']['total_expected_outputs']}")
    print(f"Outputs found: {report['summary']['outputs_found']}")
    print(f"Outputs missing (not yet generated): {report['summary']['outputs_missing']}")
    print(f"Path issues detected: {report['summary']['path_issues']}")
    print("="*60)
    
    if code_analysis['issues']:
        print("\nPATH ISSUES DETECTED:")
        for issue in code_analysis['issues']:
            print(f"  - {issue['file']}: {issue['path']} ({issue['status']})")
    
    if output_validation['missing']:
        print("\nMISSING OUTPUTS (expected but not yet generated):")
        for path in output_validation['missing'][:10]:  # Show first 10
            print(f"  - {path} ({output_validation['details'][path]})")
        if len(output_validation['missing']) > 10:
            print(f"  ... and {len(output_validation['missing']) - 10} more")
    
    # Save report if requested
    if args.output:
        import json
        output_file = project_root / args.output
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to: {output_file}")
    
    # Exit with appropriate code
    if report['status'] == 'fail':
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()