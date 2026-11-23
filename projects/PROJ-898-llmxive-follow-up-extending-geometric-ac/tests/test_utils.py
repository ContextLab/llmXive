"""
Unit tests for code/utils.py utilities.
"""
import logging
import os
import tempfile
import hashlib

import numpy as np
import pytest
import torch

from code.utils import setup_logging, set_deterministic_seed, compute_sha256


class TestSetupLogging:
    def test_console_handler_added(self):
        logger = setup_logging(log_level=logging.DEBUG)
        assert len(logger.handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_file_handler_added(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp:
            tmp_path = tmp.name

        try:
            logger = setup_logging(log_file=tmp_path)
            assert len(logger.handlers) >= 2
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        finally:
            os.unlink(tmp_path)


class TestSetDeterministicSeed:
    def test_seeds_are_set(self):
        seed = 12345
        set_deterministic_seed(seed)
        assert random.getstate()[1][0] is not None  # Python random state exists
        assert np.random.get_state()[1][0] is not None  # NumPy state exists
        assert torch.get_rng_state() is not None  # Torch state exists


class TestComputeSha256:
    def test_hash_matches_known_value(self):
        content = b"Hello, world!"
        expected = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = compute_sha256(tmp_path)
            assert result == expected
        finally:
            os.unlink(tmp_path)

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/file.txt")