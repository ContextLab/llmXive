import unittest
from pathlib import Path
from code.setup_structure import main

class TestSetupStructure(unittest.TestCase):

    def test_directory_creation(self):
        base_dir = Path(".")
        data_dir = base_dir / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        explanation_tiers_dir = data_dir / "explanation_tiers"
        simulation_results_dir = data_dir / "simulation_results"
        code_dir = base_dir / "code"
        tests_dir = base_dir / "tests"
        docs_dir = base_dir / "docs"

        # Clean up before test (optional, but good practice)
        for dir in [data_dir, raw_dir, processed_dir, explanation_tiers_dir, simulation_results_dir, code_dir, tests_dir, docs_dir]:
            if dir.exists():
                import shutil
                shutil.rmtree(dir)

        main()

        self.assertTrue(data_dir.exists())
        self.assertTrue(raw_dir.exists())
        self.assertTrue(processed_dir.exists())
        self.assertTrue(explanation_tiers_dir.exists())
        self.assertTrue(simulation_results_dir.exists())
        self.assertTrue(code_dir.exists())
        self.assertTrue(tests_dir.exists())
        self.assertTrue(docs_dir.exists())

if __name__ == '__main__':
    unittest.main()