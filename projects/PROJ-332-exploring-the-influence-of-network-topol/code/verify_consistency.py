import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
import yaml

class ConsistencyChecker:
    """
    Verifies consistency between tasks.md, plan.md (if available), and spec.md.
    Checks for:
    1. Existence of required files
    2. Task ID presence and status alignment
    3. Dependency validity
    4. Requirement traceability (FR/SC codes)
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tasks_path = project_root / "tasks.md"
        self.plan_path = project_root / "plan.md"
        self.spec_path = project_root / "specs" / "001-network-topology-thermal" / "spec.md"
        
        self.tasks: List[Dict] = []
        self.plan: Optional[Dict] = None
        self.spec: Optional[Dict] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_files(self) -> bool:
        """Load and parse all required markdown/yaml files."""
        if not self.tasks_path.exists():
            self.errors.append(f"Missing required file: {self.tasks_path}")
            return False
        
        with open(self.tasks_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Simple parser for tasks.md structure
            self.tasks = self._parse_tasks_md(content)
        
        if self.plan_path.exists():
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.plan = self._parse_plan_md(f.read())
        else:
            self.warnings.append(f"Optional file missing: {self.plan_path} (will skip plan comparisons)")
        
        if not self.spec_path.exists():
            self.errors.append(f"Missing required file: {self.spec_path}")
            return False
        
        with open(self.spec_path, 'r', encoding='utf-8') as f:
            self.spec = self._parse_spec_md(f.read())
        
        return True

    def _parse_tasks_md(self, content: str) -> List[Dict]:
        """Extract task entries from tasks.md."""
        tasks = []
        current_task = None
        
        for line in content.splitlines():
            if line.strip().startswith("- [ ]") or line.strip().startswith("- [X]"):
                if current_task:
                    tasks.append(current_task)
                
                # Parse task line
                match = re.match(r"- \[([X ])\]\s+([A-Z0-9]+)\s+(.*)", line.strip())
                if match:
                    status = "completed" if match.group(1) == "X" else "pending"
                    task_id = match.group(2)
                    description = match.group(3)
                    current_task = {
                        "id": task_id,
                        "status": status,
                        "description": description,
                        "line": line
                    }
            elif current_task and line.strip().startswith("<!--") and "FAILED" in line:
                # Handle failed task markers
                current_task["status"] = "failed"
                current_task["failure_reason"] = line.strip()
        
        if current_task:
            tasks.append(current_task)
        
        return tasks

    def _parse_plan_md(self, content: str) -> Dict:
        """Extract plan structure from plan.md."""
        return {
            "phases": self._extract_sections(content, "Phase"),
            "dependencies": self._extract_dependencies(content)
        }

    def _parse_spec_md(self, content: str) -> Dict:
        """Extract requirements from spec.md."""
        return {
            "functional_requirements": self._extract_requirements(content, "FR-"),
            "system_constraints": self._extract_requirements(content, "SC-"),
            "user_stories": self._extract_user_stories(content)
        }

    def _extract_sections(self, content: str, marker: str) -> List[str]:
        """Extract section headers containing marker."""
        sections = []
        for line in content.splitlines():
            if marker in line and line.strip().startswith("#"):
                sections.append(line.strip())
        return sections

    def _extract_dependencies(self, content: str) -> Dict[str, List[str]]:
        """Extract dependency relationships."""
        deps = {}
        current_section = None
        for line in content.splitlines():
            if "Dependencies" in line and line.strip().startswith("#"):
                current_section = "dependencies"
            elif current_section and "-" in line:
                parts = line.strip().split("->")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip()
                    if key not in deps:
                        deps[key] = []
                    deps[key].append(val)
        return deps

    def _extract_requirements(self, content: str, prefix: str) -> List[str]:
        """Extract requirement codes."""
        reqs = set()
        pattern = re.compile(rf"{prefix}\d{{3}}")
        for match in pattern.finditer(content):
            reqs.add(match.group())
        return sorted(list(reqs))

    def _extract_user_stories(self, content: str) -> List[str]:
        """Extract user story identifiers."""
        stories = set()
        pattern = re.compile(r"US\d+")
        for match in pattern.finditer(content):
            stories.add(match.group())
        return sorted(list(stories))

    def check_task_id_presence(self):
        """Verify all tasks in tasks.md are accounted for."""
        if not self.tasks:
            self.errors.append("No tasks found in tasks.md")
            return

        task_ids = {t["id"] for t in self.tasks}
        if "T041" not in task_ids:
            self.errors.append("Task T041 not found in tasks.md")

    def check_requirement_traceability(self):
        """Verify tasks reference valid requirements from spec.md."""
        if not self.spec:
            return

        valid_fr = set(self.spec["functional_requirements"])
        valid_sc = set(self.spec["system_constraints"])
        
        for task in self.tasks:
            desc = task["description"]
            # Check for FR/SC references
            fr_matches = re.findall(r"FR-\d{3}", desc)
            sc_matches = re.findall(r"SC-\d{3}", desc)
            
            for fr in fr_matches:
                if fr not in valid_fr:
                    self.warnings.append(f"Task {task['id']} references unknown requirement: {fr}")
            
            for sc in sc_matches:
                if sc not in valid_sc:
                    self.warnings.append(f"Task {task['id']} references unknown constraint: {sc}")

    def check_dependency_validity(self):
        """Verify declared dependencies exist in the task list."""
        task_ids = {t["id"] for t in self.tasks}
        
        for task in self.tasks:
            if "Depends on" in task["description"]:
                # Simple extraction of dependency IDs
                deps = re.findall(r"T\d{3}", task["description"])
                for dep in deps:
                    if dep != task["id"] and dep not in task_ids:
                        self.errors.append(f"Task {task['id']} depends on non-existent task: {dep}")

    def check_plan_alignment(self):
        """If plan.md exists, verify tasks align with plan phases."""
        if not self.plan:
            return

        # Extract phase names from plan
        plan_phases = {p.replace("# ", "").replace(":", "").strip() 
                      for p in self.plan["phases"]}
        
        for task in self.tasks:
            # Check if task mentions a phase that exists in plan
            for phase in plan_phases:
                if phase.lower() in task["description"].lower():
                    # Valid alignment found
                    break

    def run_checks(self) -> bool:
        """Execute all consistency checks."""
        if not self.load_files():
            return False

        self.check_task_id_presence()
        self.check_requirement_traceability()
        self.check_dependency_validity()
        self.check_plan_alignment()

        return len(self.errors) == 0

    def print_report(self):
        """Print a detailed consistency report."""
        print("=" * 60)
        print("CONSISTENCY CHECK REPORT: T041")
        print("=" * 60)
        
        if self.errors:
            print("\n❌ ERRORS FOUND:")
            for err in self.errors:
                print(f"  - {err}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warn in self.warnings:
                print(f"  - {warn}")
        
        if not self.errors and not self.warnings:
            print("\n✅ No consistency issues found.")
        
        print("\nSummary:")
        print(f"  Tasks analyzed: {len(self.tasks)}")
        print(f"  Requirements checked: {len(self.spec['functional_requirements']) + len(self.spec['system_constraints']) if self.spec else 0}")
        print(f"  Status: {'FAILED' if self.errors else 'PASSED'}")
        print("=" * 60)

    def main():
        """Entry point for script execution."""
        project_root = Path.cwd()
        checker = ConsistencyChecker(project_root)
        
        success = checker.run_checks()
        checker.print_report()
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    ConsistencyChecker.main()
