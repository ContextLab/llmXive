"""
Test suite for documentation and quickstart validation.
"""
import os
import pytest
from pathlib import Path
import yaml
import json


class TestDocumentationFiles:
    """Test that required documentation files exist and are valid."""

    @pytest.fixture
    def docs_dir(self):
        return Path("docs")

    @pytest.fixture
    def project_root(self):
        return Path(".")

    def test_readme_exists(self, project_root):
        """Test that README.md exists."""
        readme = project_root / "README.md"
        assert readme.exists(), "README.md must exist"
        assert readme.stat().st_size > 0, "README.md must not be empty"

    def test_quickstart_exists(self, project_root):
        """Test that quickstart.md exists."""
        quickstart = project_root / "quickstart.md"
        assert quickstart.exists(), "quickstart.md must exist"
        assert quickstart.stat().st_size > 0, "quickstart.md must not be empty"

    def test_requirements_exists(self, project_root):
        """Test that requirements.txt exists."""
        requirements = project_root / "requirements.txt"
        assert requirements.exists(), "requirements.txt must exist"
        assert requirements.stat().st_size > 0, "requirements.txt must not be empty"

    def test_ruff_config_exists(self, project_root):
        """Test that .ruff.toml exists."""
        ruff_config = project_root / ".ruff.toml"
        assert ruff_config.exists(), ".ruff.toml must exist"

    def test_black_config_exists(self, project_root):
        """Test that .black.toml exists."""
        black_config = project_root / ".black.toml"
        assert black_config.exists(), ".black.toml must exist"

    def test_env_example_exists(self, project_root):
        """Test that .env.example exists."""
        env_example = project_root / ".env.example"
        assert env_example.exists(), ".env.example must exist"

    def test_api_reference_exists(self, docs_dir):
        """Test that api_reference.md exists."""
        api_ref = docs_dir / "api_reference.md"
        assert api_ref.exists(), "docs/api_reference.md must exist"

    def test_methodology_exists(self, docs_dir):
        """Test that methodology.md exists."""
        methodology = docs_dir / "methodology.md"
        assert methodology.exists(), "docs/methodology.md must exist"

    def test_contributing_exists(self, docs_dir):
        """Test that contributing.md exists."""
        contributing = docs_dir / "contributing.md"
        assert contributing.exists(), "docs/contributing.md must exist"

    def test_validation_gate_exists(self, docs_dir):
        """Test that validation_gate.md exists."""
        validation_gate = docs_dir / "validation_gate.md"
        assert validation_gate.exists(), "docs/validation_gate.md must exist"

class TestQuickstartContent:
    """Test that quickstart.md contains required sections."""

    @pytest.fixture
    def quickstart_path(self):
        return Path("quickstart.md")

    def test_quickstart_has_setup_section(self, quickstart_path):
        """Test that quickstart has environment setup section."""
        content = quickstart_path.read_text()
        assert "## Step 1" in content or "## Installation" in content, \
            "quickstart.md must have setup/installation section"

    def test_quickstart_has_download_section(self, quickstart_path):
        """Test that quickstart has data download section."""
        content = quickstart_path.read_text()
        assert "download" in content.lower(), \
            "quickstart.md must mention data download"

    def test_quickstart_has_preprocessing_section(self, quickstart_path):
        """Test that quickstart has preprocessing section."""
        content = quickstart_path.read_text()
        assert "preprocess" in content.lower(), \
            "quickstart.md must mention preprocessing"

    def test_quickstart_has_analysis_section(self, quickstart_path):
        """Test that quickstart has analysis section."""
        content = quickstart_path.read_text()
        assert "analysis" in content.lower(), \
            "quickstart.md must mention analysis"

    def test_quickstart_has_troubleshooting(self, quickstart_path):
        """Test that quickstart has troubleshooting section."""
        content = quickstart_path.read_text()
        assert "troubleshoot" in content.lower() or "error" in content.lower(), \
            "quickstart.md should have troubleshooting guidance"

class TestRequirementsContent:
    """Test that requirements.txt contains required packages."""

    @pytest.fixture
    def requirements_path(self):
        return Path("requirements.txt")

    def test_has_pandas(self, requirements_path):
        """Test that pandas is in requirements."""
        content = requirements_path.read_text()
        assert "pandas" in content.lower(), "requirements.txt must include pandas"

    def test_has_numpy(self, requirements_path):
        """Test that numpy is in requirements."""
        content = requirements_path.read_text()
        assert "numpy" in content.lower(), "requirements.txt must include numpy"

    def test_has_scikit_learn(self, requirements_path):
        """Test that scikit-learn is in requirements."""
        content = requirements_path.read_text()
        assert "scikit-learn" in content.lower() or "scikit_learn" in content.lower(), \
            "requirements.txt must include scikit-learn"

    def test_has_statsmodels(self, requirements_path):
        """Test that statsmodels is in requirements."""
        content = requirements_path.read_text()
        assert "statsmodels" in content.lower(), "requirements.txt must include statsmodels"

    def test_has_zcompositions(self, requirements_path):
        """Test that zCompositions is in requirements."""
        content = requirements_path.read_text()
        assert "zcompositions" in content.lower(), "requirements.txt must include zCompositions"

    def test_has_scikit_bio(self, requirements_path):
        """Test that scikit-bio is in requirements."""
        content = requirements_path.read_text()
        assert "scikit-bio" in content.lower() or "scikit_bio" in content.lower(), \
            "requirements.txt must include scikit-bio"

    def test_has_pytest(self, requirements_path):
        """Test that pytest is in requirements."""
        content = requirements_path.read_text()
        assert "pytest" in content.lower(), "requirements.txt must include pytest"

    def test_has_black(self, requirements_path):
        """Test that black is in requirements."""
        content = requirements_path.read_text()
        assert "black" in content.lower(), "requirements.txt must include black"

    def test_has_ruff(self, requirements_path):
        """Test that ruff is in requirements."""
        content = requirements_path.read_text()
        assert "ruff" in content.lower(), "requirements.txt must include ruff"

class TestProjectStructure:
    """Test that required project directories exist."""

    @pytest.fixture
    def project_root(self):
        return Path(".")

    def test_code_dir_exists(self, project_root):
        """Test that code/ directory exists."""
        code_dir = project_root / "code"
        assert code_dir.exists() and code_dir.is_dir(), "code/ directory must exist"

    def test_data_dir_exists(self, project_root):
        """Test that data/ directory exists."""
        data_dir = project_root / "data"
        assert data_dir.exists() and data_dir.is_dir(), "data/ directory must exist"

    def test_results_dir_exists(self, project_root):
        """Test that results/ directory exists."""
        results_dir = project_root / "results"
        assert results_dir.exists() and results_dir.is_dir(), "results/ directory must exist"

    def test_tests_dir_exists(self, project_root):
        """Test that tests/ directory exists."""
        tests_dir = project_root / "tests"
        assert tests_dir.exists() and tests_dir.is_dir(), "tests/ directory must exist"

    def test_docs_dir_exists(self, project_root):
        """Test that docs/ directory exists."""
        docs_dir = project_root / "docs"
        assert docs_dir.exists() and docs_dir.is_dir(), "docs/ directory must exist"

    def test_data_raw_dir_exists(self, project_root):
        """Test that data/raw/ directory exists."""
        raw_dir = project_root / "data" / "raw"
        assert raw_dir.exists() and raw_dir.is_dir(), "data/raw/ directory must exist"

    def test_data_processed_dir_exists(self, project_root):
        """Test that data/processed/ directory exists."""
        processed_dir = project_root / "data" / "processed"
        assert processed_dir.exists() and processed_dir.is_dir(), "data/processed/ directory must exist"

    def test_results_associations_dir_exists(self, project_root):
        """Test that results/associations/ directory exists."""
        assoc_dir = project_root / "results" / "associations"
        assert assoc_dir.exists() and assoc_dir.is_dir(), "results/associations/ directory must exist"

    def test_results_plots_dir_exists(self, project_root):
        """Test that results/plots/ directory exists."""
        plots_dir = project_root / "results" / "plots"
        assert plots_dir.exists() and plots_dir.is_dir(), "results/plots/ directory must exist"

    def test_results_sensitivity_dir_exists(self, project_root):
        """Test that results/sensitivity/ directory exists."""
        sens_dir = project_root / "results" / "sensitivity"
        assert sens_dir.exists() and sens_dir.is_dir(), "results/sensitivity/ directory must exist"

    def test_results_validation_dir_exists(self, project_root):
        """Test that results/validation/ directory exists."""
        val_dir = project_root / "results" / "validation"
        assert val_dir.exists() and val_dir.is_dir(), "results/validation/ directory must exist"
