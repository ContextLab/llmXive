"""
Integration test for T1205: Verify the full audit pipeline works end-to-end.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

class TestHardcodedPathsIntegration:
    def test_audit_script_runs_successfully(self):
        """Test that the audit script runs without errors."""
        project_root = Path(__file__).parent.parent.parent
        audit_script = project_root / 'code' / 'scripts' / 'audit_hardcoded_paths.py'
        
        assert audit_script.exists(), f"Audit script not found at {audit_script}"
        
        # Run the audit script
        result = subprocess.run(
            ['python', str(audit_script)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Audit script failed: {result.stderr}"
    
    def test_audit_report_is_generated(self):
        """Test that the audit report is generated at the expected location."""
        project_root = Path(__file__).parent.parent.parent
        audit_report = project_root / 'data' / 'processed' / 'audit_hardcoded_paths.json'
        
        # Ensure data/processed directory exists
        audit_report.parent.mkdir(parents=True, exist_ok=True)
        
        # Run the audit script first
        audit_script = project_root / 'code' / 'scripts' / 'audit_hardcoded_paths.py'
        subprocess.run(['python', str(audit_script)], cwd=project_root, check=True)
        
        # Check that the report was generated
        assert audit_report.exists(), f"Audit report not generated at {audit_report}"
        
        # Verify the report is valid JSON
        with open(audit_report, 'r') as f:
            report = json.load(f)
        
        assert 'total_files_audited' in report
        assert 'total_hardcoded_paths_found' in report
        assert 'findings' in report
        assert isinstance(report['findings'], list)
    
    def test_audit_report_contains_expected_fields(self):
        """Test that each finding in the report contains required fields."""
        project_root = Path(__file__).parent.parent.parent
        audit_report = project_root / 'data' / 'processed' / 'audit_hardcoded_paths.json'
        
        # Run the audit script if report doesn't exist
        if not audit_report.exists():
            audit_script = project_root / 'code' / 'scripts' / 'audit_hardcoded_paths.py'
            subprocess.run(['python', str(audit_script)], cwd=project_root, check=True)
        
        with open(audit_report, 'r') as f:
            report = json.load(f)
        
        required_fields = ['file', 'line', 'content', 'matched_string', 'pattern']
        
        for finding in report['findings']:
            for field in required_fields:
                assert field in finding, f"Finding missing required field: {field}"
    
    def test_no_false_positives_in_config_file(self):
        """Test that config.py itself doesn't trigger false positives."""
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / 'code' / 'config.py'
        audit_report = project_root / 'data' / 'processed' / 'audit_hardcoded_paths.json'
        
        # Run the audit script if report doesn't exist
        if not audit_report.exists():
            audit_script = project_root / 'code' / 'scripts' / 'audit_hardcoded_paths.py'
            subprocess.run(['python', str(audit_script)], cwd=project_root, check=True)
        
        with open(audit_report, 'r') as f:
            report = json.load(f)
        
        # Filter findings for config.py
        config_findings = [f for f in report['findings'] if 'config.py' in f['file']]
        
        # Config.py should have very few or no hardcoded path findings
        # since it's the source of truth for paths
        # We allow some findings for documentation strings, but not for actual code
        code_findings = [f for f in config_findings if '"""' not in f['content'] and "'''" not in f['content']]
        
        # This is a sanity check - config.py should not have many hardcoded paths
        # in actual code (not documentation)
        assert len(code_findings) <= 2, f"config.py has too many hardcoded path findings: {code_findings}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])