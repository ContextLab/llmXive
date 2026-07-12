"""
Unit tests for benchmark_generator.py
"""
import json
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.generators.benchmark_generator import BenchmarkGenerator
from code.generators.taxonomy_loader import TaxonomyLoader, ErrorRule
from code.generators.taxonomy_validator import TaxonomyValidator
from code.config import get_project_root

@pytest.fixture
def sample_taxonomy():
    """Create a temporary taxonomy file for testing."""
    taxonomy_data = {
        "rules": [
            {
                "rule_id": "R001",
                "name": "Form Validation Error",
                "description": "User submits invalid form data",
                "category": "validation",
                "injection_trigger": "submit_button",
                "recovery_path": "fix_fields_and_resubmit",
                "severity": 3,
                "probability": 0.7
            },
            {
                "rule_id": "R002",
                "name": "Network Timeout",
                "description": "Request fails due to timeout",
                "category": "network",
                "injection_trigger": "api_call",
                "recovery_path": "retry_or_fallback",
                "severity": 4,
                "probability": 0.3
            }
        ]
    }

    project_root = get_project_root()
    taxonomy_path = project_root / "data" / "config" / "gui_error_taxonomy.yaml"
    taxonomy_path.parent.mkdir(parents=True, exist_ok=True)

    import yaml
    with open(taxonomy_path, 'w') as f:
        yaml.dump(taxonomy_data, f)

    return str(taxonomy_path)

@pytest.fixture
def generator(sample_taxonomy):
    """Create a BenchmarkGenerator instance."""
    return BenchmarkGenerator(sample_taxonomy, seed=42)

def test_generator_initialization(generator):
    """Test that generator loads rules correctly."""
    assert len(generator.rules) == 2
    assert generator.rules[0].rule_id == "R001"
    assert generator.rules[1].rule_id == "R002"

def test_generate_linear_task(generator):
    """Test linear task generation."""
    task = generator._generate_linear_task(0)
    assert task.type == "linear"
    assert task.error_injection is None
    assert task.recovery_path is None
    assert len(task.steps) > 0
    assert "id" in task.id

def test_generate_nonlinear_task(generator):
    """Test non-linear task generation."""
    task = generator._generate_nonlinear_task(0)
    assert task.type == "non-linear"
    assert task.error_injection is not None
    assert task.recovery_path is not None
    assert "rule_id" in task.error_injection
    assert len(task.recovery_path) > 0

def test_generate_dataset(generator):
    """Test full dataset generation."""
    tasks = generator.generate(total_tasks=20, non_linear_ratio=0.5)
    assert len(tasks) == 20

    linear_count = sum(1 for t in tasks if t.type == "linear")
    nonlinear_count = sum(1 for t in tasks if t.type == "non-linear")

    assert linear_count == 10
    assert nonlinear_count == 10

def test_validation(generator):
    """Test dataset validation."""
    tasks = generator.generate(total_tasks=20)
    validation = generator.validate()

    assert validation['total_tasks'] == 20
    assert validation['valid_tasks'] + validation['invalid_tasks'] == 20
    assert 'rule_coverage' in validation
    assert 'issues' in validation

def test_save_and_load(generator, tmp_path):
    """Test saving and loading benchmark data."""
    tasks = generator.generate(total_tasks=10)
    output_path = tmp_path / "test_benchmark.json"

    generator.save(str(output_path))
    assert output_path.exists()

    with open(output_path, 'r') as f:
        loaded_tasks = json.load(f)

    assert len(loaded_tasks) == 10
    assert loaded_tasks[0]['type'] in ['linear', 'non-linear']

def test_validation_report(generator, tmp_path):
    """Test validation report generation."""
    tasks = generator.generate(total_tasks=10)
    report_path = tmp_path / "test_report.json"

    generator.save_validation_report(str(report_path))
    assert report_path.exists()

    with open(report_path, 'r') as f:
        report = json.load(f)

    assert 'total_tasks' in report
    assert 'valid_tasks' in report
    assert 'coverage_rate' in report

def test_deterministic_generation():
    """Test that generation is deterministic with same seed."""
    project_root = get_project_root()
    taxonomy_path = project_root / "data" / "config" / "gui_error_taxonomy.yaml"

    if not taxonomy_path.exists():
        pytest.skip("Taxonomy file not found, skipping deterministic test")

    gen1 = BenchmarkGenerator(str(taxonomy_path), seed=123)
    gen2 = BenchmarkGenerator(str(taxonomy_path), seed=123)

    tasks1 = gen1.generate(total_tasks=5)
    tasks2 = gen2.generate(total_tasks=5)

    for t1, t2 in zip(tasks1, tasks2):
        assert t1.id == t2.id
        assert t1.type == t2.type
        assert t1.steps == t2.steps

def test_error_rule_coverage(generator):
    """Test that generated tasks use various error rules."""
    tasks = generator.generate(total_tasks=100, non_linear_ratio=1.0)
    validation = generator.validate()

    used_rules = set(validation['rule_coverage'].keys())
    assert len(used_rules) > 0
    assert len(used_rules) <= len(generator.rules)