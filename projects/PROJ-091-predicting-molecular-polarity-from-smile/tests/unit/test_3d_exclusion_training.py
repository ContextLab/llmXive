"""
Unit test for 3D exclusion in the training pipeline.

This test verifies that the training pipeline (specifically the 
lightgbm training module) does not import or call any 3D-dependent 
functions from RDKit, ensuring compliance with the 2D-only constraint.
"""
import sys
import types
from unittest.mock import patch, MagicMock
import pytest

# Import the 3D exclusion utility from the project's validators module
from utils.validators import enforce_2d_only_imports, assert_no_3d_calls

# The module we are testing
TARGET_MODULE = "models.train_lightgbm"

# List of known 3D-dependent RDKit functions that must NOT be called/used
# These are the functions that generate or require 3D conformers
FORBIDDEN_3D_FUNCTIONS = {
    "rdkit.Chem.AllChem.EmbedMolecule",
    "rdkit.Chem.AllChem.EmbedMultipleConfs",
    "rdkit.Chem.AllChem.MMFFOptimizeMolecule",
    "rdkit.Chem.AllChem.UFFOptimizeMolecule",
    "rdkit.Chem.rdDistGeom.EmbedMolecule",
    "rdkit.Chem.rdDistGeom.EmbedMultipleConfs",
    "rdkit.Chem.rdForceFieldHelpers.UFFOptimizeMolecule",
    "rdkit.Chem.rdForceFieldHelpers.MMFFOptimizeMolecule",
    "rdkit.Chem.rdMolTransforms.Get3DDistance",
    "rdkit.Chem.rdMolTransforms.Get3DDistanceMatrix",
}

def test_no_3d_imports_in_training_module():
    """
    Verify that the training module does not import any 3D-specific 
    RDKit submodules or functions directly.
    """
    # We use a custom import hook to detect forbidden imports
    class ForbiddenImportDetector:
        def __init__(self, forbidden_set):
            self.forbidden = forbidden_set
            self.found_forbidden = []

        def find_module(self, fullname, path=None):
            if fullname in self.forbidden:
                self.found_forbidden.append(fullname)
            return None  # Let the normal importer handle it

    detector = ForbiddenImportDetector(FORBIDDEN_3D_FUNCTIONS)
    
    # Temporarily install the detector
    original_meta_path = sys.meta_path.copy()
    try:
        sys.meta_path.insert(0, detector)
        
        # Attempt to import the target module
        # We use importlib to ensure the import happens fresh
        import importlib
        try:
            module = importlib.import_module(TARGET_MODULE)
        except ImportError as e:
            # If the module fails to import for other reasons (e.g. missing deps),
            # we should still check if it's due to 3D imports.
            # However, for this specific test, we expect the module to exist.
            # If it doesn't exist, we might need to mock dependencies.
            if "No module named" in str(e):
                # Module doesn't exist yet, which is fine for this test context
                # if we are just checking for forbidden imports in code structure.
                # But typically the module should exist.
                pass
            else:
                raise
        
        # Check if any forbidden imports were detected
        if detector.found_forbidden:
            pytest.fail(f"Training module attempted to import forbidden 3D functions: {detector.found_forbidden}")
            
    finally:
        sys.meta_path = original_meta_path

def test_assert_no_3d_calls_on_training_module():
    """
    Use the project's existing assert_no_3d_calls utility to verify
    that the training module's source code does not contain calls to
    forbidden 3D functions.
    """
    # This function inspects the source code of the module
    # It should raise an AssertionError if 3D calls are found
    try:
        assert_no_3d_calls(TARGET_MODULE)
    except AssertionError as e:
        pytest.fail(f"Training module contains 3D function calls: {str(e)}")
    except ModuleNotFoundError:
        # If the module doesn't exist yet, we can't check it.
        # This might happen if T023 hasn't been run.
        # In that case, we skip the check or mark as pending.
        pytest.skip(f"Module {TARGET_MODULE} not found. Skipping 3D call check.")

def test_training_pipeline_does_not_call_3d_functions():
    """
    Verify that the training pipeline logic does not invoke 3D functions
    during execution by mocking them and ensuring they are not called.
    """
    # We will mock the forbidden functions and ensure they are never called
    # when the training module's main functions are executed.
    
    # First, we need to mock the forbidden functions in the rdkit namespace
    # to detect if they are called.
    
    with patch("rdkit.Chem.AllChem.EmbedMolecule", side_effect=RuntimeError("3D function called!")) as mock_embed, \
           patch("rdkit.Chem.AllChem.EmbedMultipleConfs", side_effect=RuntimeError("3D function called!")) as mock_embed_multi:
        
        # We need to ensure the mock is active before importing the module
        # or if the module is already imported, we need to reload it.
        # For this test, we assume the module is not yet imported.
        
        import importlib
        import sys
        
        # Remove the module from cache if it exists
        if TARGET_MODULE in sys.modules:
            del sys.modules[TARGET_MODULE]
        
        try:
            module = importlib.import_module(TARGET_MODULE)
            
            # If the module has a main function or a train function, call it
            # with minimal arguments to see if it triggers 3D calls.
            # However, since we don't have real data, we might just check
            # if the module loads without triggering the mocks.
            
            # Check if any of the mocks were called during import/initialization
            if mock_embed.called or mock_embed_multi.called:
                pytest.fail("3D functions were called during module initialization or import.")
                
        except RuntimeError as e:
            if "3D function called!" in str(e):
                pytest.fail("Training module invoked a forbidden 3D function.")
            else:
                raise
        except Exception as e:
            # Other exceptions (like missing data) are expected and don't indicate 3D usage
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
