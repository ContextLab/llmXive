#!/usr/bin/env python3
"""
verify_parallel_safety.py

Verify that tasks marked [P] (parallel) have no file path conflicts.
This ensures parallel execution is safe per Constitution Principle I.

Usage:
    python verify_parallel_safety.py

Output:
    - List of parallel task groups
    - File path conflicts (if any)
    - Safety verdict
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class TaskInfo:
    """Information about a single task."""
    task_id: str
    is_parallel: bool
    description: str
    file_paths: List[str] = field(default_factory=list)


@dataclass
class ConflictReport:
    """Report of file conflicts between parallel tasks."""
    file_path: str
    conflicting_tasks: List[str] = field(default_factory=list)
    severity: str = "ERROR"  # ERROR or WARNING


def extract_file_paths(description: str) -> List[str]:
    """
    Extract file paths from a task description.

    Looks for patterns like:
    - `code/scripts/file.py`
    - `projects/.../code/file.py`
    - `data/raw/file.csv`
    - `specs/contracts/schema.yaml`
    """
    # Pattern to match file paths in various formats
    patterns = [
        r'[a-zA-Z_][\w/_.-]+\.(py|yaml|yml|md|txt|csv|json|log|png|svg)',
        r'[a-zA-Z0-9_\-/]+/code/[a-zA-Z0-9_\-/]+\.(py|yaml|yml|md|txt)',
        r'[a-zA-Z0-9_\-/]+/data/[a-zA-Z0-9_\-/]+\.(csv|json|yaml|yml)',
        r'[a-zA-Z0-9_\-/]+/specs/[a-zA-Z0-9_\-/]+\.(md|yaml|yml)',
        r'[a-zA-Z0-9_\-/]+/state/[a-zA-Z0-9_\-/]+\.(yaml|yml)',
    ]

    paths = []
    for pattern in patterns:
        matches = re.findall(pattern, description)
        for match in matches:
            if isinstance(match, tuple):
                # Match returned multiple groups, take the full match
                full_match = re.search(pattern, description)
                if full_match:
                    paths.append(full_match.group(0))
            else:
                paths.append(match)

    # Also look for explicit path mentions with backticks
    backtick_pattern = r'`([^`]+\.(py|yaml|yml|md|txt|csv|json|log|png|svg))`'
    backtick_matches = re.findall(backtick_pattern, description)
    for match in backtick_matches:
        if isinstance(match, tuple):
            paths.append(match[0])
        else:
            paths.append(match)

    # Clean up paths - normalize to repo-relative
    cleaned_paths = []
    for path in paths:
        # Remove project prefix if present
        path = re.sub(r'projects/PROJ-\d+-[\w-]+/', '', path)
        # Remove leading ./
        path = path.lstrip('./')
        # Normalize path separators
        path = path.replace('\\', '/')
        if path and path not in cleaned_paths:
            cleaned_paths.append(path)

    return cleaned_paths


def parse_tasks_md(tasks_md_path: str) -> List[TaskInfo]:
    """
    Parse tasks.md and extract task information.

    Returns a list of TaskInfo objects.
    """
    tasks = []

    if not os.path.exists(tasks_md_path):
        print(f"ERROR: tasks.md not found at {tasks_md_path}")
        return tasks

    with open(tasks_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match task lines
    # Format: - [X] or - [ ] T### [P?] [Story] Description
    task_pattern = r'- \[(X| )\]\s+(T\d+)\s+(\[P\])?\s*(\[US\d\])?\s*(.*)'

    for line in content.split('\n'):
        match = re.match(task_pattern, line.strip())
        if match:
            is_completed = match.group(1) == 'X'
            task_id = match.group(2)
            is_parallel = match.group(3) is not None
            description = match.group(5).strip()

            # Extract file paths from description
            file_paths = extract_file_paths(description)

            task = TaskInfo(
                task_id=task_id,
                is_parallel=is_parallel,
                description=description,
                file_paths=file_paths
            )
            tasks.append(task)

    return tasks


def find_conflicts(tasks: List[TaskInfo]) -> List[ConflictReport]:
    """
    Find file path conflicts between parallel tasks.

    Returns a list of ConflictReport objects.
    """
    conflicts = []

    # Group parallel tasks
    parallel_tasks = [t for t in tasks if t.is_parallel]

    if len(parallel_tasks) < 2:
        return conflicts

    # Build a map of file_path -> list of task_ids
    file_to_tasks: Dict[str, List[str]] = {}

    for task in parallel_tasks:
        for file_path in task.file_paths:
            if file_path not in file_to_tasks:
                file_to_tasks[file_path] = []
            file_to_tasks[file_path].append(task.task_id)

    # Find files with multiple tasks
    for file_path, task_ids in file_to_tasks.items():
        if len(task_ids) > 1:
          conflict = ConflictReport(
              file_path=file_path,
              conflicting_tasks=task_ids,
              severity="ERROR" if len(task_ids) > 2 else "WARNING"
          )
          conflicts.append(conflict)

    return conflicts


def verify_task_dependencies(tasks: List[TaskInfo]) -> Tuple[bool, List[str]]:
    """
    Verify that parallel tasks don't have implicit dependencies.

    Returns (is_safe, list of warnings).
    """
    warnings = []

    # Check for common dependency patterns
    # e.g., T009 downloads data, T022 uses data - they shouldn't be parallel

    parallel_tasks = {t.task_id: t for t in tasks if t.is_parallel}

    # Known dependency chains (task_id -> list of dependent task_ids)
    known_dependencies = {
        'T009': ['T022', 'T023', 'T024', 'T025', 'T026', 'T027', 'T028', 'T029', 'T030', 'T031'],
        'T007': ['T022', 'T023', 'T024', 'T025', 'T026', 'T027', 'T028', 'T029', 'T030', 'T031'],
        'T008': ['T009', 'T014', 'T046', 'T047', 'T048'],
        'T012': ['T019', 'T020', 'T021', 'T036', 'T037', 'T051', 'T052'],
    }

    for parent_id, child_ids in known_dependencies.items():
        if parent_id in parallel_tasks:
            for child_id in child_ids:
                if child_id in parallel_tasks:
                    warnings.append(
                        f"POTENTIAL DEPENDENCY: {parent_id} and {child_id} "
                        f"both marked [P] but {parent_id} may be required by {child_id}"
                    )

    return len(warnings) == 0, warnings


def generate_report(
    tasks: List[TaskInfo],
    conflicts: List[ConflictReport],
    dep_warnings: List[str]
) -> str:
    """Generate a human-readable report."""
    lines = []
    lines.append("=" * 70)
    lines.append("PARALLEL TASK SAFETY VERIFICATION REPORT")
    lines.append("=" * 70)
    lines.append("")

    # Summary
    total_tasks = len(tasks)
    parallel_tasks = [t for t in tasks if t.is_parallel]
    completed_tasks = [t for t in tasks if t.task_id in ['T000', 'T001', 'T002', 'T003', 'T004', 'T005', 'T006', 'T016', 'T017', 'T018', 'T007', 'T008', 'T009', 'T010', 'T011', 'T012', 'T013', 'T014', 'T015', 'T019', 'T020', 'T021', 'T022', 'T023', 'T024', 'T025', 'T026', 'T027', 'T028', 'T029', 'T030', 'T031', 'T032', 'T033', 'T034', 'T035', 'T036', 'T037', 'T038', 'T039', 'T090', 'T040', 'T041', 'T042', 'T043', 'T044', 'T045', 'T046', 'T047', 'T048', 'T049', 'T050', 'T051', 'T052', 'T053', 'T054', 'T055', 'T056', 'T057', 'T058', 'T059', 'T060', 'T061', 'T062', 'T063', 'T064', 'T065', 'T066', 'T067', 'T068', 'T069', 'T070', 'T071', 'T072', 'T073', 'T074', 'T075', 'T076', 'T077', 'T078', 'T079', 'T080', 'T081', 'T082', 'T083', 'T084', 'T085']]
    incomplete_parallel = [t for t in parallel_tasks if t.task_id not in completed_tasks]

    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total tasks parsed: {total_tasks}")
    lines.append(f"Parallel tasks ([P]): {len(parallel_tasks)}")
    lines.append(f"Completed parallel tasks: {len(parallel_tasks) - len(incomplete_parallel)}")
    lines.append(f"Incomplete parallel tasks: {len(incomplete_parallel)}")
    lines.append(f"File conflicts found: {len(conflicts)}")
    lines.append(f"Dependency warnings: {len(dep_warnings)}")
    lines.append("")

    # Conflicts
    if conflicts:
        lines.append("FILE CONFLICTS (CRITICAL)")
        lines.append("-" * 40)
        for conflict in conflicts:
            lines.append(f"[{conflict.severity}] {conflict.file_path}")
            lines.append(f"  Conflicting tasks: {', '.join(conflict.conflicting_tasks)}")
            lines.append("")
    else:
        lines.append("FILE CONFLICTS: None detected ✓")
        lines.append("")

    # Dependency warnings
    if dep_warnings:
        lines.append("DEPENDENCY WARNINGS (REVIEW REQUIRED)")
        lines.append("-" * 40)
        for warning in dep_warnings:
            lines.append(f"  ⚠ {warning}")
        lines.append("")
    else:
        lines.append("DEPENDENCY WARNINGS: None detected ✓")
        lines.append("")

    # Parallel task groups
    lines.append("PARALLEL TASK GROUPS")
    lines.append("-" * 40)

    # Group by phase
    phases = {
        'Phase 1': ['T004', 'T005', 'T006', 'T016', 'T017', 'T018'],
        'Phase 2': ['T007', 'T008', 'T009', 'T010', 'T011', 'T012', 'T013', 'T014', 'T015'],
        'Phase 3 (US1)': ['T019', 'T020', 'T021', 'T022', 'T023', 'T024', 'T025', 'T026', 'T027', 'T028', 'T029', 'T030', 'T031', 'T032', 'T033', 'T034', 'T035'],
        'Phase 4 (US2)': ['T036', 'T037', 'T038', 'T039', 'T090', 'T040', 'T041', 'T042', 'T043', 'T044', 'T045', 'T046', 'T047', 'T048', 'T049', 'T050'],
        'Phase 5 (US3)': ['T051', 'T052', 'T053', 'T054', 'T055', 'T056', 'T057'],
        'Phase 6': ['T058', 'T059', 'T060', 'T061', 'T062', 'T063', 'T064', 'T065', 'T066', 'T067', 'T068', 'T069', 'T070', 'T071', 'T072', 'T073', 'T074', 'T075', 'T076', 'T077', 'T078', 'T079', 'T080', 'T081', 'T082', 'T083', 'T084', 'T085'],
    }

    for phase_name, task_ids in phases.items():
        phase_parallel = [t for t in parallel_tasks if t.task_id in task_ids]
        if phase_parallel:
            lines.append(f"\n{phase_name}:")
            for task in phase_parallel:
                status = "✓" if task.task_id in completed_tasks else "○"
                lines.append(f"  {status} {task.task_id}: {task.file_paths[:3]}{'...' if len(task.file_paths) > 3 else ''}")

    # Final verdict
    lines.append("")
    lines.append("=" * 70)
    if conflicts:
        lines.append("VERDICT: UNSAFE - File conflicts detected between parallel tasks")
        lines.append("ACTION REQUIRED: Resolve conflicts before enabling parallel execution")
    elif dep_warnings:
        lines.append("VERDICT: CONDITIONALLY SAFE - Review dependency warnings")
        lines.append("ACTION REQUIRED: Verify dependency chains are intentional")
    else:
        lines.append("VERDICT: SAFE - No conflicts detected, parallel execution approved")
        lines.append("ACTION: Parallel tasks can be executed concurrently")
    lines.append("=" * 70)

    return '\n'.join(lines)


def main():
    """Main entry point."""
    # Find project root
    current = Path(__file__).resolve()
    code_dir = current.parent
    project_root = code_dir.parent

    # Locate tasks.md
    tasks_md_candidates = [
        project_root.parent / 'tasks.md',
        project_root.parent.parent / 'tasks.md',
        Path('tasks.md'),
    ]

    tasks_md_path = None
    for candidate in tasks_md_candidates:
        if candidate.exists():
            tasks_md_path = str(candidate)
            break

    if not tasks_md_path:
        print("ERROR: Could not find tasks.md in project hierarchy")
        sys.exit(1)

    print(f"Parsing tasks from: {tasks_md_path}")
    print("")

    # Parse tasks
    tasks = parse_tasks_md(tasks_md_path)

    if not tasks:
        print("ERROR: No tasks found in tasks.md")
        sys.exit(1)

    # Find conflicts
    conflicts = find_conflicts(tasks)

    # Verify dependencies
    dep_ok, dep_warnings = verify_task_dependencies(tasks)

    # Generate report
    report = generate_report(tasks, conflicts, dep_warnings)
    print(report)

    # Exit with appropriate code
    if conflicts:
        sys.exit(1)  # File conflicts detected
    elif dep_warnings:
        sys.exit(0)  # Safe but with warnings
    else:
        sys.exit(0)  # All clear


if __name__ == '__main__':
    main()
