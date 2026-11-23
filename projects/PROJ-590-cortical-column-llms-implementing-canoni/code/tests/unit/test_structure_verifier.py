"""
Unit tests for the structure verifier (T069).
"""

import pytest
import torch
import torch.nn as nn
from unittest.mock import patch, MagicMock

from src.models.microcircuit import (
    MicrocircuitColumn,
    MicrocircuitColumnConfig,
    create_microcircuit_column,
    L23Layer
)
from src.utils.structure_verifier import verify_canonical_topology, _analyze_weights

class TestStructureVerifier:
    
    def test_verify_canonical_topology_passes(self):
        """
        Test that a correctly configured MicrocircuitColumn passes verification.
        """
        config = MicrocircuitColumnConfig(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            num_columns=1
        )
        column = create_microcircuit_column(config)
        
        # This should not raise
        result = verify_canonical_topology(column)
        assert result is True

    def test_verify_ei_ratio_deviation(self):
        """
        Test that a column with incorrect E/I ratio fails verification.
        We simulate this by mocking the _analyze_weights function to return
        a skewed ratio.
        """
        config = MicrocircuitColumnConfig(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            num_columns=1
        )
        column = create_microcircuit_column(config)
        
        # Mock _analyze_weights to return 100 excitatory and 1 inhibitory
        # Ratio = 100, Expected = 4, Tolerance = 5% -> 4 * 1.05 = 4.2
        # 100 > 4.2, so it should fail.
        with patch('src.utils.structure_verifier._analyze_weights') as mock_weights:
            mock_weights.return_value = (100, 1)
            
            with pytest.raises(AssertionError) as exc_info:
                verify_canonical_topology(column)
            
            assert "E/I ratio" in str(exc_info.value)

    def test_verify_missing_layer(self):
        """
        Test that a column missing a required layer fails verification.
        """
        config = MicrocircuitColumnConfig(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            num_columns=1
        )
        column = create_microcircuit_column(config)
        
        # Remove the L23 layer to simulate a missing component
        delattr(column, 'l23_layer')
        
        with pytest.raises(AssertionError) as exc_info:
            verify_canonical_topology(column)
        
        assert "Missing L4 or L23" in str(exc_info.value)

    def test_analyze_weights_positive_negative(self):
        """
        Test the _analyze_weights helper function.
        """
        # Create a simple linear layer
        layer = nn.Linear(10, 10)
        
        # Set specific weights
        with torch.no_grad():
            layer.weight.fill_(0.5) # All positive
            layer.weight[0, 0] = -0.5 # One negative
        
        exc, inh = _analyze_weights(layer, "test")
        
        assert exc == 99 # 100 total - 1 negative
        assert inh == 1

    def test_analyze_weights_zero(self):
        """
        Test _analyze_weights with zero weights.
        """
        layer = nn.Linear(10, 10)
        with torch.no_grad():
            layer.weight.zero_()
        
        exc, inh = _analyze_weights(layer, "test")
        assert exc == 0
        assert inh == 0