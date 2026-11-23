import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

class TestBaselineIsolation:
    """Test that baseline agent does not access signature index."""
    
    def test_no_signature_access(self):
        """Assert that baseline agent code does not import or access failure_signatures.json."""
        from agents.baseline import BaselineAgent
        
        # Check that BaselineAgent does not reference the signature index file
        baseline_source = open(Path('code/agents/baseline.py')).read()
        
        # Verify no import of failure_signatures
        assert 'failure_signatures' not in baseline_source, \
            "Baseline agent should not access failure_signatures.json"
        
        # Verify no reference to data/derived/failure_signatures.json
        assert 'data/derived/failure_signatures.json' not in baseline_source, \
            "Baseline agent should not access failure_signatures.json"
    
    def test_augmented_agent_uses_signature(self):
        """Assert that augmented agent does access signature index."""
        from agents.augmented import AugmentedAgent
        
        augmented_source = open(Path('code/agents/augmented.py')).read()
        
        # Verify it does reference the signature index
        assert 'signature_index' in augmented_source, \
            "Augmented agent should use signature index"
