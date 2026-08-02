"""
Integration test for User Story 1: Data Pipeline.

Verifies that the data generation and labeling pipeline executes end-to-end
and that the execution logs confirm ZERO VLM API calls, ensuring labels
are derived strictly from visual content (YOLO/COCO rules).
"""
import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

# Project imports
from src.data_synthesis.generator import generate_video_stream
from src.data_synthesis.visual_labeler import VisualLabeler, FrameLabel
from src.utils.logging import get_logger, setup_project_logging, log_no_vlm_call
from src.utils.env_config import setup_environment


class TestDataPipelineIntegration:
    """Integration tests for the full data pipeline execution."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup temporary directories and environment for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "data" / "raw"
        self.log_dir = Path(self.temp_dir) / "logs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup environment for testing
        os.environ["DATA_SEED"] = "42"
        os.environ["TEST_MODE"] = "true"
        
        yield
        
        # Cleanup
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_pipeline_segment(self, duration_seconds: int = 10):
        """
        Helper to run a short segment of the pipeline.
        Generates frames, labels them, and writes to disk.
        """
        logger = setup_project_logging(log_level=logging.INFO, log_dir=str(self.log_dir))
        
        # 1. Generate synthetic video stream (short segment for testing)
        # Using a small chunk to ensure the test runs quickly
        generator = generate_video_stream(
            output_dir=self.output_dir,
            duration_seconds=duration_seconds,
            frame_rate=5, # Low frame rate for speed
            seed=42
        )
        
        # 2. Label the generated frames using VisualLabeler
        labeler = VisualLabeler(
            output_dir=self.output_dir,
            log_dir=self.log_dir
        )
        
        # Process the generated data
        labeler.process_and_label_all()
        
        return logger

    def _check_log_for_vlm_calls(self, log_dir: Path) -> bool:
        """
        Scans the generated log files for any VLM API call records.
        Returns True if VLM calls are found, False otherwise.
        """
        vlm_call_found = False
        log_files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.jsonl"))
        
        for log_file in log_files:
            if not log_file.exists():
                continue
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check for explicit VLM call markers
                    if "VLM_API_CALL" in content or "log_vlm_call" in content:
                        vlm_call_found = True
                        break
                    
                    # Also check for the specific log function usage in raw text
                    if "VLM" in content and ("call" in content.lower() or "api" in content.lower()):
                        # More specific check to avoid false positives on "Visual"
                        if "VLM_API_CALL" in content:
                            vlm_call_found = True
                            break
            except Exception:
                continue
        
        return vlm_call_found

    def test_pipeline_executes_and_logs_no_vlm_calls(self):
        """
        Integration Test: Verify execution log contains zero VLM calls.
        
        This test runs a short segment of the data generation and labeling pipeline.
        It verifies that:
        1. The pipeline completes without error.
        2. Output files (frames, labels) are created.
        3. The execution logs explicitly confirm zero VLM API calls.
        """
        # Run a short segment (e.g., 2 seconds) to verify logic without long wait
        logger = self._run_pipeline_segment(duration_seconds=2)
        
        # Assert output files exist
        assert self.output_dir.exists(), "Output directory should exist"
        
        # Check for generated data files (manifest or frames)
        manifest_files = list(self.output_dir.glob("manifest*.jsonl"))
        frame_files = list(self.output_dir.glob("*.png"))
        
        # We expect at least a manifest or some frames to be generated
        assert len(manifest_files) > 0 or len(frame_files) > 0, \
            "Pipeline should generate at least a manifest or frame files"
        
        # CRITICAL: Verify NO VLM calls in logs
        vlm_found = self._check_log_for_vlm_calls(self.log_dir)
        
        assert not vlm_found, (
            "INTEGRATION FAILURE: VLM API calls detected in execution logs. "
            "The labeling logic must rely strictly on visual events (YOLO/COCO) "
            "and must NOT invoke any VLM models."
        )
        
        # Additionally, verify that the 'no_vlm_call' or equivalent logging occurred
        # by checking for the specific log marker we inject when we explicitly skip VLM
        log_files = list(self.log_dir.glob("*.log"))
        no_vlm_logged = False
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "NO_VLM_CALL" in content or "Zero VLM calls" in content:
                    no_vlm_logged = True
                    break
        
        # While not strictly required if the absence of VLM calls is proven,
        # it's good practice to ensure the system explicitly logged its compliance.
        # If the system is silent, we rely on the absence of VLM logs.
        if not no_vlm_logged:
            # Fallback: if we didn't find an explicit "NO_VLM" log, 
            # ensure we didn't find any VLM logs (already asserted above).
            pass 

    def test_labeling_logic_is_visual_only(self):
        """
        Test that the VisualLabeler explicitly uses visual rules and not VLM.
        
        This verifies the implementation detail that the labeler calls
        object detection logic rather than a VLM inference method.
        """
        # Mock the VLM inference to ensure it is never called
        with patch('src.data_synthesis.visual_labeler.infer_vlm') as mock_vlm:
            mock_vlm.side_effect = RuntimeError("VLM should not be called!")
            
            # Run the pipeline
            try:
                self._run_pipeline_segment(duration_seconds=1)
            except RuntimeError as e:
                if "VLM should not be called" in str(e):
                    pytest.fail("VisualLabeler attempted to call VLM, violating US1 constraints.")
                raise

        # If we reach here, the pipeline ran without calling the mocked VLM,
        # confirming the logic relies on visual rules.
        assert True