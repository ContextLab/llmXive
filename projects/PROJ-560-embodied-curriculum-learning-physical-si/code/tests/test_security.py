import os
import json
import tempfile
import pytest
from pathlib import Path
import yaml
from src.security import (
    sanitize_path, 
    safe_load_json, 
    safe_load_csv, 
    safe_load_yaml,
    SecurityError,
    PathTraversalError
)


class TestSecurityPathSanitization:
    """Tests for path sanitization."""
    
    def test_sanitize_basic(self):
        """Test basic sanitization."""
        clean = sanitize_path("data/test.csv")
        assert clean == "data/test.csv"
        
    def test_sanitize_traversal(self):
        """Test traversal prevention."""
        try:
            dirty = sanitize_path("../../etc/passwd")
            # Should raise or clean
            assert ".." not in dirty
        except SecurityError:
            pass


class TestSecureYamlLoading:
    """Tests for secure YAML loading."""
    
    def test_safe_yaml(self):
        """Test safe YAML loading."""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write("key: value")
            data = safe_load_yaml(path)
            assert data["key"] == "value"
        finally:
            os.remove(path)


class TestSecureJsonLoading:
    """Tests for secure JSON loading."""
    
    def test_safe_json(self):
        """Test safe JSON loading."""
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write('{"key": "value"}')
            data = safe_load_json(path)
            assert data["key"] == "value"
        finally:
            os.remove(path)


class TestSecureCsvLoading:
    """Tests for secure CSV loading."""
    
    def test_safe_csv(self):
        """Test safe CSV loading."""
        fd, path = tempfile.mkstemp(suffix='.csv')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write("a,b\n1,2")
            data = safe_load_csv(path)
            assert len(data) == 1
        finally:
            os.remove(path)


class TestSchemaValidation:
    """Tests for schema validation."""
    
    def test_validate(self):
        """Test basic validation."""
        # Placeholder for schema validation logic
        pass


class TestUnifiedSecureLoader:
    """Tests for unified secure loading."""
    
    def test_unified(self):
        """Test unified loading."""
        # Placeholder for unified loader
        pass