"""
Benchmark Generator: Generates 500 synthetic GUI tasks with error injection and recovery paths.
"""
import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# Import from sibling modules
from .taxonomy_loader import TaxonomyLoader, ErrorRule
from .taxonomy_validator import TaxonomyValidator
from config import get_project_root, CONFIG

@dataclass
class BenchmarkTask:
    """Represents a single benchmark task."""
    id: str
    type: str  # "linear" or "non-linear"
    description: str
    initial_state: Dict[str, Any]
    target_state: Dict[str, Any]
    steps: List[Dict[str, Any]]
    error_injection: Optional[Dict[str, Any]]
    recovery_path: Optional[List[Dict[str, Any]]]
    difficulty: int  # 1-5
    metadata: Dict[str, Any]

class BenchmarkGenerator:
    """Generates synthetic benchmark tasks with error injection."""

    def __init__(self, taxonomy_path: str, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        self.taxonomy_loader = TaxonomyLoader(taxonomy_path)
        self.rules = self.taxonomy_loader.load()
        self.validator = TaxonomyValidator(self.rules)
        self.tasks: List[BenchmarkTask] = []

    def _generate_task_id(self, index: int) -> str:
        """Generate a deterministic task ID."""
        content = f"task_{index}_{self.seed}"
        return f"task_{hashlib.md5(content.encode()).hexdigest()[:8]}"

    def _generate_linear_task(self, index: int) -> BenchmarkTask:
        """Generate a simple linear task (no error injection)."""
        task_id = self._generate_task_id(index)

        steps = [
            {"action": "navigate", "target": "home"},
            {"action": "click", "element": "button_1"},
            {"action": "input", "field": "text_1", "value": "sample_data"},
            {"action": "click", "element": "submit"},
            {"action": "verify", "result": "success"}
        ]

        return BenchmarkTask(
            id=task_id,
            type="linear",
            description=f"Linear task {index}: Complete a basic form submission",
            initial_state={"page": "home", "form_filled": False},
            target_state={"page": "confirmation", "form_filled": True},
            steps=steps,
            error_injection=None,
            recovery_path=None,
            difficulty=1,
            metadata={"generated_at": datetime.now().isoformat(), "version": "1.0"}
        )

    def _generate_nonlinear_task(self, index: int) -> BenchmarkTask:
        """Generate a non-linear task with error injection and recovery."""
        task_id = self._generate_task_id(index)

        # Select a random error rule
        error_rule = random.choice(self.rules)

        # Generate base steps
        base_steps = [
            {"action": "navigate", "target": "home"},
            {"action": "click", "element": "menu_item"},
            {"action": "input", "field": "search", "value": "query"},
            {"action": "click", "element": "result_1"}
        ]

        # Inject error at a random step
        error_step_index = random.randint(1, len(base_steps) - 1)
        error_injection = {
            "step_index": error_step_index,
            "rule_id": error_rule.rule_id,
            "rule_name": error_rule.name,
            "trigger": error_rule.injection_trigger,
            "expected_failure": "error_dialog_appears"
        }

        # Generate recovery path
        recovery_path = [
            {"action": "click", "element": "error_close"},
            {"action": "navigate", "target": "previous"},
            {"action": "retry", "step": base_steps[error_step_index]},
            {"action": "continue"}
        ]

        # Insert error point into steps
        steps = base_steps.copy()
        steps.insert(error_step_index + 1, {
            "action": "error_state",
            "rule_id": error_rule.rule_id,
            "message": error_rule.description
        })

        return BenchmarkTask(
            id=task_id,
            type="non-linear",
            description=f"Non-linear task {index}: {error_rule.name} with recovery",
            initial_state={"page": "home", "state": "ready"},
            target_state={"page": "success", "state": "completed"},
            steps=steps,
            error_injection=error_injection,
            recovery_path=recovery_path,
            difficulty=random.randint(3, 5),
            metadata={
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
                "error_rule": error_rule.rule_id
            }
        )

    def generate(self, total_tasks: int = 500, non_linear_ratio: float = 0.8) -> List[BenchmarkTask]:
        """
        Generate the full benchmark dataset.
        Args:
            total_tasks: Total number of tasks to generate (default 500)
            non_linear_ratio: Ratio of non-linear tasks (default 0.8)
        """
        self.tasks = []
        num_non_linear = int(total_tasks * non_linear_ratio)
        num_linear = total_tasks - num_non_linear

        # Generate linear tasks
        for i in range(num_linear):
            self.tasks.append(self._generate_linear_task(i))

        # Generate non-linear tasks
        for i in range(num_non_linear):
            self.tasks.append(self._generate_nonlinear_task(i + num_linear))

        # Shuffle to mix linear and non-linear
        random.shuffle(self.tasks)

        return self.tasks

    def validate(self) -> Dict[str, Any]:
        """Validate the generated dataset against the taxonomy."""
        task_dicts = [asdict(t) for t in self.tasks]
        return self.validator.validate_dataset(task_dicts)

    def save(self, output_path: str):
        """Save the benchmark dataset to a JSON file."""
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        task_dicts = [asdict(t) for t in self.tasks]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(task_dicts, f, indent=2)

    def save_validation_report(self, output_path: str):
        """Generate and save the validation report."""
        report = self.validate()
        self.validator.save_report(report, output_path)

def main():
    """Main entry point for benchmark generation."""
    project_root = get_project_root()
    taxonomy_path = project_root / "data" / "config" / "gui_error_taxonomy.yaml"
    output_path = project_root / "data" / "benchmarks" / "benchmark_.json"
    report_path = project_root / "data" / "results" / "taxonomy_validation_report.json"

    print(f"Loading taxonomy from: {taxonomy_path}")
    generator = BenchmarkGenerator(str(taxonomy_path))

    print(f"Generating 500 benchmark tasks...")
    tasks = generator.generate(total_tasks=500)

    print(f"Saving benchmark to: {output_path}")
    generator.save(str(output_path))

    print(f"Generating validation report...")
    generator.save_validation_report(str(report_path))

    # Print summary
    linear_count = sum(1 for t in tasks if t.type == "linear")
    nonlinear_count = sum(1 for t in tasks if t.type == "non-linear")
    print(f"Generated {len(tasks)} tasks: {linear_count} linear, {nonlinear_count} non-linear")

    # Validate
    validation = generator.validate()
    print(f"Validation: {validation['valid_tasks']} valid, {validation['invalid_tasks']} invalid")
    print(f"Rule coverage: {validation['coverage_rate']:.2%}")

    return 0

if __name__ == "__main__":
    exit(main())
