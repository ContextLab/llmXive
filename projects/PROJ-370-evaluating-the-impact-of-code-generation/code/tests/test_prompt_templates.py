"""
Unit tests for prompt_templates.py
"""
import pytest
import json
from code.src.inference.prompt_templates import (
    SeverityLabel,
    format_severity_label,
    get_severity_priority,
    get_bug_detection_prompt,
    create_inference_request
)


class TestSeverityLabel:
    def test_values_returns_all_severities(self):
        values = SeverityLabel.values()
        assert "critical" in values
        assert "major" in values
        assert "minor" in values
        assert "style" in values
        assert len(values) == 4

    def test_enum_creation(self):
        assert SeverityLabel.CRITICAL.value == "critical"
        assert SeverityLabel.MAJOR.value == "major"
        assert SeverityLabel.MINOR.value == "minor"
        assert SeverityLabel.STYLE.value == "style"


class TestFormatSeverityLabel:
    def test_normalizes_uppercase(self):
        assert format_severity_label("CRITICAL") == "critical"
        assert format_severity_label("Major") == "major"

    def test_normalizes_whitespace(self):
        assert format_severity_label("  minor  ") == "minor"

    def test_rejects_invalid_label(self):
        with pytest.raises(ValueError):
            format_severity_label("invalid_severity")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError):
            format_severity_label("")


class TestGetSeverityPriority:
    def test_priority_order(self):
        assert get_severity_priority("critical") == 0
        assert get_severity_priority("major") == 1
        assert get_severity_priority("minor") == 2
        assert get_severity_priority("style") == 3

    def test_priority_case_insensitive(self):
        assert get_severity_priority("CRITICAL") == 0
        assert get_severity_priority("Minor") == 2


class TestGetBugDetectionPrompt:
    def test_contains_pr_id(self):
        prompt = get_bug_detection_prompt("PR-123", "file.py", "diff")
        assert "PR-123" in prompt

    def test_contains_file_path(self):
        prompt = get_bug_detection_prompt("PR-123", "src/main.py", "diff")
        assert "src/main.py" in prompt

    def test_contains_diff_content(self):
        prompt = get_bug_detection_prompt("PR-123", "file.py", "added line")
        assert "added line" in prompt

    def test_contains_llm_context_flagged(self):
        prompt = get_bug_detection_prompt("PR-123", "file.py", "diff", llm_generated_flag=True)
        assert "flagged as potentially LLM-generated" in prompt

    def test_contains_llm_context_not_flagged(self):
        prompt = get_bug_detection_prompt("PR-123", "file.py", "diff", llm_generated_flag=False)
        assert "standard human-written code" in prompt

    def test_contains_severity_options(self):
        prompt = get_bug_detection_prompt("PR-123", "file.py", "diff")
        assert "critical" in prompt
        assert "major" in prompt
        assert "minor" in prompt
        assert "style" in prompt

    def test_contains_json_instructions(self):
        prompt = get_bug_detection_prompt("PR-123", "file.py", "diff")
        assert "valid JSON list" in prompt
        assert "file_path" in prompt
        assert "line_start" in prompt
        assert "severity" in prompt


class TestCreateInferenceRequest:
    def test_returns_dict(self):
        request = create_inference_request("PR-123", "file.py", "diff")
        assert isinstance(request, dict)

    def test_contains_required_fields(self):
        request = create_inference_request("PR-123", "file.py", "diff")
        assert "pr_id" in request
        assert "file_path" in request
        assert "diff_content" in request
        assert "llm_generated_flag" in request
        assert "prompt" in request

    def test_contains_correct_values(self):
        request = create_inference_request("PR-123", "file.py", "diff", llm_generated_flag=True)
        assert request["pr_id"] == "PR-123"
        assert request["file_path"] == "file.py"
        assert request["diff_content"] == "diff"
        assert request["llm_generated_flag"] is True
        assert isinstance(request["prompt"], str)
        assert len(request["prompt"]) > 0

    def test_prompt_matches_get_bug_detection_prompt(self):
        request = create_inference_request("PR-123", "file.py", "diff", llm_generated_flag=True)
        direct_prompt = get_bug_detection_prompt("PR-123", "file.py", "diff", llm_generated_flag=True)
        assert request["prompt"] == direct_prompt