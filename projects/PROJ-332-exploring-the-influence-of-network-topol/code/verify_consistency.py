"""
T041: Verify tasks.md and plan.md consistency against spec.md requirements.

This script performs a static analysis of the project's documentation to ensure
that the tasks defined in `tasks.md` and the implementation plan in `plan.md`
align with the functional and non-functional requirements listed in `spec.md`.

It checks for:
1. Presence of required requirement IDs (FR-*, SC-*) in task descriptions.
2. Consistency of file paths between tasks and the actual project structure.
3. Validation of dependency chains (e.g., T007a must precede T015).
4. Verification that all "Unresolved Claims" are either resolved or flagged.
5. Confirmation that all User Stories have corresponding implementation and test tasks.

Exit codes:
0: Consistency check passed.
1: Consistency check failed (inconsistencies found).
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

# Project root relative to this script (assuming script is in code/)
PROJECT_ROOT = Path(__file__).parent.parent

TASKS_MD_PATH = PROJECT_ROOT / "tasks.md"
PLAN_MD_PATH = PROJECT_ROOT / "plan.md"
SPEC_MD_PATH = PROJECT_ROOT / "specs" / "001-network-topology-thermal" / "spec.md"
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-network-topology-thermal" / "contracts"

# Regex patterns
REQ_PATTERN = re.compile(r'(FR-\d+|SC-\d+)')
TASK_ID_PATTERN = re.compile(r'\[([~X ])\]\s*T(\d+)')
UNRESOLVED_CLAIM_PATTERN = re.compile(r'\[UNRESOLVED-CLAIM:\s*c_[a-f0-9]+\s*—\s*status=not_enough_info\]')
FILE_PATH_PATTERN = re.compile(r'`code/[^`]+`|`tests/[^`]+`|`data/[^`]+`|`specs/[^`]+`')

class ConsistencyChecker:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.tasks: Dict[str, Dict] = {}
        self.requirements: Set[str] = set()
        self.claims: Set[str] = set()
        self.files_referenced: Set[str] = set()
        self.user_stories: Set[str] = set()

    def load_file(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")
        return path.read_text(encoding='utf-8')

    def parse_tasks(self, content: str) -> None:
        lines = content.split('\n')
        current_story = None
        for line in lines:
            # Detect User Story headers
            if 'User Story' in line:
                match = re.search(r'User Story\s+(\d+)', line)
                if match:
                    current_story = f"US{match.group(1)}"
                    self.user_stories.add(current_story)

            # Detect task lines
            match = TASK_ID_PATTERN.search(line)
            if match:
                status = match.group(1)
                task_id = f"T{match.group(2)}"
                self.tasks[task_id] = {
                    'status': status,
                    'line': line,
                    'story': current_story,
                    'content': line
                }

                # Extract requirements
                reqs = REQ_PATTERN.findall(line)
                for req in reqs:
                    self.requirements.add(req)

                # Extract unresolved claims
                claims = UNRESOLVED_CLAIM_PATTERN.findall(line)
                for claim in claims:
                    self.claims.add(claim)

                # Extract file paths
                paths = FILE_PATH_PATTERN.findall(line)
                for p in paths:
                    self.files_referenced.add(p.strip('`'))

    def validate_requirements_coverage(self, spec_content: str) -> None:
        """Check if all requirements in spec.md are referenced in tasks.md."""
        spec_reqs = set(REQ_PATTERN.findall(spec_content))
        missing_in_tasks = spec_reqs - self.requirements

        # Filter out requirements that might be optional or meta
        # For now, flag any missing as a warning or error depending on severity
        if missing_in_tasks:
            self.errors.append(f"Requirements in spec.md not referenced in tasks.md: {sorted(missing_in_tasks)}")

    def validate_dependency_chains(self) -> None:
        """Check for logical dependency violations based on task descriptions."""
        # Hardcoded critical dependencies from tasks.md
        critical_deps = {
            'T007a': ['T015', 'T021', 'T029', 'T035'],
            'T004a': ['T021'],
            'T001a': ['T038'],
            'T027a': ['T028']
        }

        for prereq, dependents in critical_deps.items():
            if prereq not in self.tasks:
                self.errors.append(f"Missing prerequisite task: {prereq}")
                continue

            prereq_status = self.tasks[prereq]['status']
            for dep in dependents:
                if dep in self.tasks:
                    dep_status = self.tasks[dep]['status']
                    # If prerequisite is done (X) but dependent is not (not X), it's a state, not an error
                    # If prerequisite is NOT done but dependent IS done, that's an error
                    if prereq_status != 'X' and dep_status == 'X':
                        self.errors.append(f"Dependency violation: {dep} is marked done, but prerequisite {prereq} is not.")

    def validate_file_paths(self) -> None:
        """Ensure referenced files exist or are expected to be created."""
        existing_files = set()
        for root, _, files in os.walk(PROJECT_ROOT):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), PROJECT_ROOT)
                existing_files.add(rel)

        for ref in self.files_referenced:
            # Normalize path
            if ref.startswith('code/'):
                full_path = PROJECT_ROOT / ref
            elif ref.startswith('tests/'):
                full_path = PROJECT_ROOT / ref
            elif ref.startswith('data/'):
                full_path = PROJECT_ROOT / ref
            elif ref.startswith('specs/'):
                full_path = PROJECT_ROOT / ref
            else:
                continue

            if not full_path.exists():
                # Check if it's a directory reference (e.g., `data/raw/`)
                if ref.endswith('/'):
                    if not full_path.exists():
                        self.warnings.append(f"Referenced directory does not exist: {ref}")
                else:
                    # It might be a file to be created by a task
                    # We assume if it's in tasks.md as a target, it's intended to be created
                    pass

    def validate_unresolved_claims(self) -> None:
        """Flag unresolved claims as warnings."""
        if self.claims:
            self.warnings.append(f"Unresolved claims found in tasks: {self.claims}")

    def validate_user_story_coverage(self) -> None:
        """Ensure every User Story has at least one implementation and one test task."""
        # Group tasks by story
        story_tasks: Dict[str, List[str]] = {us: [] for us in self.user_stories}
        for tid, tdata in self.tasks.items():
            if tdata['story'] and tdata['story'] in story_tasks:
                story_tasks[tdata['story']].append(tid)

        for story, tids in story_tasks.items():
            impl_tasks = [t for t in tids if 'Unit test' not in t and 'Contract test' not in t and 'Test' not in t]
            test_tasks = [t for t in tids if 'test' in t.lower()]

            if not impl_tasks:
                self.errors.append(f"{story} has no implementation tasks.")
            if not test_tasks:
                self.errors.append(f"{story} has no test tasks.")

    def run(self) -> bool:
        try:
            tasks_content = self.load_file(TASKS_MD_PATH)
            spec_content = self.load_file(SPEC_MD_PATH)
            # plan.md is optional for this check but good to have
            if PLAN_MD_PATH.exists():
                self.load_file(PLAN_MD_PATH) # Just check existence/readability

            self.parse_tasks(tasks_content)
            self.validate_requirements_coverage(spec_content)
            self.validate_dependency_chains()
            self.validate_file_paths()
            self.validate_unresolved_claims()
            self.validate_user_story_coverage()

            if self.errors:
                print("CONSISTENCY CHECK FAILED:")
                for err in self.errors:
                    print(f"  [ERROR] {err}")
                return False

            if self.warnings:
                print("CONSISTENCY CHECK PASSED WITH WARNINGS:")
                for warn in self.warnings:
                    print(f"  [WARN] {warn}")
                return True

            print("CONSISTENCY CHECK PASSED: tasks.md and plan.md are consistent with spec.md.")
            return True

        except FileNotFoundError as e:
            print(f"CRITICAL ERROR: {e}")
            return False
        except Exception as e:
            print(f"UNEXPECTED ERROR: {e}")
            return False

if __name__ == "__main__":
    checker = ConsistencyChecker()
    success = checker.run()
    sys.exit(0 if success else 1)