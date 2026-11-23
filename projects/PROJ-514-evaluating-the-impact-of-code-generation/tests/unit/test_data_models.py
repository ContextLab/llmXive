import pytest
from utils.data_models import CodeSample, SmellMetric, StatResult

class TestCodeSample:
    def test_create_human_sample(self):
        sample = CodeSample(
            source_type="human",
            repository_id="repo_123",
            issue_id="ISS-001",
            task_id="T-001",
            language="python",
            file_path="src/main.py",
            function_name="calculate_sum",
            is_fresh_commit=True,
            content="def calculate_sum(a, b): return a + b",
            sample_id="sample_001",
            commit_sha="abc123"
        )
        assert sample.source_type == "human"
        assert sample.is_fresh_commit is True
        assert len(sample.content) > 0

    def test_to_dict_serialization(self):
        sample = CodeSample(
            source_type="llm",
            repository_id="repo_456",
            issue_id="ISS-002",
            task_id="T-002",
            language="java",
            file_path="src/Service.java",
            function_name="processData",
            is_fresh_commit=False,
            sample_id="sample_002",
            commit_sha="def456"
        )
        data = sample.to_dict()
        assert data["source_type"] == "llm"
        assert data["content_length"] == 0
        assert "sample_id" in data

    def test_from_dict_reconstruction(self):
        raw_data = {
            "source_type": "human",
            "repository_id": "repo_999",
            "issue_id": "ISS-003",
            "task_id": "T-003",
            "language": "python",
            "file_path": "utils.py",
            "function_name": "helper",
            "is_fresh_commit": True,
            "sample_id": "sample_003",
            "commit_sha": "ghi789"
        }
        sample = CodeSample.from_dict(raw_data)
        assert sample.repository_id == "repo_999"
        assert sample.function_name == "helper"

class TestSmellMetric:
    def test_create_metric(self):
        metric = SmellMetric(
            sample_id="sample_001",
            smell_type="LongMethod",
            count=1,
            threshold_used=30.0,
            continuous_metric_value=45.0
        )
        assert metric.smell_type == "LongMethod"
        assert metric.count == 1

    def test_to_dict(self):
        metric = SmellMetric(
            sample_id="sample_002",
            smell_type="DuplicatedCode",
            count=3,
            threshold_used=10.0,
            continuous_metric_value=15.5
        )
        data = metric.to_dict()
        assert data["count"] == 3
        assert isinstance(data["threshold_used"], float)

class TestStatResult:
    def test_create_result(self):
        result = StatResult(
            smell_type="LongMethod",
            p_value=0.03,
            effect_size=0.45,
            confidence_interval=(0.1, 0.8),
            correction_method="bonferroni",
            test_method_used="blocked_permutation"
        )
        assert result.p_value == 0.03
        assert result.confidence_interval == (0.1, 0.8)

    def test_to_dict_list_conversion(self):
        result = StatResult(
            smell_type="FeatureEnvy",
            p_value=0.12,
            effect_size=0.15,
            confidence_interval=(0.0, 0.3),
            correction_method="bonferroni",
            test_method_used="blocked_permutation"
        )
        data = result.to_dict()
        # Ensure tuple is converted to list for JSON compatibility
        assert isinstance(data["confidence_interval"], list)
        assert data["smell_type"] == "FeatureEnvy"