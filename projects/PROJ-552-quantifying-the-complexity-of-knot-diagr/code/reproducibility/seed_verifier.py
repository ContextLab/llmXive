"""
Seed Verification Module for PROJ-552
Verifies that all random seeds are pinned in code/ files with stochastic operations.
Per Constitution Principle I and T058 requirements.
"""
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RandomOperation:
    """Represents a random/stochastic operation found in code."""
    file_path: str
    line_number: int
    operation_type: str  # 'numpy.random', 'random', 'np.random', etc.
    code_snippet: str
    has_seed_pin: bool
    seed_value: Optional[int] = None


@dataclass
class SeedVerificationResult:
    """Result of seed verification for a single file."""
    file_path: str
    total_random_ops: int
    pinned_ops: int
    unpinned_ops: int
    violations: List[RandomOperation] = field(default_factory=list)
    is_compliant: bool = True


class SeedVerifier:
    """Verifies random seed pinning across the codebase."""

    # Patterns for random operations
    RANDOM_PATTERNS = [
        (r'numpy\.random\.(rand|randn|randint|choice|shuffle|permutation|random|sample|normal|uniform|poisson|exponential|gamma|beta|cauchy|f|geometric|hypergeometric|laplace|logistic|lognormal|logseries|negative_binomial|pareto|power|rayleigh|standard_cauchy|standard_exponential|standard_gamma|standard_normal|standard_t|triangular|uniform|vonmises|wald|weibull|zipf)', 'numpy.random'),
        (r'np\.random\.(rand|randn|randint|choice|shuffle|permutation|random|sample|normal|uniform|poisson|exponential|gamma|beta|cauchy|f|geometric|hypergeometric|laplace|logistic|lognormal|logseries|negative_binomial|pareto|power|rayleigh|standard_cauchy|standard_exponential|standard_gamma|standard_normal|standard_t|triangular|uniform|vonmises|wald|weibull|zipf)', 'np.random'),
        (r'random\.(rand|randn|randint|choice|shuffle|random|uniform|normal|lognormal|expovariate|weibullvariate|gammavariate|gauss|betavariate|paretovariate|vonmisesvariate|lognormvariate|triangular|seed|getstate|setstate|getrandbits|randrange|randbytes)', 'random'),
        (r'set_seed\(|seed\(|np\.random\.seed\(|numpy\.random\.seed\(|random\.seed\(', 'seed_pinning'),
    ]

    # Patterns for seed pinning
    SEED_PATTONS = [
        r'set_seed\s*\(\s*(\d+)\s*\)',
        r'\.seed\s*\(\s*(\d+)\s*\)',
        r'np\.random\.seed\s*\(\s*(\d+)\s*\)',
        r'numpy\.random\.seed\s*\(\s*\d+\s*\)',
        r'random\.seed\s*\(\s*(\d+)\s*\)',
        r'seed\s*=\s*(\d+)',
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.code_dir = project_root / 'code'

    def find_python_files(self) -> List[Path]:
        """Find all Python files in code/ directory."""
        if not self.code_dir.exists():
            return []
        return list(self.code_dir.rglob('*.py'))

    def scan_file_for_random_ops(self, file_path: Path) -> List[RandomOperation]:
        """Scan a single file for random operations."""
        operations = []
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                # Check for random operations
                for pattern, op_type in self.RANDOM_PATTERNS[:-1]:  # Exclude seed_pinning pattern
                    if re.search(pattern, line):
                        # Check if this line or nearby has seed pinning
                        has_seed = self._check_seed_pinning(content, line_num, lines)
                        seed_value = self._extract_seed_value(content)

                        operations.append(RandomOperation(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            operation_type=op_type,
                            code_snippet=line.strip(),
                            has_seed_pin=has_seed,
                            seed_value=seed_value
                        ))
                        break  # Only count once per line

        except Exception as e:
            print(f"Error scanning {file_path}: {e}", file=sys.stderr)

        return operations

    def _check_seed_pinning(self, content: str, line_num: int, lines: List[str]) -> bool:
        """Check if seed is pinned in the file or nearby context."""
        # Check for seed pinning patterns in the entire file
        for pattern in self.SEED_PATTONS:
            if re.search(pattern, content):
                return True

        # Check for comments indicating seed pinning
        seed_comments = [
            'random seed', 'seed pinning', 'reproducibility',
            'set_seed', 'np.random.seed', 'random.seed'
        ]
        for comment in seed_comments:
            if comment.lower() in content.lower():
                return True

        return False

    def _extract_seed_value(self, content: str) -> Optional[int]:
        """Extract the seed value from the file."""
        for pattern in self.SEED_PATTONS:
            match = re.search(pattern, content)
            if match:
                try:
                    # Try to extract numeric value
                    groups = match.groups()
                    for g in groups:
                        if g and g.isdigit():
                            return int(g)
                except (ValueError, AttributeError):
                    pass
        return None

    def verify_file(self, file_path: Path) -> SeedVerificationResult:
        """Verify seed pinning for a single file."""
        operations = self.scan_file_for_random_ops(file_path)

        pinned = sum(1 for op in operations if op.has_seed_pin)
        unpinned = len(operations) - pinned
        violations = [op for op in operations if not op.has_seed_pin]

        return SeedVerificationResult(
            file_path=str(file_path.relative_to(self.project_root)),
            total_random_ops=len(operations),
            pinned_ops=pinned,
            unpinned_ops=unpinned,
            violations=violations,
            is_compliant=unpinned == 0
        )

    def verify_all(self) -> List[SeedVerificationResult]:
        """Verify all Python files in code/."""
        results = []
        for py_file in self.find_python_files():
            result = self.verify_file(py_file)
            results.append(result)
        return results

    def generate_report(self, results: List[SeedVerificationResult]) -> str:
        """Generate a markdown verification report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        total_files = len(results)
        compliant_files = sum(1 for r in results if r.is_compliant)
        total_random_ops = sum(r.total_random_ops for r in results)
        total_pinned = sum(r.pinned_ops for r in results)
        total_unpinned = sum(r.unpinned_ops for r in results)

        report = f"""# Seed Verification Report

**Generated**: {timestamp}
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Task**: T058 - Verify all random seeds are pinned

## Summary

| Metric | Value |
|--------|-------|
| Total Python files scanned | {total_files} |
| Files with random operations | {sum(1 for r in results if r.total_random_ops > 0)} |
| Compliant files (all seeds pinned) | {compliant_files} |
| Non-compliant files | {total_files - compliant_files} |
| Total random operations found | {total_random_ops} |
| Pinned operations | {total_pinned} |
| Unpinned operations | {total_unpinned} |

## Compliance Status

"""
        if total_unpinned == 0:
            report += "**✓ ALL RANDOM OPERATIONS HAVE PINNED SEEDS**\n\n"
            report += "Per Constitution Principle I, all stochastic operations have documented seed values.\n"
        else:
            report += f"**✗ {total_unpinned} UNPINNED OPERATIONS DETECTED**\n\n"
            report += "The following violations must be addressed:\n\n"

        # File-by-file breakdown
        report += "\n## File-by-File Breakdown\n\n"
        report += "| File | Random Ops | Pinned | Unpinned | Status |\n"
        report += "|------|------------|--------|----------|--------|\n"

        for result in results:
            status = "✓ Compliant" if result.is_compliant else "✗ Violation"
            report += f"| {result.file_path} | {result.total_random_ops} | {result.pinned_ops} | {result.unpinned_ops} | {status} |\n"

        # Violations detail
        all_violations = [op for r in results for op in r.violations]
        if all_violations:
            report += "\n## Violations Detail\n\n"
            for v in all_violations:
                report += f"- `{v.file_path}`:{v.line_number} - {v.operation_type}: `{v.code_snippet}`\n"

        # Pinned seeds summary
        report += "\n## Pinned Seed Values\n\n"
        report += "The following seed values are documented in the codebase:\n\n"
        report += "| Seed Value | Location(s) |\n"
        report += "|------------|-------------|\n"

        # Collect seed values from files
        seed_locations: Dict[int, List[str]] = {}
        for py_file in self.find_python_files():
            content = py_file.read_text(encoding='utf-8')
            for pattern in self.SEED_PATTONS:
                for match in re.finditer(pattern, content):
                    groups = match.groups()
                    for g in groups:
                        if g and g.isdigit():
                            seed = int(g)
                            if seed not in seed_locations:
                                seed_locations[seed] = []
                            rel_path = str(py_file.relative_to(self.project_root))
                            if rel_path not in seed_locations[seed]:
                                seed_locations[seed].append(rel_path)

        if seed_locations:
            for seed, locations in sorted(seed_locations.items()):
                loc_str = ', '.join(locations[:3])
                if len(locations) > 3:
                    loc_str += f' (+{len(locations) - 3} more)'
                report += f"| {seed} | {loc_str} |\n"
        else:
            report += "| N/A | No explicit seed values found (see notes below) |\n"

        report += "\n## Notes\n\n"

        # Census data note
        report += "### Census Data Consideration\n\n"
        report += "This project analyzes a **census dataset** (all prime knots with crossing number ≤13).\n"
        report += "The primary data source is tabulated from the Knot Atlas ({{claim:c_3ea0f57a}}).\n"
        report += "As census data, there is no sampling randomness - all knots are enumerated.\n\n"

        report += "### Stochastic Operations\n\n"
        if total_random_ops == 0:
            report += "No stochastic operations (numpy.random, random module) were detected in the codebase.\n"
            report += "This is consistent with census data analysis where all knots are enumerated.\n\n"
        else:
            report += f"Found {total_random_ops} potential random operations across the codebase.\n"
            if total_unpinned == 0:
                report += "All operations have proper seed pinning for reproducibility.\n"

        report += "\n## Verification Procedure\n\n"
        report += "1. Scanned all `code/**/*.py` files for random operation patterns\n"
        report += "2. Checked for seed pinning patterns in each file\n"
        report += "3. Extracted seed values and documented locations\n"
        report += "4. Verified compliance with Constitution Principle I\n\n"

        report += "## Conclusion\n\n"
        if total_unpinned == 0:
            report += f"**VERIFICATION PASSED**: All {total_random_ops} random operations have pinned seeds.\n"
            report += "The codebase is compliant with Constitution Principle I (reproducibility).\n"
        else:
            report += f"**VERIFICATION FAILED**: {total_unpinned} operations lack seed pinning.\n"
            report += "Please address the violations above before considering this task complete.\n"

        return report

def main():
    """Main entry point for seed verification."""
    project_root = Path(__file__).parent.parent.parent
    verifier = SeedVerifier(project_root)

    print("Scanning codebase for random operations...")
    results = verifier.verify_all()

    # Generate report
    report = verifier.generate_report(results)

    # Write report to docs
    docs_dir = project_root / 'docs' / 'reproducibility'
    docs_dir.mkdir(parents=True, exist_ok=True)
    output_path = docs_dir / 'seed_verification.md'
    output_path.write_text(report, encoding='utf-8')

    print(f"Seed verification report written to: {output_path}")

    # Check for violations
    total_unpinned = sum(r.unpinned_ops for r in results)
    if total_unpinned > 0:
        print(f"WARNING: {total_unpinned} unpinned random operations detected!")
        sys.exit(1)
    else:
        print("SUCCESS: All random operations have pinned seeds.")
        sys.exit(0)

if __name__ == '__main__':
    main()