import pytest
import os
import tempfile
from pathlib import Path
from code.verify_consistency import ConsistencyChecker

@pytest.fixture
def temp_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create minimal tasks.md
        tasks_md = root / "tasks.md"
        tasks_md.write_text("""
        # Tasks

        - [X] T001 Create project structure
        - [ ] T002 [US1] Implement main logic in code/main.py
        - [ ] T003 [US1] Depends on T002
        - [ ] T004 [US2] Implement analysis in code/analysis.py
        """)

        # Create minimal spec.md
        specs_dir = root / "specs" / "001-network-topology-thermal"
        specs_dir.mkdir(parents=True)
        spec_md = specs_dir / "spec.md"
        spec_md.write_text("""
        ## US1: Main Logic
        FR-001: Implement main logic.

        ## US2: Analysis
        FR-002: Implement analysis.
        """)

        yield root

def test_consistency_check_passes(temp_project):
    checker = ConsistencyChecker(temp_project)
    tasks = checker.load_tasks()
    spec = checker.load_spec()

    assert len(tasks) == 4
    assert 'T001' in tasks
    assert tasks['T001']['status'] == 'done'
    assert tasks['T002']['user_story'] == 'US1'
    assert tasks['T003']['dependencies'] == ['T002']

    assert len(spec) == 2
    assert 'US1' in spec
    assert 'US2' in spec

    # Run full check
    result = checker.run()
    assert result is True
    assert len(checker.errors) == 0

def test_missing_dependency_detection(temp_project):
    # Modify tasks.md to have invalid dependency
    tasks_md = temp_project / "tasks.md"
    tasks_md.write_text("""
    # Tasks

    - [X] T001 Create project structure
    - [ ] T002 [US1] Depends on T999
    """)

    checker = ConsistencyChecker(temp_project)
    tasks = checker.load_tasks()

    checker.check_task_dependencies(tasks)

    assert any("non-existent task T999" in err for err in checker.errors)

def test_user_story_coverage_detection(temp_project):
    # Remove US2 from spec
    spec_md = temp_project / "specs" / "001-network-topology-thermal" / "spec.md"
    spec_md.write_text("""
    ## US1: Main Logic
    FR-001: Implement main logic.
    """)

    checker = ConsistencyChecker(temp_project)
    tasks = checker.load_tasks()
    spec = checker.load_spec()

    checker.check_user_story_coverage(tasks, spec)

    assert any("User story US2 in spec.md has no tasks" in err for err in checker.errors)

def test_orphaned_task_warning(temp_project):
    # Add task without user story
    tasks_md = temp_project / "tasks.md"
    tasks_md.write_text("""
    # Tasks

    - [X] T001 Create project structure
    - [ ] T002 Implement random logic
    """)

    checker = ConsistencyChecker(temp_project)
    tasks = checker.load_tasks()

    checker.check_orphaned_tasks(tasks)

    assert any("Task T002 has no user story association" in warn for warn in checker.warnings)
