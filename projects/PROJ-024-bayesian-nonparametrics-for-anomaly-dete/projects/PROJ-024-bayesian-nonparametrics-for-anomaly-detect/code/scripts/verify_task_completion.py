"""
Final Acceptance Verification Script (T145)

Verifies all [X] marked tasks in tasks.md have no FAILED-IN-EXECUTION comments.
Per spec.md Status Tracking Mechanism - this task blocks stage advancement.

Usage:
    python verify_task_completion.py
    
Output:
    Prints verification status for each completed task.
    Returns exit code 0 if all tasks pass, 1 if any task has FAILED-IN-EXECUTION.
"""

import re
import sys
from pathlib import Path


def find_tasks_md() -> Path:
    """Locate tasks.md in the project hierarchy."""
    # Check common locations
    possible_paths = [
        Path("tasks.md"),
        Path("projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect/tasks.md"),
        Path("../tasks.md"),
        Path("../../tasks.md"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path.resolve()
    
    raise FileNotFoundError("tasks.md not found in expected locations")


def parse_tasks(content: str) -> list[dict]:
    """
    Parse tasks.md and extract task information.
    
    Returns list of dicts with:
        - task_id: T###
        - status: [X] or [ ]
        - has_failed_execution: bool
        - line_content: full line text
    """
    tasks = []
    task_pattern = re.compile(r'^\s*-?\s*\[([X ])\]\s*(T\d+)\s+')
    
    for line in content.splitlines():
        match = task_pattern.match(line)
        if match:
            status = match.group(1)
            task_id = match.group(2)
            is_completed = status.upper() == 'X'
            
            # Check for FAILED-IN-EXECUTION in the line
            has_failed = 'FAILED-IN-EXECUTION' in line.upper()
            
            tasks.append({
                'task_id': task_id,
                'status': status,
                'is_completed': is_completed,
                'has_failed_execution': has_failed,
                'line_content': line.strip()
            })
    
    return tasks


def verify_completion(tasks: list[dict]) -> tuple[bool, list[str]]:
    """
    Verify all completed tasks have no FAILED-IN-EXECUTION comments.
    
    Returns:
        (all_passed, failure_messages)
    """
    failures = []
    
    for task in tasks:
        if task['is_completed'] and task['has_failed_execution']:
            failures.append(
                f"❌ {task['task_id']} is marked [X] but has FAILED-IN-EXECUTION: "
                f"{task['line_content'][:100]}..."
            )
    
    return len(failures) == 0, failures


def main():
    """Main entry point for verification."""
    print("=" * 70)
    print("T145 - Final Acceptance Verification Task")
    print("=" * 70)
    print()
    
    # Locate tasks.md
    try:
        tasks_path = find_tasks_md()
        print(f"Found tasks.md at: {tasks_path}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Read and parse tasks
    try:
        content = tasks_path.read_text(encoding='utf-8')
        tasks = parse_tasks(content)
    except Exception as e:
        print(f"ERROR reading tasks.md: {e}")
        sys.exit(1)
    
    # Summary statistics
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t['is_completed'])
    pending_tasks = total_tasks - completed_tasks
    
    print(f"Total tasks found: {total_tasks}")
    print(f"Completed tasks [X]: {completed_tasks}")
    print(f"Pending tasks [ ]: {pending_tasks}")
    print()
    
    # Verification
    all_passed, failures = verify_completion(tasks)
    
    if failures:
        print("=" * 70)
        print("❌ VERIFICATION FAILED - Tasks with FAILED-IN-EXECUTION:")
        print("=" * 70)
        for failure in failures:
            print(failure)
            print()
        
        print("=" * 70)
        print(f"SUMMARY: {len(failures)} completed task(s) have FAILED-IN-EXECUTION")
        print("This project CANNOT advance to 'analyzed' stage until fixed.")
        print("=" * 70)
        sys.exit(1)
    else:
        print("=" * 70)
        print("✅ VERIFICATION PASSED")
        print("=" * 70)
        print()
        print("All completed tasks [X] have no FAILED-IN-EXECUTION comments.")
        print("Project can advance to 'analyzed' stage.")
        print()
        
        # List completed tasks for reference
        print("Completed tasks verified:")
        for task in tasks:
            if task['is_completed']:
                print(f"  ✓ {task['task_id']}")
        
        print()
        print(f"Total verified: {completed_tasks} tasks")
        print("=" * 70)
        sys.exit(0)


if __name__ == '__main__':
    main()
