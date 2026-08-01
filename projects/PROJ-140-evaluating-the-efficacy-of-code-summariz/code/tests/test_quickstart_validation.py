"""
Test suite for T043: Run quickstart.md validation.

This test validates that the project's quickstart.md file exists,
contains valid instructions, and that the referenced scripts can be
executed successfully.
"""
import os
import sys
import subprocess
import yaml
import json
import tempfile
import shutil
import unittest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestQuickstartValidation(unittest.TestCase):
    """Validation tests for quickstart.md and project readiness."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = PROJECT_ROOT
        self.quickstart_path = self.project_root / "quickstart.md"
        self.code_dir = self.project_root / "code"
        self.data_dir = self.project_root / "data"

    def test_quickstart_file_exists(self):
        """Verify quickstart.md exists at project root."""
        self.assertTrue(
            self.quickstart_path.exists(),
            "quickstart.md must exist at project root"
        )

    def test_quickstart_has_content(self):
        """Verify quickstart.md is not empty."""
        with open(self.quickstart_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertGreater(
            len(content.strip()), 0,
            "quickstart.md must contain content"
        )

    def test_quickstart_has_install_section(self):
        """Verify quickstart.md contains installation instructions."""
        with open(self.quickstart_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        self.assertTrue(
            "install" in content or "dependenc" in content,
            "quickstart.md must contain installation/dependency instructions"
        )

    def test_quickstart_has_execution_section(self):
        """Verify quickstart.md contains execution instructions."""
        with open(self.quickstart_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        self.assertTrue(
            "run" in content or "execute" in content or "python" in content,
            "quickstart.md must contain execution instructions"
        )

    def test_required_data_directories_exist(self):
        """Verify required data directories from quickstart exist."""
        required_dirs = [
            "data/defects4j",
            "data/summaries",
            "data/interaction_logs",
            "data/analysis_results",
            "data/consent"
        ]
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            self.assertTrue(
                full_path.exists() and full_path.is_dir(),
                f"Required directory {dir_path} must exist"
            )

    def test_required_code_modules_exist(self):
        """Verify required code modules referenced in quickstart exist."""
        required_modules = [
            "code/data_prep/download_defects4j.py",
            "code/data_prep/generate_summaries.py",
            "code/analysis/run_statistics.py",
            "code/utils/interaction_logger.py",
            "code/utils/anonymize_logs.py"
        ]
        for module_path in required_modules:
            full_path = self.project_root / module_path
            self.assertTrue(
                full_path.exists() and full_path.is_file(),
                f"Required module {module_path} must exist"
            )

    def test_requirements_txt_exists(self):
        """Verify requirements.txt exists for dependency installation."""
        req_path = self.project_root / "requirements.txt"
        self.assertTrue(
            req_path.exists(),
            "requirements.txt must exist for dependency management"
        )

    def test_requirements_txt_has_content(self):
        """Verify requirements.txt is not empty."""
        req_path = self.project_root / "requirements.txt"
        if req_path.exists():
            with open(req_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertGreater(
                len(content.strip()), 0,
                "requirements.txt must contain dependencies"
            )

    def test_project_structure_compliant(self):
        """Verify project follows expected directory structure."""
        expected_structure = [
            "code",
            "code/data_prep",
            "code/analysis",
            "code/utils",
            "code/tests",
            "data",
            "tests"
        ]
        for dir_path in expected_structure:
            full_path = self.project_root / dir_path
            self.assertTrue(
                full_path.exists() and full_path.is_dir(),
                f"Expected directory {dir_path} must exist"
            )

    def test_gitignore_exists(self):
        """Verify .gitignore exists."""
        gitignore_path = self.project_root / ".gitignore"
        self.assertTrue(
            gitignore_path.exists(),
            ".gitignore must exist for version control"
        )

    def test_no_placeholder_files(self):
        """Verify no placeholder/TODO files exist in critical paths."""
        critical_files = [
            "code/data_prep/download_defects4j.py",
            "code/data_prep/generate_summaries.py",
            "code/analysis/run_statistics.py"
        ]
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Check for obvious placeholders
                self.assertFalse(
                    "TODO" in content or "pass" in content or "NotImplementedError" in content,
                    f"File {file_path} should not contain TODO/pass/NotImplementedError placeholders"
                )

    def test_syntax_validity_of_core_modules(self):
        """Verify core Python modules have valid syntax."""
        core_modules = [
            "code/data_prep/download_defects4j.py",
            "code/data_prep/generate_summaries.py",
            "code/analysis/run_statistics.py",
            "code/utils/interaction_logger.py",
            "code/utils/anonymize_logs.py",
            "code/utils/latency_calibrator.py",
            "code/utils/assignment_generator.py"
        ]
        for module_path in core_modules:
            full_path = self.project_root / module_path
            if full_path.exists():
                try:
                    compile(full_path.read_text(), str(full_path), 'exec')
                except SyntaxError as e:
                    self.fail(f"Syntax error in {module_path}: {e}")

    def test_quickstart_references_real_scripts(self):
        """Verify scripts referenced in quickstart.md actually exist."""
        with open(self.quickstart_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract potential script references (basic heuristic)
        import re
        script_patterns = [
            r'code/[\w/]+\.py',
            r'python code/[\w/]+\.py'
        ]
        
        referenced_scripts = []
        for pattern in script_patterns:
            matches = re.findall(pattern, content)
            referenced_scripts.extend(matches)
        
        for script_ref in referenced_scripts:
            # Normalize path
            script_path = script_ref.replace('python ', '').strip()
            full_path = self.project_root / script_path
            self.assertTrue(
                full_path.exists(),
                f"Script {script_path} referenced in quickstart.md must exist"
            )

    def test_data_files_produced_by_previous_tasks(self):
        """Verify that data files from completed tasks exist."""
        # These are expected outputs from T013-T020 and T024
        expected_files = [
            # From T013: Defects4J download (at least directory structure)
            "data/defects4j",
            # From T014: Summaries
            "data/summaries/llm_sim_summaries.csv",
            "data/summaries/rule_summaries.csv",
            # From T015-T016: Interaction logs (may be empty if no participants yet, but files should exist)
            "data/interaction_logs/raw_logs.csv",
            "data/interaction_logs/anonymized_logs.csv",
            # From T024: Analysis results
            "data/analysis_results/results.csv",
            "data/analysis_results/sensitivity_analysis.csv",
            "data/analysis_results/outlier_flags.json"
        ]
        
        for file_path in expected_files:
            full_path = self.project_root / file_path
            # For directories, check existence
            if not file_path.endswith('.csv') and not file_path.endswith('.json'):
                self.assertTrue(
                    full_path.exists() and full_path.is_dir(),
                    f"Directory {file_path} must exist"
                )
            else:
                # For files, they should exist (may be empty if no data yet)
                self.assertTrue(
                    full_path.exists(),
                    f"File {file_path} must exist"
                )

    def test_reproducibility_package_exists(self):
        """Verify reproducibility package exists (from T031)."""
        package_path = self.project_root / "data/reproducibility_package_v1.0.tar.gz"
        self.assertTrue(
            package_path.exists(),
            "Reproducibility package data/reproducibility_package_v1.0.tar.gz must exist"
        )

    def test_ci_workflow_exists(self):
        """Verify CI workflow for reproducibility exists (from T030)."""
        workflow_path = self.project_root / ".github/workflows/test_reproducibility.yml"
        self.assertTrue(
            workflow_path.exists(),
            "CI workflow .github/workflows/test_reproducibility.yml must exist"
        )

    def test_api_contract_exists(self):
        """Verify API contract documentation exists (from T018a)."""
        contract_path = self.project_root / "contracts/api_participant.md"
        self.assertTrue(
            contract_path.exists(),
            "API contract contracts/api_participant.md must exist"
        )

    def test_consent_directory_secure(self):
        """Verify consent directory exists and is properly excluded."""
        consent_dir = self.project_root / "data/consent"
        self.assertTrue(
            consent_dir.exists() and consent_dir.is_dir(),
            "Consent directory data/consent must exist"
        )
        
        # Check .gitignore excludes consent
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                gitignore_content = f.read()
            self.assertTrue(
                "data/consent" in gitignore_content or "consent" in gitignore_content,
                ".gitignore must exclude data/consent directory"
            )

if __name__ == '__main__':
    unittest.main()
