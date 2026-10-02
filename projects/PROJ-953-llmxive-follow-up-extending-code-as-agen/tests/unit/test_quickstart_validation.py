"""
Unit tests for T037: quickstart.md validation.

This test suite verifies that quickstart.md enforces the full-environment
re-execution baseline and does NOT allow a 'static-only shortcut'.
"""
import os
import re
from pathlib import Path

import pytest


def get_quickstart_content() -> str:
    """Load the content of docs/quickstart.md."""
    quickstart_path = Path("docs/quickstart.md")
    if not quickstart_path.exists():
        pytest.fail(f"docs/quickstart.md not found. Expected at: {quickstart_path.absolute()}")
    
    with open(quickstart_path, "r", encoding="utf-8") as f:
        return f.read()


class TestQuickstartValidation:
    """Tests to validate quickstart.md content against T037 requirements."""

    def test_file_exists(self):
        """Verify that docs/quickstart.md exists."""
        assert Path("docs/quickstart.md").exists(), "docs/quickstart.md must exist"

    def test_rejects_static_only_shortcut(self):
        """
        Verify that quickstart.md does NOT allow a 'static-only shortcut'.
        
        The validation MUST FAIL if the document suggests skipping dynamic execution,
        CPU-only baseline, or full environment re-execution.
        """
        content = get_quickstart_content()
        
        # Patterns that indicate a forbidden shortcut
        forbidden_patterns = [
            r"static.*only",
            r"skip.*dynamic",
            r"no.*execution",
            r"shortcut.*baseline",
            r"bypass.*re-execution",
            r"static.*analysis.*only",
            r"without.*running",
            r"static-only",
            r"no.*baseline",
            r"skip.*baseline",
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                pytest.fail(
                    f"quickstart.md contains forbidden shortcut pattern: '{pattern}'. "
                    "The document must enforce full-environment re-execution."
                )

    def test_enforces_full_environment_reexecution(self):
        """
        Verify that quickstart.md explicitly enforces the full-environment re-execution baseline.
        
        The document must contain clear instructions for:
        1. Setting up the full environment (virtualenv, dependencies)
        2. Downloading real data (not synthetic)
        3. Running the dynamic execution baseline
        """
        content = get_quickstart_content()
        
        required_elements = [
            (r"virtualenv|venv|environment", "Environment setup instructions"),
            (r"pip.*install|requirements", "Dependency installation"),
            (r"download|fetch|ingest.*data", "Data download instructions"),
            (r"baseline|dynamic.*execution|run.*baseline", "Baseline execution requirement"),
            (r"re-execut|full.*environment", "Re-execution baseline mention"),
        ]
        
        missing = []
        for pattern, description in required_elements:
            if not re.search(pattern, content, re.IGNORECASE):
                missing.append(description)
        
        if missing:
            pytest.fail(
                f"quickstart.md is missing required elements for full-environment re-execution: {missing}. "
                "The document must explicitly enforce the baseline."
            )

    def test_steps_for_environment_setup(self):
        """Verify step-by-step instructions for environment setup are present."""
        content = get_quickstart_content()
        
        # Look for numbered steps or clear sequence indicators
        step_patterns = [
            r"step\s*\d+",
            r"1\.\s+",
            r"first\s+step",
            r"setup.*step",
            r"install.*dependencies",
        ]
        
        found_steps = any(re.search(p, content, re.IGNORECASE) for p in step_patterns)
        assert found_steps, (
            "quickstart.md must include step-by-step instructions for environment setup. "
            "Found no clear sequence or steps."
        )

    def test_steps_for_data_download(self):
        """Verify step-by-step instructions for data download are present."""
        content = get_quickstart_content()
        
        step_patterns = [
            r"download.*data",
            r"fetch.*dataset",
            r"ingest.*task",
            r"step.*data",
            r"1\.\s+.*data",
        ]
        
        found_steps = any(re.search(p, content, re.IGNORECASE) for p in step_patterns)
        assert found_steps, (
            "quickstart.md must include step-by-step instructions for data download. "
            "Found no clear sequence or steps."
        )

    def test_steps_for_model_training(self):
        """Verify step-by-step instructions for model training are present."""
        content = get_quickstart_content()
        
        step_patterns = [
            r"train.*model",
            r"model.*training",
            r"step.*train",
            r"1\.\s+.*train",
            r"run.*training",
        ]
        
        found_steps = any(re.search(p, content, re.IGNORECASE) for p in step_patterns)
        assert found_steps, (
            "quickstart.md must include step-by-step instructions for model training. "
            "Found no clear sequence or steps."
        )

    def test_cpu_only_constraint_enforced(self):
        """
        Verify that quickstart.md enforces CPU-only execution.
        
        The document should explicitly state that no GPU/CUDA is used
        and that the baseline is CPU-only.
        """
        content = get_quickstart_content()
        
        # Should mention CPU or explicitly exclude GPU
        cpu_patterns = [
            r"cpu.*only",
            r"no.*gpu",
            r"cpu.*execution",
            r"cpu.*baseline",
            r"without.*gpu",
            r"cpu-only",
        ]
        
        found_cpu = any(re.search(p, content, re.IGNORECASE) for p in cpu_patterns)
        assert found_cpu, (
            "quickstart.md must explicitly enforce CPU-only execution. "
            "Found no mention of CPU constraints or GPU exclusion."
        )

    def test_real_data_requirement_enforced(self):
        """
        Verify that quickstart.md enforces real data usage.
        
        The document must explicitly state that synthetic data is NOT allowed
        and that real datasets (SWE-bench, AgentBench) must be used.
        """
        content = get_quickstart_content()
        
        # Should mention real data or specific datasets
        real_data_patterns = [
            r"real.*data",
            r"actual.*data",
            r"no.*synthetic",
            r"no.*fake",
            r"swe-bench",
            r"agentbench",
            r"huggingface",
            r"download.*real",
        ]
        
        found_real = any(re.search(p, content, re.IGNORECASE) for p in real_data_patterns)
        assert found_real, (
            "quickstart.md must enforce real data usage. "
            "Found no mention of real data requirement or specific datasets."
        )

    def test_no_synthetic_fallback_mentioned(self):
        """
        Verify that quickstart.md does NOT mention synthetic fallbacks.
        
        The document should not suggest using synthetic data as a fallback
        when real data is unavailable.
        """
        content = get_quickstart_content()
        
        forbidden_patterns = [
            r"synthetic.*fallback",
            r"fallback.*data",
            r"mock.*data",
            r"fake.*fallback",
            r"generate.*synthetic",
            r"sample.*data.*fallback",
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                pytest.fail(
                    f"quickstart.md mentions forbidden synthetic fallback: '{pattern}'. "
                    "The document must not suggest using synthetic data."
                )

    def test_timeout_handling_mentioned(self):
        """
        Verify that quickstart.md mentions timeout handling for baseline execution.
        
        The document should mention that timeouts are handled and recorded.
        """
        content = get_quickstart_content()
        
        timeout_patterns = [
            r"timeout",
            r"duration.*limit",
            r"max.*time",
            r"execution.*timeout",
        ]
        
        found_timeout = any(re.search(p, content, re.IGNORECASE) for p in timeout_patterns)
        assert found_timeout, (
            "quickstart.md should mention timeout handling for baseline execution. "
            "Found no mention of timeouts or duration limits."
        )

    def test_output_artifacts_listed(self):
        """
        Verify that quickstart.md lists expected output artifacts.
        
        The document should mention the key output files like ground_truth.csv,
        features.csv, and model reports.
        """
        content = get_quickstart_content()
        
        artifact_patterns = [
            r"ground.*truth",
            r"features.*csv",
            r"model.*report",
            r"decision.*boundary",
            r"threshold.*sweep",
        ]
        
        found_artifacts = any(re.search(p, content, re.IGNORECASE) for p in artifact_patterns)
        assert found_artifacts, (
            "quickstart.md should list expected output artifacts. "
            "Found no mention of key output files."
        )