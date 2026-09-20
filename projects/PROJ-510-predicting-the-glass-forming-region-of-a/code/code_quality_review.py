"""
Code Quality Final Review (T063)

Performs a static analysis and review of the project's Python codebase to ensure
adherence to best practices, documentation standards, and project coding conventions.
Generates a structured review report.
"""
import os
import sys
import ast
import logging
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/code_quality_review.log')
    ]
)
logger = logging.getLogger(__name__)

# Project constants
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
REPORT_PATH = PROJECT_ROOT / "data" / "logs" / "code_quality_review_report.json"
CHECKSUM_PATH = PROJECT_ROOT / "data" / "logs" / "code_quality_review_checksums.txt"

# Configuration
MIN_DOCSTRING_COVERAGE = 0.8
MAX_LINE_LENGTH = 100
MAX_FUNCTION_LENGTH = 50
MAX_CLASS_LENGTH = 100
REQUIRED_MODULES = [
    'ingestion.py', 'features.py', 'train.py', 'analyze.py', 'utils.py',
    'audit_data_source.py', 'check_sc002.py', 'check_sc003.py',
    'statistical_test.py', 'validate_schemas.py', 'generate_report.py',
    't024c_gate.py', 't029b_fallback.py', 't031_sensitivity_analysis.py'
]

class CodeQualityAnalyzer:
    """Analyzes Python code for quality metrics and best practices."""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}
        self.files_analyzed: List[str] = []

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file for quality issues."""
        issues = []
        metrics = {
            'lines_of_code': 0,
            'functions_count': 0,
            'classes_count': 0,
            'docstring_coverage': 0.0,
            'has_mandatory_imports': False,
            'has_main_guard': False,
            'has_logging': False,
            'max_line_length': 0
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                metrics['lines_of_code'] = len([l for l in lines if l.strip() and not l.strip().startswith('#')])

            tree = ast.parse(content)

            # Check for mandatory imports
            mandatory_imports = {'logging', 'os', 'sys'}
            found_imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        found_imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        found_imports.add(node.module.split('.')[0])

            metrics['has_mandatory_imports'] = mandatory_imports.issubset(found_imports)
            if not metrics['has_mandatory_imports']:
                missing = mandatory_imports - found_imports
                issues.append({
                    'type': 'MISSING_IMPORT',
                    'message': f"Missing mandatory imports: {missing}",
                    'severity': 'WARNING'
                })

            # Check for main guard
            metrics['has_main_guard'] = any(
                isinstance(node, ast.If) and
                isinstance(node.test, ast.Compare) and
                len(node.test.ops) == 1 and
                isinstance(node.test.ops[0], ast.Eq) and
                isinstance(node.test.comparators[0], ast.Constant) and
                node.test.comparators[0].value == '__main__'
                for node in ast.walk(tree)
            )
            if not metrics['has_main_guard']:
                issues.append({
                    'type': 'NO_MAIN_GUARD',
                    'message': "File lacks if __name__ == '__main__' guard",
                    'severity': 'INFO'
                })

            # Check for logging usage
            metrics['has_logging'] = 'logging' in found_imports or 'get_logger' in content
            if not metrics['has_logging']:
                issues.append({
                    'type': 'NO_LOGGING',
                    'message': "File does not appear to use logging",
                    'severity': 'INFO'
                })

            # Analyze functions and classes
            func_count = 0
            class_count = 0
            docstring_count = 0
            total_items = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_count += 1
                    total_items += 1
                    if ast.get_docstring(node):
                        docstring_count += 1
                    if len(node.body) > MAX_FUNCTION_LENGTH:
                        issues.append({
                            'type': 'LONG_FUNCTION',
                            'message': f"Function '{node.name}' exceeds {MAX_FUNCTION_LENGTH} lines",
                            'severity': 'WARNING',
                            'location': f"{file_path.name}:{node.lineno}"
                        })
                elif isinstance(node, ast.ClassDef):
                    class_count += 1
                    total_items += 1
                    if ast.get_docstring(node):
                        docstring_count += 1
                    if len(node.body) > MAX_CLASS_LENGTH:
                        issues.append({
                            'type': 'LONG_CLASS',
                            'message': f"Class '{node.name}' exceeds {MAX_CLASS_LENGTH} lines",
                            'severity': 'WARNING',
                            'location': f"{file_path.name}:{node.lineno}"
                        })

            metrics['functions_count'] = func_count
            metrics['classes_count'] = class_count
            metrics['docstring_coverage'] = (docstring_count / total_items) if total_items > 0 else 1.0

            if metrics['docstring_coverage'] < MIN_DOCSTRING_COVERAGE:
                issues.append({
                    'type': 'LOW_DOCSTRING_COVERAGE',
                    'message': f"Docstring coverage {metrics['docstring_coverage']:.1%} < {MIN_DOCSTRING_COVERAGE:.1%}",
                    'severity': 'WARNING'
                })

            # Check line lengths
            max_line_len = max((len(line) for line in lines), default=0)
            metrics['max_line_length'] = max_line_len
            if max_line_len > MAX_LINE_LENGTH:
                issues.append({
                    'type': 'LONG_LINE',
                    'message': f"Line length {max_line_len} exceeds {MAX_LINE_LENGTH}",
                    'severity': 'WARNING'
                })

            self.files_analyzed.append(str(file_path))

        except SyntaxError as e:
            issues.append({
                'type': 'SYNTAX_ERROR',
                'message': str(e),
                'severity': 'ERROR',
                'location': str(file_path)
            })
        except Exception as e:
            issues.append({
                'type': 'ANALYSIS_ERROR',
                'message': f"Failed to analyze: {str(e)}",
                'severity': 'ERROR',
                'location': str(file_path)
            })

        return {
            'file': str(file_path),
            'metrics': metrics,
            'issues': issues
        }

    def analyze_project(self) -> Dict[str, Any]:
        """Analyze the entire project codebase."""
        results = {
            'summary': {
                'total_files': 0,
                'files_with_issues': 0,
                'total_issues': 0,
                'critical_issues': 0,
                'warnings': 0,
                'info': 0
            },
            'files': [],
            'overall_metrics': {}
        }

        # Analyze code directory
        if CODE_DIR.exists():
            for py_file in CODE_DIR.glob('*.py'):
                if py_file.name.startswith('_'):
                    continue
                result = self.analyze_file(py_file)
                results['files'].append(result)
                results['summary']['total_files'] += 1

                if result['issues']:
                    results['summary']['files_with_issues'] += 1
                    results['summary']['total_issues'] += len(result['issues'])
                    for issue in result['issues']:
                        if issue['severity'] == 'ERROR':
                            results['summary']['critical_issues'] += 1
                        elif issue['severity'] == 'WARNING':
                            results['summary']['warnings'] += 1
                        else:
                            results['summary']['info'] += 1

        # Analyze tests directory
        if TESTS_DIR.exists():
            for py_file in TESTS_DIR.glob('test_*.py'):
                result = self.analyze_file(py_file)
                results['files'].append(result)
                results['summary']['total_files'] += 1

        # Calculate overall metrics
        if results['files']:
            all_metrics = [f['metrics'] for f in results['files'] if 'metrics' in f]
            if all_metrics:
                results['overall_metrics'] = {
                    'avg_docstring_coverage': sum(m['docstring_coverage'] for m in all_metrics) / len(all_metrics),
                    'total_functions': sum(m['functions_count'] for m in all_metrics),
                    'total_classes': sum(m['classes_count'] for m in all_metrics),
                    'avg_line_length': sum(m['max_line_length'] for m in all_metrics) / len(all_metrics)
                }

        return results

def generate_report(analyzer: CodeQualityAnalyzer, results: Dict[str, Any]) -> None:
    """Generate a detailed code quality report."""
    report = {
        'timestamp': str(Path(REPORT_PATH).parent.parent),
        'project': 'PROJ-510-predicting-the-glass-forming-region-of-a',
        'task': 'T063',
        'summary': results['summary'],
        'overall_metrics': results.get('overall_metrics', {}),
        'files_analyzed': analyzer.files_analyzed,
        'detailed_results': results['files'],
        'recommendations': []
    }

    # Generate recommendations
    if results['summary']['critical_issues'] > 0:
        report['recommendations'].append("Fix all syntax errors and critical issues before proceeding.")
    if results['summary']['warnings'] > 0:
        report['recommendations'].append("Review and address warnings, particularly long functions and low docstring coverage.")
    if results['overall_metrics'].get('avg_docstring_coverage', 0) < MIN_DOCSTRING_COVERAGE:
        report['recommendations'].append("Increase docstring coverage to at least 80% for all functions and classes.")

    # Ensure output directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Code quality report written to {REPORT_PATH}")

def main():
    """Main entry point for the code quality review."""
    logger.info("Starting Code Quality Final Review (T063)")

    analyzer = CodeQualityAnalyzer()
    results = analyzer.analyze_project()

    generate_report(analyzer, results)

    # Print summary
    summary = results['summary']
    logger.info(f"Analysis complete: {summary['total_files']} files analyzed")
    logger.info(f"Issues found: {summary['total_issues']} (Critical: {summary['critical_issues']}, Warnings: {summary['warnings']}, Info: {summary['info']})")

    if summary['critical_issues'] > 0:
        logger.warning("Critical issues detected. Review the report for details.")
        sys.exit(1)
    else:
        logger.info("Code quality review passed with no critical issues.")
        sys.exit(0)

if __name__ == '__main__':
    main()
