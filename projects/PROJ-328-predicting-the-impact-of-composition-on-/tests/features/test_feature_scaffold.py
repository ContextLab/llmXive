"""
Tests for feature module scaffolding.

Verifies that all required files exist and can be imported.
"""
import pytest
import sys
from pathlib import Path

# Add code directory to path
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

class TestFeatureScaffold:
    """Test that feature module scaffolding is complete."""

    def test_features_init_exists(self):
        """Verify __init__.py exists in code/features/"""
        init_path = code_path / "features" / "__init__.py"
        assert init_path.exists(), f"__init__.py not found at {init_path}"

    def test_transformer_exists(self):
        """Verify transformer.py exists in code/features/"""
        transformer_path = code_path / "features" / "transformer.py"
        assert transformer_path.exists(), f"transformer.py not found at {transformer_path}"

    def test_descriptor_engine_exists(self):
        """Verify descriptor_engine.py exists in code/features/"""
        descriptor_path = code_path / "features" / "descriptor_engine.py"
        assert descriptor_path.exists(), f"descriptor_engine.py not found at {descriptor_path}"

    def test_collinearity_exists(self):
        """Verify collinearity.py exists in code/features/"""
        collinearity_path = code_path / "features" / "collinearity.py"
        assert collinearity_path.exists(), f"collinearity.py not found at {collinearity_path}"

    def test_import_transformer(self):
        """Verify CLRTransformer can be imported."""
        from features.transformer import CLRTransformer
        assert CLRTransformer is not None

    def test_import_descriptor_engine(self):
        """Verify DescriptorEngine can be imported."""
        from features.descriptor_engine import DescriptorEngine
        assert DescriptorEngine is not None

    def test_import_collinearity_functions(self):
        """Verify collinearity functions can be imported."""
        from features.collinearity import (
            calculate_vif,
            get_collinear_features,
            remove_collinear_features,
            save_vif_report
        )
        assert calculate_vif is not None
        assert get_collinear_features is not None
        assert remove_collinear_features is not None
        assert save_vif_report is not None

    def test_import_from_package(self):
        """Verify all components can be imported from features package."""
        from features import CLRTransformer, DescriptorEngine
        from features import calculate_vif, get_collinear_features
        
        assert CLRTransformer is not None
        assert DescriptorEngine is not None
        assert calculate_vif is not None
        assert get_collinear_features is not None

    def test_transformer_instantiation(self):
        """Verify CLRTransformer can be instantiated."""
        from features.transformer import CLRTransformer
        transformer = CLRTransformer(pseudo_count=1e-6)
        assert transformer is not None
        assert transformer.pseudo_count == 1e-6

    def test_descriptor_engine_instantiation(self):
        """Verify DescriptorEngine can be instantiated."""
        from features.descriptor_engine import DescriptorEngine
        engine = DescriptorEngine()
        assert engine is not None

    def test_vif_report_save_function(self):
        """Verify save_vif_report function exists and has correct signature."""
        from features.collinearity import save_vif_report
        import inspect
        
        sig = inspect.signature(save_vif_report)
        params = list(sig.parameters.keys())
        
        assert 'vif_df' in params
        assert 'output_path' in params
        assert 'threshold' in params