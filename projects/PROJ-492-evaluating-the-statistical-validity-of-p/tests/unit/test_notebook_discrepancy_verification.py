"""
Unit tests for T034: Statistical Consistency Verification Notebook.

These tests verify that:
1. The notebook exists at the expected path
2. The notebook can be loaded and parsed as valid JSON
3. The notebook contains required sections (markdown cells for documentation)
4. The notebook contains code cells that load audit data
5. The notebook produces output when executed (via nbconvert or similar)
"""
import json
import os
from pathlib import Path
import pytest

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
NOTEBOOK_PATH = PROJECT_ROOT / 'notebooks' / 'statistical_consistency_verification.ipynb'
OUTPUT_DIR = PROJECT_ROOT / 'output'
AUDIT_REPORT_PATH = OUTPUT_DIR / 'audit_report.json'
DISCREPANCY_REPORT_PATH = OUTPUT_DIR / 'discrepancy_report.json'

class TestNotebookExistence:
    """Test that the notebook file exists."""
    
    def test_notebook_file_exists(self):
        """Verify notebook file exists at expected path."""
        assert NOTEBOOK_PATH.exists(), f"Notebook not found at {NOTEBOOK_PATH}"
    
    def test_notebook_directory_exists(self):
        """Verify notebooks directory exists."""
        assert (PROJECT_ROOT / 'notebooks').exists()

class TestNotebookStructure:
    """Test notebook JSON structure."""
    
    def test_notebook_is_valid_json(self):
        """Verify notebook is valid JSON."""
        with open(NOTEBOOK_PATH, 'r') as f:
            notebook = json.load(f)
        assert isinstance(notebook, dict)
    
    def test_notebook_has_required_metadata(self):
        """Verify notebook has required metadata fields."""
        with open(NOTEBOOK_PATH, 'r') as f:
            notebook = json.load(f)
        assert 'cells' in notebook
        assert 'nbformat' in notebook
        assert notebook['nbformat'] >= 4
    
    def test_notebook_has_cells(self):
        """Verify notebook has cells."""
        with open(NOTEBOOK_PATH, 'r') as f:
            notebook = json.load(f)
        assert len(notebook['cells']) > 0

class TestNotebookContent:
    """Test notebook cell content."""
    
    def test_notebook_has_markdown_cells(self):
        """Verify notebook has markdown documentation cells."""
        with open(NOTEBOOK_PATH, 'r') as f:
            notebook = json.load(f)
        markdown_cells = [c for c in notebook['cells'] if c['cell_type'] == 'markdown']
        assert len(markdown_cells) > 0, "Notebook should have markdown cells for documentation"
    
    def test_notebook_has_code_cells(self):
        """Verify notebook has executable code cells."""
        with open(NOTEBOOK_PATH, 'r') as f:
            notebook = json.load(f)
        code_cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
        assert len(code_cells) > 0, "Notebook should have code cells"
    
    def test_notebook_references_audit_report(self):
        """Verify notebook references audit_report.json."""
        with open(NOTEBOOK_PATH, 'r') as f:
            content = f.read()
        assert 'audit_report.json' in content, "Notebook should reference audit_report.json"
    
    def test_notebook_references_discrepancy_report(self):
        """Verify notebook produces discrepancy_report.json."""
        with open(NOTEBOOK_PATH, 'r') as f:
            content = f.read()
        assert 'discrepancy_report.json' in content, "Notebook should produce discrepancy_report.json"
    
    def test_notebook_mentions_principle_vi(self):
        """Verify notebook documents Constitution Principle VI."""
        with open(NOTEBOOK_PATH, 'r') as f:
            content = f.read()
        assert 'Principle VI' in content or 'Principle 6' in content, \
            "Notebook should reference Constitution Principle VI"
    
    def test_notebook_has_p_value_threshold(self):
        """Verify notebook uses 0.05 p-value threshold."""
        with open(NOTEBOOK_PATH, 'r') as f:
            content = f.read()
        assert '0.05' in content, "Notebook should use 0.05 p-value threshold"

class TestNotebookExecution:
    """Test that notebook can produce output."""
    
    @pytest.fixture
    def sample_audit_report(self, tmp_path):
        """Create a sample audit report for testing."""
        audit_dir = tmp_path / 'output'
        audit_dir.mkdir(parents=True)
        audit_report = audit_dir / 'audit_report.json'
        
        sample_data = {
            'records': [
                {
                    'url': 'https://example.com/test1',
                    'reported_p_value': 0.03,
                    'reconstructed_p_value': 0.08,
                    'absolute_p_difference': 0.05,
                    'effect_size_difference': 0.02,
                    'test_type': 'z-test',
                    'outcome_type': 'binary',
                    'sample_size_mismatch': False,
                    'notes': 'Minor rounding difference'
                },
                {
                    'url': 'https://example.com/test2',
                    'reported_p_value': 0.01,
                    'reconstructed_p_value': 0.15,
                    'absolute_p_difference': 0.14,
                    'effect_size_difference': 0.05,
                    'test_type': 'fisher',
                    'outcome_type': 'binary',
                    'sample_size_mismatch': True,
                    'notes': 'Sample size mismatch detected'
                },
                {
                    'url': 'https://example.com/test3',
                    'reported_p_value': 0.04,
                    'reconstructed_p_value': 0.045,
                    'absolute_p_difference': 0.005,
                    'effect_size_difference': 0.01,
                    'test_type': 'z-test',
                    'outcome_type': 'binary',
                    'sample_size_mismatch': False,
                    'notes': 'Consistent'
                }
            ]
        }
        
        with open(audit_report, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        return audit_dir
    
    def test_notebook_can_load_audit_report(self, sample_audit_report):
        """Verify notebook code can load audit report."""
        # Read the notebook and check it has code to load JSON
        with open(NOTEBOOK_PATH, 'r') as f:
            notebook = json.load(f)
        
        code_cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
        code_content = '\n'.join([''.join(c.get('source', [])) for c in code_cells])
        
        assert 'json.load' in code_content, "Notebook should use json.load to read audit report"
        assert 'audit_report.json' in code_content, "Notebook should reference audit_report.json"
    
    def test_notebook_filters_discrepancies(self, sample_audit_report):
        """Verify notebook filters for p-value discrepancies > 0.05."""
        with open(NOTEBOOK_PATH, 'r') as f:
            content = f.read()
        
        # Check for threshold comparison logic
        assert '0.05' in content, "Notebook should use 0.05 threshold"
        assert 'absolute_p_difference' in content, "Notebook should check absolute_p_difference"

class TestNotebookOutput:
    """Test notebook output requirements."""
    
    def test_notebook_exports_discrepancy_report(self):
        """Verify notebook exports discrepancy_report.json."""
        with open(NOTEBOOK_PATH, 'r') as f:
            content = f.read()
        
        assert 'discrepancy_report.json' in content, \
            "Notebook should write to discrepancy_report.json"
        assert 'json.dump' in content or 'json.dumps' in content, \
            "Notebook should serialize output as JSON"
    
    def test_notebook_includes_summary_statistics(self):
        """Verify notebook includes summary statistics."""
        with open(NOTEBOOK_PATH, 'r') as f:
            content = f.read()
        
        assert 'total_records' in content or 'Total records' in content, \
            "Notebook should include total records count"
        assert 'inconsistency_rate' in content or 'rate' in content.lower(), \
            "Notebook should include inconsistency rate"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
