"""
Tests for network isolation security hardening.

These tests verify that:
1. The network isolation context manager blocks socket connections
2. Module imports are validated correctly
3. The decorator prevents network calls
4. Static analysis detects potential external calls
"""
import pytest
import socket
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from security.network_isolation import (
    NetworkIsolationContext,
    ensure_no_network_access,
    validate_no_external_calls,
    audit_all_modules,
    SecurityViolationError,
    _check_module_import,
    ALLOWED_MODULES,
    BLOCKED_MODULES
)

class TestNetworkIsolationContext:
    """Tests for the NetworkIsolationContext context manager."""
    
    def test_blocks_socket_connections(self):
        """Test that socket connections are blocked when isolation is active."""
        with NetworkIsolationContext():
            with pytest.raises(SecurityViolationError) as exc_info:
                # Try to create a socket connection
                sock = socket.socket()
                sock.connect(('example.com', 80))
            
            assert "Network isolation active" in str(exc_info.value)
    
    def test_allows_socket_connections_outside_context(self):
        """Test that socket connections work outside the isolation context."""
        # This test should not raise an exception
        # We just verify the context manager properly restores state
        sock = socket.socket()
        # Don't actually connect, just verify socket creation works
        sock.close()
    
    def test_restores_state_on_exit(self):
        """Test that the context manager restores original state on exit."""
        original_connect = socket.socket.connect
        
        with NetworkIsolationContext():
            # Inside context, connect should be patched
            assert socket.socket.connect != original_connect
        
        # After exit, connect should be restored
        assert socket.socket.connect == original_connect

class TestEnsureNoNetworkAccessDecorator:
    """Tests for the ensure_no_network_access decorator."""
    
    def test_blocks_network_calls_in_decorated_function(self):
        """Test that decorated functions cannot make network calls."""
        
        @ensure_no_network_access
        def function_with_network_call():
            sock = socket.socket()
            sock.connect(('example.com', 80))
            return True
        
        with pytest.raises(SecurityViolationError):
            function_with_network_call()
    
    def test_allows_normal_execution(self):
        """Test that decorated functions can execute normally without network calls."""
        
        @ensure_no_network_access
        def function_without_network_call():
            return "success"
        
        result = function_without_network_call()
        assert result == "success"

class TestValidateNoExternalCalls:
    """Tests for static analysis of external calls."""
    
    def test_detects_requests_import(self):
        """Test detection of requests import."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import requests\n")
            f.write("requests.get('http://example.com')\n")
            temp_path = Path(f.name)
        
        try:
            result = validate_no_external_calls(temp_path)
            assert result is False
        finally:
            temp_path.unlink()
    
    def test_detects_urllib_import(self):
        """Test detection of urllib import."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from urllib.request import urlopen\n")
            f.write("urlopen('http://example.com')\n")
            temp_path = Path(f.name)
        
        try:
            result = validate_no_external_calls(temp_path)
            assert result is False
        finally:
            temp_path.unlink()
    
    def test_allows_safe_modules(self):
        """Test that safe modules pass validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import json\n")
            f.write("import os\n")
            f.write("data = json.dumps({'key': 'value'})\n")
            temp_path = Path(f.name)
        
        try:
            result = validate_no_external_calls(temp_path)
            assert result is True
        finally:
            temp_path.unlink()
    
    def test_handles_nonexistent_file(self):
        """Test handling of nonexistent file."""
        result = validate_no_external_calls(Path('/nonexistent/file.py'))
        assert result is False

class TestCheckModuleImport:
    """Tests for module import checking."""
    
    def test_allows_allowed_modules(self):
        """Test that allowed modules pass the check."""
        # Should not raise
        _check_module_import('json')
        _check_module_import('numpy')
        _check_module_import('pandas')
    
    def test_blocks_blocked_modules_when_isolated(self):
        """Test that blocked modules are blocked when isolation is active."""
        with NetworkIsolationContext():
            with pytest.raises(SecurityViolationError):
                _check_module_import('requests')
            
            with pytest.raises(SecurityViolationError):
                _check_module_import('urllib3')
    
    def test_allows_blocked_modules_when_not_isolated(self):
        """Test that blocked modules are allowed when isolation is not active."""
        # Should not raise when not in isolation context
        _check_module_import('requests')
        _check_module_import('urllib3')

class TestAuditAllModules:
    """Tests for the full module audit function."""
    
    def test_audits_project_modules(self):
        """Test that the audit function finds and checks modules."""
        # Create a temporary project structure
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create a safe module
            safe_module = project_root / 'code' / 'safe_module.py'
            safe_module.parent.mkdir(parents=True)
            safe_module.write_text("import json\nimport os\n")
            
            # Create an unsafe module
            unsafe_module = project_root / 'code' / 'unsafe_module.py'
            unsafe_module.write_text("import requests\n")
            
            results = audit_all_modules(project_root)
            
            assert len(results['audited_files']) >= 2
            assert len(results['safe_files']) >= 1
            assert len(results['unsafe_files']) >= 1

class TestSecurityConstants:
    """Tests for security-related constants."""
    
    def test_allowed_modules_contains_common_safe_modules(self):
        """Test that allowed modules include common safe modules."""
        required_modules = ['json', 'os', 'sys', 'random', 'pathlib', 'typing']
        for module in required_modules:
            assert module in ALLOWED_MODULES
    
    def test_blocked_modules_contains_common_network_modules(self):
        """Test that blocked modules include common network modules."""
        required_modules = ['requests', 'urllib3', 'http.client', 'aiohttp']
        for module in required_modules:
            assert module in BLOCKED_MODULES

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
