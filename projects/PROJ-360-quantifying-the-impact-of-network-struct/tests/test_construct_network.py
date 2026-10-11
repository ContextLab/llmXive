import subprocess
import sys
import tempfile
from pathlib import Path

from pymatgen.core import Lattice, Structure

def test_construct_network_on_simple_structure():
    # Create temporary directories for input CIFs and output networks
    with tempfile.TemporaryDirectory() as tmp_input_dir, tempfile.TemporaryDirectory() as tmp_output_dir:
        input_path = Path(tmp_input_dir)
        output_path = Path(tmp_output_dir)

        # Build a simple NaCl structure and write to CIF
        lattice = Lattice.cubic(5.64)
        species = ["Na", "Cl"]
        coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
        struct = Structure(lattice, species, coords)
        cif_file = input_path / "mp-123.cif"
        struct.to(filename=str(cif_file))

        # Run the construct_network script
        script_path = Path("code") / "construct_network.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--input", str(input_path), "--output", str(output_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        # Ensure the script exited cleanly
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Verify that a pickle file was created
        pickle_files = list(output_path.glob("*.pkl"))
        assert len(pickle_files) == 1, "Expected one network pickle file"

        # Verify that the manifest exists and reports success
        manifest_path = output_path / "network_manifest.json"
        assert manifest_path.is_file(), "Manifest JSON not created"

        import json
        manifest = json.loads(manifest_path.read_text())
        assert manifest["total_processed"] == 1
        assert manifest["successful"] == 1
        assert manifest["errors"] == 0
        entry = manifest["entries"][0]
        assert entry["status"] in ("covalent", "fallback")
        assert entry["nodes"] >= 2
        assert entry["edges"] >= 1