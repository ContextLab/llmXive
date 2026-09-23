"""
Contract test for output directory structure.
Verifies that the output directory structure matches the specification.
"""
import os
import pytest
from pathlib import Path
import tempfile
import subprocess
import sys

def test_output_directory_structure_contract():
    """
    Contract test: Verify output directory structure matches specification.
    
    Specification requires:
        - output/
        - output/figures/
        - output/reports/
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        code_dir = temp_path / "code"
        code_dir.mkdir()
        
        # Copy script
        script_content = (Path(__file__).parent.parent.parent / "code" / "create_output_dirs.py").read_text()
        (code_dir / "create_output_dirs.py").write_text(script_content)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_path)
            
            # Execute script
            subprocess.run(
                [sys.executable, str(code_dir / "create_output_dirs.py")],
                capture_output=True,
                check=True
            )
            
            # Contract assertions
            output_root = temp_path / "output"
            assert output_root.exists(), "Contract violation: output/ directory missing"
            assert output_root.is_dir(), "Contract violation: output/ is not a directory"
            
            figures_dir = output_root / "figures"
            assert figures_dir.exists(), "Contract violation: output/figures/ directory missing"
            assert figures_dir.is_dir(), "Contract violation: output/figures/ is not a directory"
            
            reports_dir = output_root / "reports"
            assert reports_dir.exists(), "Contract violation: output/reports/ directory missing"
            assert reports_dir.is_dir(), "Contract violation: output/reports/ is not a directory"
            
            # Additional contract: no unexpected files in root output
            items = list(output_root.iterdir())
            expected_items = {figures_dir.name, reports_dir.name}
            actual_items = {item.name for item in items}
            
            assert actual_items == expected_items, (
                f"Contract violation: unexpected items in output/: {actual_items - expected_items}"
            )
            
        finally:
            os.chdir(original_cwd)
