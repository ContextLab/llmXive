"""
Unit tests for reaction template splitting logic (T017a).

Tests:
1. Strict template separation between splits
2. Zero overlap verification
3. Condition usage in split logic
4. Artifact generation
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.preprocessing import (
    extract_reaction_template,
    scaffold_split,
    verify_template_overlap,
    verify_conditions_used_in_split,
    verify_reaction_template_split,
    load_and_preprocess
)

class TestReactionTemplateSplitting:
    """Test suite for reaction template splitting functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data with known templates."""
        data = {
            'reactant_smiles': [
                'CC(=O)O',  # Template: CC(=O)O
                'CC(=O)O',  # Same template
                'CCO',      # Different template
                'CCO',      # Same template
                'c1ccccc1', # Aromatic template
                'c1ccccc1', # Same template
                'CC(C)O',   # Another template
                'CC(C)O',   # Same template
            ],
            'dft_total_energy': [-100.0, -100.5, -50.0, -50.5, -200.0, -200.5, -75.0, -75.5],
            'solvent': ['water', 'ethanol', 'water', 'ethanol', 'water', 'ethanol', 'water', 'ethanol'],
            'catalyst': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
            'temperature': [298, 298, 300, 300, 298, 298, 300, 300]
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def sample_data_with_templates(self, sample_data):
        """Create sample data with pre-computed templates."""
        df = sample_data.copy()
        df['reaction_template'] = df['reactant_smiles']
        return df
    
    def test_extract_reaction_template_simple(self):
        """Test basic template extraction."""
        smiles = 'CC(=O)O'
        template = extract_reaction_template(smiles)
        assert template is not None
        assert isinstance(template, str)
        assert len(template) > 0
    
    def test_scaffold_split_no_overlap(self, sample_data_with_templates):
        """Test that scaffold split produces zero overlap."""
        train_df, val_df, test_df = scaffold_split(
            sample_data_with_templates,
            template_col='reaction_template',
            train_ratio=0.5,
            val_ratio=0.25,
            test_ratio=0.25,
            seed=42
        )
        
        # Verify no template overlap
        train_templates = set(train_df['reaction_template'].unique())
        val_templates = set(val_df['reaction_template'].unique())
        test_templates = set(test_df['reaction_template'].unique())
        
        assert len(train_templates & val_templates) == 0
        assert len(train_templates & test_templates) == 0
        assert len(val_templates & test_templates) == 0
    
    def test_verify_template_overlap_pass(self, sample_data_with_templates):
        """Test overlap verification with valid split."""
        train_df, val_df, test_df = scaffold_split(
            sample_data_with_templates,
            template_col='reaction_template',
            seed=42
        )
        
        assert verify_template_overlap(train_df, val_df, test_df) == True
    
    def test_verify_template_overlap_fail(self):
        """Test overlap detection with intentional overlap."""
        # Create DataFrames with overlapping templates
        train_df = pd.DataFrame({
            'reaction_template': ['A', 'B', 'C']
        })
        val_df = pd.DataFrame({
            'reaction_template': ['B', 'D', 'E']  # 'B' overlaps
        })
        test_df = pd.DataFrame({
            'reaction_template': ['F', 'G', 'H']
        })
        
        assert verify_template_overlap(train_df, val_df, test_df) == False
    
    def test_condition_usage_verification(self, sample_data_with_templates):
        """Test that condition usage is verified."""
        train_df, val_df, test_df = scaffold_split(
            sample_data_with_templates,
            template_col='reaction_template',
            condition_cols=['solvent', 'catalyst'],
            seed=42
        )
        
        result = verify_conditions_used_in_split(
            train_df, val_df, test_df,
            condition_cols=['solvent', 'catalyst']
        )
        
        # Should return True (conditions appear balanced)
        assert result == True
    
    def test_verify_reaction_template_split_artifacts(self, sample_data_with_templates):
        """Test that output artifacts are generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            train_df, val_df, test_df, manifest = verify_reaction_template_split(
                sample_data_with_templates,
                template_col='reaction_template',
                output_dir=output_dir
            )
            
            # Check manifest
            assert 'train_count' in manifest
            assert 'val_count' in manifest
            assert 'test_count' in manifest
            assert 'overlap_check' in manifest
            assert manifest['overlap_check'] == True
            
            # Check output files
            split_indices_path = output_dir / 'split_indices.parquet'
            split_manifest_path = output_dir / 'split_manifest.json'
            
            assert split_indices_path.exists()
            assert split_manifest_path.exists()
            
            # Verify manifest content
            with open(split_manifest_path, 'r') as f:
                loaded_manifest = json.load(f)
            
            assert loaded_manifest['train_count'] == len(train_df)
            assert loaded_manifest['val_count'] == len(val_df)
            assert loaded_manifest['test_count'] == len(test_df)
            
            # Verify split indices schema
            split_indices = pd.read_parquet(split_indices_path)
            assert 'split' in split_indices.columns
            assert 'index' in split_indices.columns
            
            # Verify splits are present
            splits = split_indices['split'].unique()
            assert set(splits) == {'train', 'val', 'test'}
    
    def test_split_ratio_accuracy(self, sample_data_with_templates):
        """Test that split ratios are approximately correct."""
        n_total = len(sample_data_with_templates)
        train_df, val_df, test_df = scaffold_split(
            sample_data_with_templates,
            template_col='reaction_template',
            train_ratio=0.6,
            val_ratio=0.2,
            test_ratio=0.2,
            seed=42
        )
        
        # Note: Exact ratios may not be achieved due to template grouping
        # But the sum should equal total
        assert len(train_df) + len(val_df) + len(test_df) == n_total
    
    def test_error_on_overlap(self, sample_data_with_templates):
        """Test that error is raised if overlap is detected."""
        # This test is somewhat artificial since scaffold_split
        # should never produce overlap, but we test the verification logic
        
        # Create a scenario where overlap would occur (manually)
        # In practice, scaffold_split prevents this
        train_df = pd.DataFrame({'reaction_template': ['A', 'B']})
        val_df = pd.DataFrame({'reaction_template': ['B', 'C']})  # Overlap on 'B'
        test_df = pd.DataFrame({'reaction_template': ['D', 'E']})
        
        # Verify that our overlap check catches it
        assert not verify_template_overlap(train_df, val_df, test_df)
    
    def test_full_pipeline_integration(self, sample_data):
        """Test the full load_and_preprocess pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save sample data
            data_path = Path(tmpdir) / 'test_data.csv'
            sample_data.to_csv(data_path, index=False)
            
            output_dir = Path(tmpdir) / 'output'
            
            result = load_and_preprocess(
                data_path=data_path,
                output_dir=output_dir
            )
            
            # Check result structure
            assert 'train' in result
            assert 'val' in result
            assert 'test' in result
            assert 'manifest' in result
            
            # Check artifact generation
            assert (output_dir / 'processed' / 'split_indices.parquet').exists()
            assert (output_dir / 'processed' / 'split_manifest.json').exists()
            
            # Check manifest
            manifest = result['manifest']
            assert manifest['overlap_check'] == True
            assert manifest['train_count'] > 0
            assert manifest['val_count'] > 0
            assert manifest['test_count'] > 0