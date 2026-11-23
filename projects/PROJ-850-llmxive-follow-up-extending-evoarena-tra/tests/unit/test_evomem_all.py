import pytest
from pathlib import Path
import sys
import os
import json
import tempfile
from src.agents.evomem_all import EvoMemAll

class TestEvoMemAllInitialization:
    def test_init_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = EvoMemAll(memory_path=Path(tmpdir))
            assert agent.name == "EvoMem-All"
            assert agent.n_patches == 10
            assert agent.memory_path == Path(tmpdir)

    def test_init_custom_params(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = EvoMemAll(
                memory_path=Path(tmpdir),
                n_patches=5,
                seed=123,
                name="TestAgent"
            )
            assert agent.name == "TestAgent"
            assert agent.n_patches == 5

class TestEvoMemAllRetrieval:
    def test_retrieve_fewer_than_n(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock JSONL file with 3 patches
            jsonl_path = Path(tmpdir) / "patches.jsonl"
            patches = [
                {"state_description": "patch 1"},
                {"state_description": "patch 2"},
                {"state_description": "patch 3"}
            ]
            with open(jsonl_path, "w") as f:
                for p in patches:
                    f.write(json.dumps(p) + "\n")

            agent = EvoMemAll(memory_path=Path(tmpdir), n_patches=10)
            selected, tokens = agent.retrieve_context("task_1")

            assert len(selected) == 3
            assert tokens > 0

    def test_retrieve_more_than_n(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock JSONL file with 15 patches
            jsonl_path = Path(tmpdir) / "patches.jsonl"
            patches = [{"state_description": f"patch {i}"} for i in range(15)]
            with open(jsonl_path, "w") as f:
                for p in patches:
                    f.write(json.dumps(p) + "\n")

            agent = EvoMemAll(memory_path=Path(tmpdir), n_patches=5)
            selected, tokens = agent.retrieve_context("task_1")

            assert len(selected) == 5
            # Should get the last 5: patch 10 to 14 (0-indexed)
            assert selected[0]["state_description"] == "patch 10"
            assert selected[-1]["state_description"] == "patch 14"

    def test_retrieve_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = EvoMemAll(memory_path=Path(tmpdir), n_patches=5)
            selected, tokens = agent.retrieve_context("task_1")
            assert len(selected) == 0
            assert tokens == 0

    def test_retrieve_from_passed_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = EvoMemAll(memory_path=Path(tmpdir), n_patches=2)
            patches = [
                {"state_description": "A"},
                {"state_description": "B"},
                {"state_description": "C"}
            ]
            selected, tokens = agent.retrieve_context("task_1", patches=patches)
            assert len(selected) == 2
            assert selected[0]["state_description"] == "B"
            assert selected[1]["state_description"] == "C"

class TestEvoMemAllExecution:
    def test_execute_task_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = Path(tmpdir) / "patches.jsonl"
            patches = [{"state_description": f"patch {i}"} for i in range(5)]
            with open(jsonl_path, "w") as f:
                for p in patches:
                    f.write(json.dumps(p) + "\n")

            agent = EvoMemAll(memory_path=Path(tmpdir), n_patches=3)
            task = {
                "task_id": "test_task",
                "patches": patches
            }
            result = agent.execute_task(task)

            assert result["task_id"] == "test_task"
            assert result["agent_variant"] == "EvoMem-All"
            assert result["patches_retrieved"] == 3
            assert result["success"] is True
            assert "context_tokens" in result
            assert "execution_time_ms" in result

    def test_execute_task_no_patches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = EvoMemAll(memory_path=Path(tmpdir), n_patches=3)
            task = {
                "task_id": "empty_task",
                "patches": []
            }
            result = agent.execute_task(task)

            assert result["task_id"] == "empty_task"
            assert result["patches_retrieved"] == 0
            assert result["success"] is False

class TestEvoMemAllTokenCounting:
    def test_token_estimation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = Path(tmpdir) / "patches.jsonl"
            # 100 characters roughly equals 25 tokens (1 token ~ 4 chars)
            patches = [{"state_description": "x" * 100}]
            with open(jsonl_path, "w") as f:
                for p in patches:
                    f.write(json.dumps(p) + "\n")

            agent = EvoMemAll(memory_path=Path(tmpdir), n_patches=1)
            selected, tokens = agent.retrieve_context("task_1")

            # Expect approximately 25 tokens
            assert 20 <= tokens <= 30
