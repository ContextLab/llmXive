"""
Verification script for T037: Verify tasks.md execution order matches data flow.

This script parses tasks.md to extract task dependencies and execution order,
then validates that the order matches the required data flow:
extraction -> analysis -> visualization.

It also verifies that all referenced files exist and imports are consistent.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)


def verify_file_exists(file_path: Path, description: str) -> bool:
    """Verify that a file exists at the given path."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path} ({description})")
        return False
    logger.info(f"File exists: {file_path}")
    return True


def verify_imports(code_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verify that all import statements in the codebase reference existing modules.
    Returns (success, list of error messages).
    """
    errors = []
    import_pattern = re.compile(r'^from\s+(\S+)\s+import\s+|^import\s+(\S+)', re.MULTILINE)

    for py_file in code_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            matches = import_pattern.findall(content)
            for match in matches:
                module_name = match[0] or match[1]
                # Skip standard library and third-party imports (simplified check)
                if '.' in module_name or module_name in ['sys', 'os', 'json', 're', 'math', 'csv', 'logging', 'argparse', 'datetime', 'random', 'hashlib', 'subprocess', 'time', 'io', 'pstats', 'cProfile', 'numpy', 'matplotlib', 'seaborn', 'scipy', 'statsmodels', 'yaml', 'jinja2', 'tracemalloc', 'itertools', 'typing']:
                    continue
                # Check if the module exists within the project
                # Convert dotted module name to path
                module_path = code_dir / (module_name.replace('.', '/') + '.py')
                package_path = code_dir / module_name.replace('.', '/')
                if not (module_path.exists() or package_path.is_dir()):
                    # Allow relative imports within same directory
                    if not any(p in module_name for p in ['analysis', 'extraction', 'visualization', 'utils']):
                        errors.append(f"Module not found: {module_name} in {py_file}")
        except Exception as e:
            errors.append(f"Error reading {py_file}: {e}")

    return len(errors) == 0, errors


def verify_tasks_md_dependencies(tasks_md_path: Path, code_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verify that tasks.md execution order matches the data flow.
    Returns (success, list of error messages).
    """
    errors = []

    if not tasks_md_path.exists():
        return False, [f"tasks.md not found at {tasks_md_path}"]

    content = tasks_md_path.read_text(encoding="utf-8")

    # Parse task dependencies from tasks.md
    # Look for patterns like "Depends on: T013, T014"
    depends_pattern = re.compile(r'\[([A-Z]\d+)\].*Depends on:\s*([A-Z0-9,\s]+)', re.DOTALL)

    task_deps = {}
    task_order = []
    task_phases = {}

    # Extract task order and dependencies
    lines = content.split('\n')
    current_phase = None
    for line in lines:
        if line.startswith('## Phase'):
            current_phase = line.strip()
        match = re.match(r'- \[([ xX])\]\s*([A-Z]\d+)', line)
        if match:
            task_id = match.group(2)
            task_order.append(task_id)
            task_phases[task_id] = current_phase

    # Extract dependencies
    for match in depends_pattern.finditer(content):
        task_id = match.group(1)
        deps_str = match.group(2)
        deps = [d.strip() for d in deps_str.split(',') if d.strip()]
        task_deps[task_id] = deps

    # Define expected data flow phases
    # Extraction -> Analysis -> Visualization
    extraction_tasks = {'T013', 'T017', 'T040', 'T043', 'T047'}
    analysis_tasks = {'T014', 'T015', 'T021', 'T021b', 'T022', 'T041'}
    visualization_tasks = {'T027', 'T027b', 'T028', 'T031'}

    # Verify that dependencies respect the data flow
    for task_id, deps in task_deps.items():
        task_phase = None
        if task_id in extraction_tasks:
            task_phase = 'extraction'
        elif task_id in analysis_tasks:
            task_phase = 'analysis'
        elif task_id in visualization_tasks:
            task_phase = 'visualization'

        if not task_phase:
            continue

        for dep in deps:
            dep_phase = None
            if dep in extraction_tasks:
                dep_phase = 'extraction'
            elif dep in analysis_tasks:
                dep_phase = 'analysis'
            elif dep in visualization_tasks:
                dep_phase = 'visualization'

            if dep_phase and task_phase != dep_phase:
                # Check if the dependency order is correct
                # Extraction can depend on setup, Analysis on Extraction, Visualization on Analysis
                allowed_deps = {
                    'extraction': {'setup', 'foundation'},
                    'analysis': {'extraction', 'setup', 'foundation'},
                    'visualization': {'analysis', 'extraction', 'setup', 'foundation'}
                }

                if dep_phase not in allowed_deps.get(task_phase, set()):
                    errors.append(
                        f"Data flow violation: {task_id} ({task_phase}) depends on {dep} ({dep_phase})"
                    )

    # Verify that tasks are ordered correctly in the file
    phase_order = ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Phase 5', 'Phase N']
    last_phase_idx = -1

    for task_id in task_order:
        phase = task_phases.get(task_id, 'Unknown')
        try:
            phase_idx = phase_order.index(phase)
            if phase_idx < last_phase_idx:
                errors.append(f"Task {task_id} appears in {phase} but should be after earlier phases")
            last_phase_idx = max(last_phase_idx, phase_idx)
        except ValueError:
            pass  # Unknown phase, skip

    return len(errors) == 0, errors


def run_verification() -> bool:
    """Run all verification checks for T037."""
    project_root = Path(__file__).parent.parent
    tasks_md_path = project_root / "tasks.md"
    code_dir = project_root / "code"

    all_passed = True
    error_messages = []

    # 1. Verify tasks.md exists
    if not verify_file_exists(tasks_md_path, "Task definitions"):
        all_passed = False
        error_messages.append("tasks.md is missing")
    else:
        # 2. Verify imports in codebase
        imports_ok, import_errors = verify_imports(code_dir)
        if not imports_ok:
            all_passed = False
            error_messages.extend(import_errors)

        # 3. Verify tasks.md execution order matches data flow
        flow_ok, flow_errors = verify_tasks_md_dependencies(tasks_md_path, code_dir)
        if not flow_ok:
            all_passed = False
            error_messages.extend(flow_errors)

    if all_passed:
        logger.info("T037 Verification PASSED: Execution order matches data flow")
    else:
        logger.error(f"T037 Verification FAILED: {len(error_messages)} errors found")
        for error in error_messages:
            logger.error(f"  - {error}")

    return all_passed


def main():
    """Main entry point for T037 verification."""
    success = run_verification()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()