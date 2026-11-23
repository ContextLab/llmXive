"""
Tests for GFM Wrapper.
"""
import os
import tempfile
import unittest

import numpy as np
import torch

from code.gfm_wrapper import GFMWrapper
from utils import set_deterministic_seed


class TestGFMWrapper(unittest.TestCase):
    """Unit tests for the GFMWrapper class."""

    def setUp(self):
        """Set up test fixtures."""
        set_deterministic_seed(42)
        self.obs_dim = 128
        self.latent_dim = 64
        self.action_dim = 12
        self.test_obs = np.random.randn(self.obs_dim).astype(np.float32)
        self.test_solver_output = np.random.randn(16).astype(np.float32)

    def test_initialization(self):
        """Test that the wrapper initializes correctly."""
        wrapper = GFMWrapper(device="cpu")
        self.assertIsNotNone(wrapper.model)
        self.assertEqual(wrapper.device.type, "cpu")
        self.assertTrue(wrapper.model.training == False)  # eval mode

    def test_encode_observation(self):
        """Test encoding of observation to latent space."""
        wrapper = GFMWrapper(device="cpu")
        latent = wrapper.encode_observation(self.test_obs)

        self.assertIsInstance(latent, torch.Tensor)
        self.assertEqual(latent.shape[-1], wrapper.latent_dim)
        self.assertFalse(torch.isnan(latent).any())

    def test_decode_action(self):
        """Test decoding from latent and solver output to action."""
        wrapper = GFMWrapper(device="cpu")
        latent = wrapper.encode_observation(self.test_obs)
        action = wrapper.decode_action(latent, torch.from_numpy(self.test_solver_output))

        self.assertIsInstance(action, torch.Tensor)
        self.assertEqual(action.shape[-1], wrapper.action_dim)
        self.assertFalse(torch.isnan(action).any())

    def test_encode_and_decode_pipeline(self):
        """Test the full encode -> decode pipeline."""
        wrapper = GFMWrapper(device="cpu")
        action = wrapper.encode_and_decode(self.test_obs, self.test_solver_output)

        self.assertIsInstance(action, torch.Tensor)
        self.assertEqual(action.shape[-1], wrapper.action_dim)

    def test_integrity_check(self):
        """Test model integrity verification."""
        wrapper = GFMWrapper(device="cpu")
        self.assertTrue(wrapper.verify_integrity())

    def test_model_hash(self):
        """Test model hash generation."""
        wrapper = GFMWrapper(device="cpu")
        hash1 = wrapper.get_model_hash()
        hash2 = wrapper.get_model_hash()

        self.assertEqual(hash1, hash2)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex length

    def test_device_placement(self):
        """Test that model moves to correct device."""
        wrapper = GFMWrapper(device="cpu")
        # Check parameters are on CPU
        for param in wrapper.model.parameters():
            self.assertEqual(param.device.type, "cpu")

    def test_batch_processing(self):
        """Test processing a batch of observations."""
        wrapper = GFMWrapper(device="cpu")
        batch_obs = np.random.randn(4, self.obs_dim).astype(np.float32)
        batch_solver = np.random.randn(4, 16).astype(np.float32)

        latent = wrapper.encode_observation(batch_obs)
        action = wrapper.decode_action(latent, torch.from_numpy(batch_solver))

        self.assertEqual(latent.shape[0], 4)
        self.assertEqual(action.shape[0], 4)