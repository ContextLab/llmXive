import pytest
import json
import tempfile
from pathlib import Path
from src.plan.verify_alignment import verify_alignment, load_file_text

def test_load_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_file_text(Path("/nonexistent/file.txt"))

def test_load_file_empty():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        temp_path = Path(f.name)
    try:
        with open(temp_path, 'w') as f:
            f.write("")
        with pytest.raises(FileNotFoundError):
            load_file_text(temp_path)
    finally:
        temp_path.unlink()

def test_verify_alignment_pass():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create valid spec and plan with no contradictions
        spec_content = """
        # Spec
        System MUST use eBird data.
        """
        plan_content = """
        # Plan
        We will use eBird data.
        """
        
        spec_path = tmpdir_path / "spec.md"
        plan_path = tmpdir_path / "plan.md"
        
        spec_path.write_text(spec_content)
        plan_path.write_text(plan_content)
        
        result = verify_alignment(spec_path, plan_path)
        assert result["status"] == "PASS"
        assert len(result["final_contradictions"]) == 0

def test_verify_alignment_with_whitelisted_deviation():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Spec says NOAA, Plan says Daymet (Contradiction)
        spec_content = """
        # Spec
        System MUST use NOAA/PRISM data.
        """
        plan_content = """
        # Plan
        We will use Daymet data.
        """
        
        spec_path = tmpdir_path / "spec.md"
        plan_path = tmpdir_path / "plan.md"
        
        spec_path.write_text(spec_content)
        plan_path.write_text(plan_content)
        
        # Create deviation file
        deviation_data = [
            {
                "spec_requirement": "NOAA/PRISM (FR-001)",
                "implemented_source": "Daymet",
                "reason": "Plan explicitly substitutes NOAA/PRISM with Daymet.",
                "timestamp": "2023-10-27T10:00:00Z"
            }
        ]
        deviation_path = tmpdir_path / "deviation.json"
        with open(deviation_path, 'w') as f:
            json.dump(deviation_data, f)
        
        # Should pass because deviation is whitelisted
        result = verify_alignment(spec_path, plan_path, deviation_path)
        assert result["status"] == "PASS"
        assert len(result["final_contradictions"]) == 0

def test_verify_alignment_fails_unwhitelisted():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Spec says NOAA, Plan says Daymet (Contradiction)
        spec_content = """
        # Spec
        System MUST use NOAA/PRISM data.
        """
        plan_content = """
        # Plan
        We will use Daymet data.
        """
        
        spec_path = tmpdir_path / "spec.md"
        plan_path = tmpdir_path / "plan.md"
        
        spec_path.write_text(spec_content)
        plan_path.write_text(plan_content)
        
        # Create empty deviation file (no whitelist)
        deviation_path = tmpdir_path / "deviation.json"
        with open(deviation_path, 'w') as f:
            json.dump([], f)
        
        # Should fail because deviation is NOT whitelisted
        with pytest.raises(RuntimeError) as excinfo:
            verify_alignment(spec_path, plan_path, deviation_path)
        
        assert "Alignment verification failed" in str(excinfo.value)
        assert "NOAA" in str(excinfo.value)
        assert "Daymet" in str(excinfo.value)