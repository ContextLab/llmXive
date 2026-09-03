import json
import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.generate_schemas import main

class TestSchemaGeneration(unittest.TestCase):
    def test_schemas_generated(self):
        """Test that the generate_schemas script creates the required files."""
        # Run the main function to ensure files are created
        base_dir = Path(__file__).parent.parent.parent
        contracts_dir = base_dir / "contracts"

        # Ensure directory exists for the test context
        contracts_dir.mkdir(parents=True, exist_ok=True)

        # Call main
        result = main()
        self.assertEqual(result, 0)

        # Check files exist
        expected_files = [
            "PaperManifest.schema.yaml",
            "ReproResult.schema.yaml",
            "StatSummary.schema.yaml"
        ]

        for filename in expected_files:
            filepath = contracts_dir / filename
            self.assertTrue(filepath.exists(), f"File {filepath} was not generated.")
            self.assertGreater(filepath.stat().st_size, 0, f"File {filepath} is empty.")

    def test_schema_content_validity(self):
        """Basic check that generated files contain expected schema markers."""
        base_dir = Path(__file__).parent.parent.parent
        contracts_dir = base_dir / "contracts"

        # Re-run to ensure fresh files
        main()

        expected_markers = {
            "PaperManifest.schema.yaml": "title: PaperManifest",
            "ReproResult.schema.yaml": "title: ReproResult",
            "StatSummary.schema.yaml": "title: StatSummary"
        }

        for filename, marker in expected_markers.items():
            filepath = contracts_dir / filename
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(marker, content, f"File {filename} missing expected marker: {marker}")
                self.assertIn("$schema:", content, f"File {filename} missing $schema definition.")

if __name__ == "__main__":
    unittest.main()