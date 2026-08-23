"""
Unit tests for the artifact verification script (T052).

These tests verify that the ArtifactVerifier class correctly:
1. Finds artifacts in the data directory
2. Parses lineage log entries
3. Verifies artifacts have valid lineage
4. Detects missing lineage entries
5. Detects missing generating scripts
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from verify_artifacts import ArtifactVerifier


class TestArtifactVerifier:
    """Test suite for ArtifactVerifier class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create directory structure
            (project_root / 'data').mkdir()
            (project_root / 'code').mkdir()
            (project_root / 'code' / 'data').mkdir()
            (project_root / 'code' / 'models').mkdir()
            
            # Create some fake artifacts
            (project_root / 'data' / 'test.csv').write_text('a,b\n1,2')
            (project_root / 'data' / 'processed' / 'model.pkl').parent.mkdir(exist_ok=True)
            (project_root / 'data' / 'processed' / 'model.pkl').write_text('fake model')
            
            # Create a lineage log with one valid and one invalid entry
            lineage_content = """2024-01-01T10:00:00 | data/test.csv | code/data/download.py | SUCCESS | Downloaded test data
2024-01-01T10:01:00 | data/processed/model.pkl | code/models/train.py | SUCCESS | Trained model
2024-01-01T10:02:00 | data/missing.csv | code/data/missing.py | SUCCESS | Missing artifact
"""
            (project_root / 'data' / 'lineage.log').write_text(lineage_content)
            
            # Create the generating scripts
            (project_root / 'code' / 'data' / 'download.py').write_text('# download script')
            (project_root / 'code' / 'models' / 'train.py').write_text('# train script')
            
            yield project_root
    
    def test_find_artifacts(self, temp_project):
        """Test that find_artifacts correctly identifies data files."""
        verifier = ArtifactVerifier(temp_project)
        artifacts = verifier.find_artifacts()
        
        assert len(artifacts) == 2  # test.csv and model.pkl
        assert any('test.csv' in str(a) for a in artifacts)
        assert any('model.pkl' in str(a) for a in artifacts)
    
    def test_parse_lineage_log(self, temp_project):
        """Test that parse_lineage_log correctly extracts entries."""
        verifier = ArtifactVerifier(temp_project)
        lineage_data = verifier.parse_lineage_log()
        
        assert len(lineage_data) == 3
        assert Path('data/test.csv') in lineage_data
        assert lineage_data[Path('data/test.csv')]['generated_by'] == 'code/data/download.py'
        assert lineage_data[Path('data/test.csv')]['status'] == 'SUCCESS'
    
    def test_verify_script_exists(self, temp_project):
        """Test that verify_script_exists correctly identifies existing scripts."""
        verifier = ArtifactVerifier(temp_project)
        
        # Valid script
        assert verifier.verify_script_exists('code/data/download.py') is True
        
        # Invalid script
        assert verifier.verify_script_exists('code/nonexistent.py') is False
    
    def test_verify_artifact_valid(self, temp_project):
        """Test verification of a valid artifact."""
        verifier = ArtifactVerifier(temp_project)
        lineage_data = verifier.parse_lineage_log()
        
        artifact_path = Path('data/test.csv')
        is_verified, error_msg = verifier.verify_artifact(artifact_path, lineage_data)
        
        assert is_verified is True
        assert error_msg is None
    
    def test_verify_artifact_missing_lineage(self, temp_project):
        """Test verification of an artifact with no lineage entry."""
        verifier = ArtifactVerifier(temp_project)
        lineage_data = verifier.parse_lineage_log()
        
        artifact_path = Path('data/nonexistent.csv')
        is_verified, error_msg = verifier.verify_artifact(artifact_path, lineage_data)
        
        assert is_verified is False
        assert "No lineage entry found" in error_msg
    
    def test_verify_artifact_missing_script(self, temp_project):
        """Test verification of an artifact with missing generating script."""
        # Create a lineage entry for a non-existent script
        lineage_content = """2024-01-01T10:00:00 | data/test.csv | code/data/nonexistent.py | SUCCESS | Downloaded test data
"""
        (temp_project / 'data' / 'lineage.log').write_text(lineage_content)
        
        verifier = ArtifactVerifier(temp_project)
        lineage_data = verifier.parse_lineage_log()
        
        artifact_path = Path('data/test.csv')
        is_verified, error_msg = verifier.verify_artifact(artifact_path, lineage_data)
        
        assert is_verified is False
        assert "Generating script" in error_msg
    
    def test_run_verification(self, temp_project):
        """Test the full verification process."""
        verifier = ArtifactVerifier(temp_project)
        success = verifier.run_verification()
        
        # Should succeed since all artifacts are properly linked
        assert success is True
    
    def test_generate_report(self, temp_project):
        """Test that generate_report produces a valid report."""
        verifier = ArtifactVerifier(temp_project)
        verifier.run_verification()
        
        report = verifier.generate_report()
        
        assert "ARTIFACT VERIFICATION REPORT" in report
        assert "Total Artifacts Found" in report
        assert "Artifacts Verified" in report
        assert "Constitution Principle IV" in report

if __name__ == '__main__':
    pytest.main([__file__, '-v'])