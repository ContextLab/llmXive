import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from review_physical_claims import check_physical_claims, load_file_content, load_json_content

class TestPhysicalClaimsReview:
    
    def test_supported_claims(self):
        """Test that a report with proper invariance section and data is considered supported."""
        
        # Create a mock report with a claim and a reference
        mock_report = """
        # Analysis Report
        
        ## Physical Invariance Verification
        
        The critical coupling strength $K_c$ is an element of physical reality,
        independent of the observer's coordinate frame. This is confirmed by T026.
        
        ### Results
        All topologies are invariant.
        """
        
        # Create a mock invariance data
        mock_data = [
            {"topology_id": "1", "status": "invariant", "p": 0.1},
            {"topology_id": "2", "status": "invariant", "p": 0.5}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.md"
            data_path = Path(tmpdir) / "data.json"
            
            report_path.write_text(mock_report)
            with open(data_path, 'w') as f:
                json.dump(mock_data, f)
            
            supported, unsupported, refs = check_physical_claims(str(report_path), str(data_path))
            
            assert supported is True
            assert len(unsupported) == 0
            assert len(refs) > 0

    def test_missing_invariance_section(self):
        """Test that a report claiming physical reality without the section fails."""
        
        mock_report = """
        # Analysis Report
        
        The critical coupling strength $K_c$ is an element of physical reality.
        """
        
        mock_data = [
            {"topology_id": "1", "status": "invariant"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.md"
            data_path = Path(tmpdir) / "data.json"
            
            report_path.write_text(mock_report)
            with open(data_path, 'w') as f:
                json.dump(mock_data, f)
            
            supported, unsupported, refs = check_physical_claims(str(report_path), str(data_path))
            
            assert supported is False
            assert any("lacks 'Physical Invariance Verification' section" in u for u in unsupported)

    def test_variant_topology(self):
        """Test that a report fails if invariance data contains a variant topology."""
        
        mock_report = """
        # Analysis Report
        
        ## Physical Invariance Verification
        
        The critical coupling strength $K_c$ is an element of physical reality.
        """
        
        mock_data = [
            {"topology_id": "1", "status": "invariant"},
            {"topology_id": "2", "status": "variant"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.md"
            data_path = Path(tmpdir) / "data.json"
            
            report_path.write_text(mock_report)
            with open(data_path, 'w') as f:
                json.dump(mock_data, f)
            
            supported, unsupported, refs = check_physical_claims(str(report_path), str(data_path))
            
            assert supported is False
            assert any("not all topologies are marked 'invariant'" in u for u in unsupported)

    def test_missing_reference(self):
        """Test that a report with claims but no explicit references fails."""
        
        mock_report = """
        # Analysis Report
        
        ## Physical Invariance Verification
        
        The critical coupling strength $K_c$ is an element of physical reality.
        
        ### Results
        All topologies are invariant.
        """
        
        mock_data = [
            {"topology_id": "1", "status": "invariant"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.md"
            data_path = Path(tmpdir) / "data.json"
            
            report_path.write_text(mock_report)
            with open(data_path, 'w') as f:
                json.dump(mock_data, f)
            
            supported, unsupported, refs = check_physical_claims(str(report_path), str(data_path))
            
            # This should fail because there are no explicit references like T026 or invariance_verification
            assert supported is False
            assert any("contains no explicit references" in u for u in unsupported)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])