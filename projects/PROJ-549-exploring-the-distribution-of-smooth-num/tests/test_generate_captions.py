import json
import os
import tempfile
import pytest
from unittest.mock import patch

# Import the functions to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from generate_captions import load_model_fits, generate_captions, write_captions

class TestLoadModelFits:
    def test_load_existing_file(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {"plan_beta": 0.5, "spec_beta": 0.8}
        file_path = tmp_path / "model_fits.json"
        file_path.write_text(json.dumps(test_data))
        
        result = load_model_fits(str(file_path))
        assert result == test_data

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_model_fits(str(tmp_path / "nonexistent.json"))

    def test_load_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_model_fits(str(file_path))

class TestGenerateCaptions:
    def test_generate_plan_success(self):
        """Test caption generation when plan regression succeeds."""
        data = {
            "plan_beta": 0.45,
            "plan_beta_se": 0.02,
            "plan_r_squared": 0.98,
            "plan_ks_p": 0.15,
            "spec_beta": 0.8,
            "spec_beta_se": 0.05,
            "spec_r_squared": 0.95,
            "spec_chi2_p": 0.30
        }
        captions = generate_captions(data)
        
        assert len(captions) == 3
        assert "Plan-Primary Analysis" in captions[0]
        assert "0.45" in captions[0]
        assert "0.02" in captions[0]
        assert "0.98" in captions[0]
        assert "0.15" in captions[0]

    def test_generate_plan_failure(self):
        """Test caption generation when plan regression fails (null beta)."""
        data = {
            "plan_beta": None,
            "plan_beta_se": None,
            "plan_r_squared": None,
            "plan_ks_p": 0.15,
            "spec_beta": 0.8,
            "spec_beta_se": 0.05,
            "spec_r_squared": 0.95,
            "spec_chi2_p": 0.30
        }
        captions = generate_captions(data)
        
        assert len(captions) == 3
        assert "failed to converge" in captions[0]
        assert "0.15" in captions[0]

    def test_generate_spec_success(self):
        """Test caption generation when spec regression succeeds."""
        data = {
            "plan_beta": 0.45,
            "plan_beta_se": 0.02,
            "plan_r_squared": 0.98,
            "plan_ks_p": 0.15,
            "spec_beta": 0.8,
            "spec_beta_se": 0.05,
            "spec_r_squared": 0.95,
            "spec_chi2_p": 0.30
        }
        captions = generate_captions(data)
        
        assert "Spec-Mandatory Analysis" in captions[1]
        assert "0.8" in captions[1]
        assert "0.05" in captions[1]
        assert "0.95" in captions[1]
        assert "0.30" in captions[1]

    def test_generate_spec_failure(self):
        """Test caption generation when spec regression fails (null beta)."""
        data = {
            "plan_beta": 0.45,
            "plan_beta_se": 0.02,
            "plan_r_squared": 0.98,
            "plan_ks_p": 0.15,
            "spec_beta": None,
            "spec_beta_se": None,
            "spec_r_squared": None,
            "spec_chi2_p": 0.30
        }
        captions = generate_captions(data)
        
        assert "failed to converge" in captions[1]
        assert "0.30" in captions[1]

    def test_generate_summary(self):
        """Test that summary caption is always generated."""
        data = {
            "plan_beta": 0.45,
            "plan_beta_se": 0.02,
            "plan_r_squared": 0.98,
            "plan_ks_p": 0.15,
            "spec_beta": 0.8,
            "spec_beta_se": 0.05,
            "spec_r_squared": 0.95,
            "spec_chi2_p": 0.30
        }
        captions = generate_captions(data)
        
        assert "Analysis of smooth number distribution" in captions[2]
        assert "Plan grid" in captions[2]
        assert "Spec grid" in captions[2]

class TestWriteCaptions:
    def test_write_captions(self, tmp_path):
        """Test writing captions to a file."""
        captions = ["Caption 1 content", "Caption 2 content", "Caption 3 content"]
        output_path = tmp_path / "captions.txt"
        
        write_captions(captions, str(output_path))
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "Caption 1:" in content
        assert "Caption 1 content" in content
        assert "Caption 2:" in content
        assert "Caption 2 content" in content
        assert "Caption 3:" in content
        assert "Caption 3 content" in content