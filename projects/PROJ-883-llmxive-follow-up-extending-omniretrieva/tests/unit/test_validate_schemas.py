"""Tests that contract schemas can validate a representative instance."""

from pathlib import Path

from validate_schemas import load_schema, validate_instance


def _schema_path(name: str) -> Path:
    """Return the absolute Path to a contract schema file."""
    return Path("specs/001-llmxive-follow-up-extending-omniretrieva/contracts") / f"{name}.schema.yaml"


def test_query_instance_schema():
    schema = load_schema(_schema_path("query_instance"))
    instance = {
        "query_id": "q_1",
        "source_type": "text",
        "complexity_level": 1,
        "logical_plan": {"steps": []},
        "ground_truth_plan": {"steps": []},
    }
    # Should not raise ValidationError
    validate_instance(schema, instance, "query_instance")


def test_execution_log_schema():
    schema = load_schema(_schema_path("execution_log"))
    instance = {
        "query_id": "q_1",
        "source_type": "graph",
        "complexity_level": 3,
        "latency_ms": 123.4,
        "translation_error": False,
        "success_flag": True,
        "timeout_flag": False,
    }
    validate_instance(schema, instance, "execution_log")


def test_execution_metric_schema():
    schema = load_schema(_schema_path("execution_metric"))
    instance = {
        "query_id": "q_1",
        "source_type": "relational",
        "complexity_level": 2,
        "latency_ms": 87.6,
        "translation_error": True,
        "success_flag": False,
        "timeout_flag": True,
        "engine_version": "sqlite-3.41",
        "throttle_config": "2 cores, 7 GB",
    }
    validate_instance(schema, instance, "execution_metric")


def test_statistics_result_schema():
    schema = load_schema(_schema_path("statistics-result"))
    instance = {
        "cutoff": 3,
        "spike_point": 2.5,
        "slope_change": 1.23,
    }
    validate_instance(schema, instance, "statistics-result")