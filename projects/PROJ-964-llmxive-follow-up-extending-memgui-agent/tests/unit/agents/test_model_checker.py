"""
Unit tests for code/agents/model_checker.py
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from agents.model_checker import (
    verify_model,
    extract_verified_datasets_block,
    check_model_in_block,
    ALLOWED_SUBSTITUTES,
    PRIMARY_MODEL_ID
)


class TestExtractVerifiedDatasetsBlock:
    def test_extract_block_present(self):
        content = """
        # Plan

        ## Verified datasets
        - MemGUI-8B-SFT
        - Some other dataset

        ## Next Section
        """
        result = extract_verified_datasets_block(content)
        assert "MemGUI-8B-SFT" in result
        assert "Verified datasets" in result
        assert "Next Section" not in result

    def test_extract_block_missing(self):
        content = """
        # Plan
        No verified datasets here.
        """
        result = extract_verified_datasets_block(content)
        assert result == ""

    def test_extract_case_insensitive(self):
        content = """
        # Plan
        ## verified datasets
        - MemGUI-8B-SFT
        """
        result = extract_verified_datasets_block(content)
        assert "MemGUI-8B-SFT" in result


class TestCheckModelInBlock:
    def test_model_found(self):
        block = "We use MemGUI-8B-SFT for the task."
        assert check_model_in_block(block, "MemGUI-8B-SFT") is True

    def test_model_not_found(self):
        block = "We use Llama-2 for the task."
        assert check_model_in_block(block, "MemGUI-8B-SFT") is False


class TestVerifyModel:
    @patch('agents.model_checker.read_plan_md')
    def test_primary_found(self, mock_read):
        mock_read.return_value = """
        # Plan
        ## Verified datasets
        - MemGUI-8B-SFT
        """
        success, model_id, msg = verify_model()
        assert success is True
        assert model_id == PRIMARY_MODEL_ID
        assert "found" in msg.lower()

    @patch('agents.model_checker.read_plan_md')
    def test_primary_not_found_pivot(self, mock_read):
        mock_read.return_value = """
        # Plan
        ## Verified datasets
        - SomeOtherModel
        """
        success, model_id, msg = verify_model()
        assert success is True
        assert model_id == ALLOWED_SUBSTITUTES[0]
        assert "pivoting" in msg.lower()

    @patch('agents.model_checker.read_plan_md')
    def test_plan_missing_pivot(self, mock_read):
        mock_read.return_value = None
        success, model_id, msg = verify_model()
        assert success is True
        assert model_id == ALLOWED_SUBSTITUTES[0]
        assert "not found" in msg.lower()

    @patch('agents.model_checker.read_plan_md')
    def test_verified_block_missing_pivot(self, mock_read):
        mock_read.return_value = "# Plan\nNo section here."
        success, model_id, msg = verify_model()
        assert success is True
        assert model_id == ALLOWED_SUBSTITUTES[0]
        assert "not found" in msg.lower()
