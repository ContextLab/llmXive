"""
Tests for T007d: Validate research.md and configure target_auc.

These tests verify that:
1. The script correctly identifies missing research.md
2. The script extracts target_auc from research.md
3. The script updates code/config.yaml correctly
4. The script raises appropriate errors for malformed research.md
"""
import os
import sys
import tempfile
import shutil
import pytest
import yaml
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from validate_research import (
    check_research_md_exists,
    extract_target_auc_from_research,
    update_config_yaml,
    validate_config,
    RESEARCH_MD_PATH,
    CONFIG_YAML_PATH
)

class TestValidateResearch:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Set up temporary directory for each test."""
        self.original_cwd = os.getcwd()
        self.tmp_dir = tmp_path
        os.chdir(tmp_path)
        
        # Create necessary directories
        (tmp_path / 'code').mkdir(exist_ok=True)
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
    
    def test_check_research_md_exists_missing(self):
        """Test that check_research_md_exists raises error when research.md is missing."""
        with pytest.raises(FileNotFoundError) as exc_info:
            check_research_md_exists()
        
        assert RESEARCH_MD_PATH in str(exc_info.value)
    
    def test_check_research_md_exists_present(self, tmp_path):
        """Test that check_research_md_exists passes when research.md exists."""
        # Create a dummy research.md
        research_md = tmp_path / RESEARCH_MD_PATH
        research_md.write_text("# Research Plan\n\ntarget_auc: 0.80\n")
        
        # Should not raise
        check_research_md_exists()
    
    def test_extract_target_auc_yaml_style(self, tmp_path):
        """Test extraction of target_auc in YAML style."""
        research_content = """
        # Research Plan
        
        Parameters:
        target_auc: 0.75
        temporal_split: 0.8
        """
        research_md = tmp_path / RESEARCH_MD_PATH
        research_md.write_text(research_content)
        
        os.chdir(tmp_path)
        target_auc = extract_target_auc_from_research()
        
        assert target_auc == 0.75
    
    def test_extract_target_auc_natural_language(self, tmp_path):
        """Test extraction of target_auc in natural language."""
        research_content = """
        # Research Plan
        
        The target AUC is 0.82 for this study.
        """
        research_md = tmp_path / RESEARCH_MD_PATH
        research_md.write_text(research_content)
        
        os.chdir(tmp_path)
        target_auc = extract_target_auc_from_research()
        
        assert target_auc == 0.82
    
    def test_extract_target_auc_missing(self, tmp_path):
        """Test that extraction fails when target_auc is not found."""
        research_content = """
        # Research Plan
        
        This is a research plan without target_auc.
        """
        research_md = tmp_path / RESEARCH_MD_PATH
        research_md.write_text(research_content)
        
        os.chdir(tmp_path)
        
        with pytest.raises(ValueError) as exc_info:
            extract_target_auc_from_research()
        
        assert 'target_auc' in str(exc_info.value)
    
    def test_update_config_yaml_existing(self, tmp_path):
        """Test updating an existing config.yaml."""
        # Create existing config
        config_path = tmp_path / 'code' / 'config.yaml'
        existing_config = {
            'seed': 42,
            'memory_limit_mb': 7000
        }
        with open(config_path, 'w') as f:
            yaml.dump(existing_config, f)
        
        os.chdir(tmp_path)
        update_config_yaml(0.85)
        
        # Verify update
        with open(config_path, 'r') as f:
            updated_config = yaml.safe_load(f)
        
        assert updated_config['target_auc'] == 0.85
        assert updated_config['seed'] == 42
        assert updated_config['memory_limit_mb'] == 7000
    
    def test_update_config_yaml_new(self, tmp_path):
        """Test creating a new config.yaml."""
        config_path = tmp_path / 'code' / 'config.yaml'
        
        os.chdir(tmp_path)
        update_config_yaml(0.90)
        
        # Verify creation
        assert config_path.exists()
        
        with open(config_path, 'r') as f:
            new_config = yaml.safe_load(f)
        
        assert new_config['target_auc'] == 0.90
    
    def test_validate_config_success(self, tmp_path):
        """Test successful validation of config.yaml."""
        config_path = tmp_path / 'code' / 'config.yaml'
        config_content = {
            'target_auc': 0.78,
            'seed': 42
        }
        with open(config_path, 'w') as f:
            yaml.dump(config_content, f)
        
        os.chdir(tmp_path)
        auc = validate_config()
        
        assert auc == 0.78
    
    def test_validate_config_missing_key(self, tmp_path):
        """Test validation fails when target_auc is missing."""
        config_path = tmp_path / 'code' / 'config.yaml'
        config_content = {
            'seed': 42,
            'memory_limit_mb': 7000
        }
        with open(config_path, 'w') as f:
            yaml.dump(config_content, f)
        
        os.chdir(tmp_path)
        
        with pytest.raises(RuntimeError) as exc_info:
            validate_config()
        
        assert 'target_auc' in str(exc_info.value)
    
    def test_full_integration(self, tmp_path):
        """Test the full workflow: research.md -> config.yaml -> validation."""
        # Create research.md
        research_md = tmp_path / RESEARCH_MD_PATH
        research_md.write_text("""
        # Research Plan for GNN Anomaly Detection
        
        Target AUC Threshold: 0.80
        target_auc: 0.80
        
        This plan defines the success criteria for the GNN anomaly detection study.
        """)
        
        os.chdir(tmp_path)
        
        # Run the workflow
        check_research_md_exists()
        target_auc = extract_target_auc_from_research()
        update_config_yaml(target_auc)
        final_auc = validate_config()
        
        assert final_auc == 0.80
        
        # Verify file contents
        config_path = tmp_path / 'code' / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config['target_auc'] == 0.80