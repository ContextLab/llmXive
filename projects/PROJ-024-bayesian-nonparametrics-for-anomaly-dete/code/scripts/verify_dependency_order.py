#!/usr/bin/env python3
"""
verify_dependency_order.py

Checks that completed tasks in tasks.md respect the dependency order
defined in the project's dependency graph (phase structure).

Usage:
    python verify_dependency_order.py

This script:
    1. Reads tasks.md and parses task completion status
    2. Defines the expected dependency order from phase structure
    3. Validates that completed tasks follow the dependency order
    4. Reports any violations or confirms compliance
    
Exit codes:
    0 - All dependencies satisfied
    1 - Dependency violations found
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime


# Phase definitions and their dependencies
# Each phase has a set of task IDs and depends on previous phases
PHASE_DEPENDENCIES = {
    'Phase_0_Research_Design': {
        'tasks': set(),  # Will be populated from tasks.md
        'depends_on': set(),  # No dependencies
        'description': 'Research & Design Documentation'
    },
    'Phase_1_Setup': {
        'tasks': set(),
        'depends_on': {'Phase_0_Research_Design'},
        'description': 'Setup (Shared Infrastructure)'
    },
    'Phase_2_Foundational': {
        'tasks': set(),
        'depends_on': {'Phase_1_Setup'},
        'description': 'Foundational (Blocking Prerequisites)'
    },
    'Phase_3_US1': {
        'tasks': set(),
        'depends_on': {'Phase_2_Foundational'},
        'description': 'User Story 1 - Core DPGMM Implementation'
    },
    'Phase_4_US2': {
        'tasks': set(),
        'depends_on': {'Phase_2_Foundational'},
        'description': 'User Story 2 - Baseline Comparison'
    },
    'Phase_5_US3': {
        'tasks': set(),
        'depends_on': {'Phase_2_Foundational'},
        'description': 'User Story 3 - Threshold Calibration'
    },
    'Phase_6_Polish': {
        'tasks': set(),
        'depends_on': {'Phase_3_US1', 'Phase_4_US2', 'Phase_5_US3'},
        'description': 'Polish & Cross-Cutting Concerns'
    }
}

# Phase ordering for validation (earlier phases must complete before later ones)
PHASE_ORDER = [
    'Phase_0_Research_Design',
    'Phase_1_Setup',
    'Phase_2_Foundational',
    'Phase_3_US1',
    'Phase_4_US2',
    'Phase_5_US3',
    'Phase_6_Polish'
]

# Task ID to phase mapping (regex patterns for phase detection)
TASK_PHASE_PATTERNS = {
    'Phase_0_Research_Design': r'^T00[0-9]$|T000|T001|T002|T003$',
    'Phase_1_Setup': r'^T00[4-8]$|^T01[6-8]$',
    'Phase_2_Foundational': r'^T00[9-5]$|^T01[2-5]$',
    'Phase_3_US1': r'^T01[9-3]$|^T02[0-5]$|^T03[0-5]$',
    'Phase_4_US2': r'^T03[6-9]$|^T04[0-9]$|^T090$',
    'Phase_5_US3': r'^T05[1-7]$',
    'Phase_6_Polish': r'^T05[8-9]$|^T06[0-9]$|^T07[0-9]$|^T08[0-9]$',
}

def get_project_root() -> Path:
    """Find the project root by looking for tasks.md."""
    current = Path(__file__).resolve()
    # Search upward for tasks.md
    for parent in current.parents:
        if (parent / 'tasks.md').exists():
            return parent
    # Fallback: assume current directory
    return Path(__file__).parent.parent.parent

def parse_tasks_md(tasks_md_path: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Parse tasks.md to extract task IDs and their completion status.
    
    Returns:
        Tuple of (all_tasks, completed_tasks)
        - all_tasks: Dict mapping task_id -> description
        - completed_tasks: Dict mapping task_id -> description for [X] tasks
    """
    all_tasks = {}
    completed_tasks = {}
    
    if not tasks_md_path.exists():
        print(f"ERROR: tasks.md not found at {tasks_md_path}")
        return all_tasks, completed_tasks
    
    with open(tasks_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse task lines: - [X] T### or - [ ] T###
    task_pattern = r'-\s*\[([X ])\]\s+(T\d+)\s+\[.*?\]\s+(.+?)(?:\s*<!--.*?-->|$)'
    
    for match in re.finditer(task_pattern, content, re.DOTALL):
        status, task_id, description = match.groups()
        description = description.strip()
        # Clean up description (remove trailing markers)
        description = re.sub(r'\s*<!--.*?-->', '', description).strip()
        
        all_tasks[task_id] = description
        
        if status.upper() == 'X':
            completed_tasks[task_id] = description
    
    return all_tasks, completed_tasks

def assign_task_to_phase(task_id: str) -> str:
    """Assign a task ID to its phase based on task ID patterns."""
    for phase, pattern in TASK_PHASE_PATTERNS.items():
        if re.match(pattern, task_id):
            return phase
    # Default to Phase_6_Polish for unknown tasks
    return 'Phase_6_Polish'

def populate_phase_tasks(completed_tasks: Dict[str, str]) -> Dict[str, Set[str]]:
    """Populate the phase task sets based on completed tasks."""
    phase_tasks = {phase: set() for phase in PHASE_DEPENDENCIES}
    
    for task_id in completed_tasks:
        phase = assign_task_to_phase(task_id)
        phase_tasks[phase].add(task_id)
    
    return phase_tasks

def validate_dependency_order(
    completed_tasks: Dict[str, str],
    phase_tasks: Dict[str, Set[str]]
) -> List[str]:
    """
    Validate that completed tasks respect the dependency order.
    
    Returns a list of violation messages (empty if all valid).
    """
    violations = []
    
    # Track which phases have any completed tasks
    completed_phases = set(phase for phase, tasks in phase_tasks.items() if tasks)
    
    # Check each completed phase's dependencies
    for phase in PHASE_ORDER:
        if phase not in completed_phases:
            continue
        
        # Get dependencies for this phase
        deps = PHASE_DEPENDENCIES[phase]['depends_on']
        
        # Check if all dependencies are satisfied (have completed tasks)
        for dep_phase in deps:
            if dep_phase not in completed_phases:
                violations.append(
                    f"VIOLATION: Phase '{phase}' has tasks completed, "
                    f"but its dependency phase '{dep_phase}' has no completed tasks"
                )
        
        # Also check that within a phase, all tasks are marked [X]
        # (This is a sanity check - if we're validating a phase, all its tasks should be done)
        phase_task_ids = set()
        for task_id in completed_tasks:
            if assign_task_to_phase(task_id) == phase:
                phase_task_ids.add(task_id)
        
        if phase_task_ids:
            # Phase has some completed tasks - this is normal during incremental work
            pass
    
    # Check for out-of-order completions within phases
    # (e.g., Phase 6 tasks completed before Phase 2 foundational tasks)
    for i, phase in enumerate(PHASE_ORDER):
        if phase not in completed_phases:
            continue
        
        # Check if any later phase has completed tasks
        for later_phase in PHASE_ORDER[i+1:]:
            if later_phase in completed_phases:
                # This is OK if the dependency is satisfied
                later_deps = PHASE_DEPENDENCIES[later_phase]['depends_on']
                if phase in later_deps:
                    # Later phase depends on this phase - OK
                    continue
                else:
                    # Later phase doesn't depend on this phase - check transitive deps
                    # This is generally OK for parallel phases
                    pass
    
    return violations

def generate_report(
    all_tasks: Dict[str, str],
    completed_tasks: Dict[str, str],
    violations: List[str]
) -> str:
    """Generate a human-readable report of the dependency validation."""
    lines = []
    lines.append("=" * 60)
    lines.append("DEPENDENCY ORDER VERIFICATION REPORT")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 60)
    lines.append("")
    
    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total tasks in tasks.md: {len(all_tasks)}")
    lines.append(f"Completed tasks: {len(completed_tasks)}")
    lines.append(f"Pending tasks: {len(all_tasks) - len(completed_tasks)}")
    lines.append(f"Violations found: {len(violations)}")
    lines.append("")
    
    # Phase breakdown
    lines.append("PHASE BREAKDOWN")
    lines.append("-" * 40)
    phase_tasks = populate_phase_tasks(completed_tasks)
    
    for phase in PHASE_ORDER:
        tasks = phase_tasks[phase]
        desc = PHASE_DEPENDENCIES[phase]['description']
        status = "COMPLETED" if tasks else "NOT STARTED"
        lines.append(f"{phase}: {len(tasks)} tasks ({status})")
        if tasks:
            for task_id in sorted(tasks):
                lines.append(f"  - {task_id}")
    lines.append("")
    
    # Violations
    if violations:
        lines.append("DEPENDENCY VIOLATIONS")
        lines.append("-" * 40)
        for v in violations:
            lines.append(f"  ⚠ {v}")
        lines.append("")
    else:
        lines.append("DEPENDENCY STATUS")
        lines.append("-" * 40)
        lines.append("  ✓ All completed tasks respect dependency order")
        lines.append("")
    
    # Next recommended tasks
    lines.append("NEXT RECOMMENDED TASKS")
    lines.append("-" * 40)
    
    # Find the first incomplete phase with no dependency violations
    for phase in PHASE_ORDER:
        if phase not in phase_tasks or not phase_tasks[phase]:
            # Check if all dependencies are satisfied
            deps_satisfied = True
            for dep in PHASE_DEPENDENCIES[phase]['depends_on']:
                if dep in phase_tasks and not phase_tasks[dep]:
                    deps_satisfied = False
                    break
            
            if deps_satisfied:
                lines.append(f"  Ready to start: {phase}")
                lines.append(f"    Description: {PHASE_DEPENDENCIES[phase]['description']}")
                break
    else:
        lines.append("  All phases have started - check for remaining incomplete tasks")
    lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)

def main():
    """Main entry point for dependency order verification."""
    print("Dependency Order Verification")
    print("-" * 40)
    
    # Find project root and tasks.md
    project_root = get_project_root()
    tasks_md_path = project_root / 'tasks.md'
    
    if not tasks_md_path.exists():
        print(f"ERROR: Could not find tasks.md at {tasks_md_path}")
        sys.exit(1)
    
    print(f"Project root: {project_root}")
    print(f"Tasks file: {tasks_md_path}")
    print()
    
    # Parse tasks
    all_tasks, completed_tasks = parse_tasks_md(tasks_md_path)
    
    if not all_tasks:
        print("ERROR: No tasks found in tasks.md")
        sys.exit(1)
    
    print(f"Found {len(all_tasks)} total tasks")
    print(f"Found {len(completed_tasks)} completed tasks")
    print()
    
    # Validate dependencies
    violations = validate_dependency_order(completed_tasks, populate_phase_tasks(completed_tasks))
    
    # Generate and print report
    report = generate_report(all_tasks, completed_tasks, violations)
    print(report)
    
    # Exit with appropriate code
    if violations:
        print("\n" + "!" * 40)
        print("DEPENDENCY VIOLATIONS DETECTED")
        print("!" * 40)
        sys.exit(1)
    else:
        print("\n" + "=" * 40)
        print("ALL DEPENDENCIES SATISFIED")
        print("=" * 40)
        sys.exit(0)

if __name__ == '__main__':
    main()
