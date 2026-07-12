"""
Environment setup and validation for CI runner constraints.

This module configures environment variables to enforce CPU-only execution,
memory limits, and other CI-specific constraints. It also validates that
critical dependencies like RDKit are correctly installed and functional.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging for setup phase
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_ci_environment_variables():
    """
    Configure environment variables for CI runner constraints.
    
    Sets:
    - CPU-only execution flags
    - Memory limits
    - Disables GPU usage
    - Sets thread limits for reproducibility
    """
    # Force CPU-only execution
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['TORCH_CUDA_ARCH_LIST'] = ''
    
    # Set memory limits (in GB) - adjust based on CI constraints
    # Default to 4GB if not specified, matching analysis.py constraints
    if 'MEMORY_LIMIT_GB' not in os.environ:
        os.environ['MEMORY_LIMIT_GB'] = '4'
    
    # Set thread limits for reproducibility and resource control
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['NUMEXPR_NUM_THREADS'] = '1'
    
    # Disable GPU-accelerated libraries
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF warnings
    
    # Set dataset cache directory to avoid permission issues
    if 'HF_DATASETS_CACHE' not in os.environ:
        cache_dir = Path.home() / '.cache' / 'huggingface' / 'datasets'
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ['HF_DATASETS_CACHE'] = str(cache_dir)
    
    logger.info("CI environment variables configured successfully")
    logger.info(f"Memory limit: {os.environ['MEMORY_LIMIT_GB']} GB")
    logger.info(f"CPU threads: OMP={os.environ['OMP_NUM_THREADS']}, MKL={os.environ['MKL_NUM_THREADS']}")

def validate_rdkit_installation():
    """
    Validate that RDKit is installed and functional.
    
    Returns:
        bool: True if RDKit is valid, False otherwise
        
    Raises:
        ImportError: If RDKit cannot be imported
        RuntimeError: If RDKit functionality tests fail
    """
    try:
        from rdkit import Chem
        from rdkit import RDLogger
        
        # Disable RDKit warnings for cleaner output
        RDLogger.DisableLog('rdApp.*')
        
        # Test basic functionality
        smiles = "CCO"  # Ethanol
        mol = Chem.MolFromSmiles(smiles)
        
        if mol is None:
            raise RuntimeError(f"RDKit failed to parse SMILES: {smiles}")
        
        # Verify molecular properties calculation
        mw = Chem.Descriptors.MolWt(mol)
        if mw <= 0:
            raise RuntimeError(f"RDKit returned invalid molecular weight: {mw}")
        
        logger.info("RDKit validation successful")
        logger.info(f"  - Version: {Chem.__version__ if hasattr(Chem, '__version__') else 'unknown'}")
        logger.info(f"  - Test molecule (ethanol) MW: {mw:.2f} g/mol")
        
        return True
        
    except ImportError as e:
        logger.error(f"RDKit import failed: {e}")
        logger.error("Please install RDKit: conda install -c conda-forge rdkit")
        raise
    except Exception as e:
        logger.error(f"RDKit functionality test failed: {e}")
        raise RuntimeError(f"RDKit validation failed: {e}")

def validate_dependencies():
    """
    Validate all critical dependencies are installed.
    
    Returns:
        dict: Validation results for each dependency
    """
    dependencies = {
        'rdkit': 'rdkit',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'scipy': 'scipy',
        'scikit-learn': 'sklearn',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'requests': 'requests',
        'huggingface_hub': 'huggingface_hub',
        'datasets': 'datasets'
    }
    
    results = {}
    for name, import_name in dependencies.items():
        try:
            __import__(import_name)
            results[name] = {'status': 'installed', 'error': None}
            logger.debug(f"  {name}: installed")
        except ImportError as e:
            results[name] = {'status': 'missing', 'error': str(e)}
            logger.error(f"  {name}: MISSING - {e}")
    
    return results

def main():
    """
    Main entry point for environment setup and validation.
    
    This function:
    1. Configures CI environment variables
    2. Validates RDKit installation
    3. Validates all critical dependencies
    4. Reports overall status
    """
    logger.info("=" * 60)
    logger.info("Starting environment setup and validation")
    logger.info("=" * 60)
    
    # Step 1: Configure CI environment
    logger.info("Step 1: Configuring CI environment variables")
    set_ci_environment_variables()
    
    # Step 2: Validate RDKit
    logger.info("Step 2: Validating RDKit installation")
    try:
        rdkit_valid = validate_rdkit_installation()
    except Exception as e:
        logger.error(f"RDKit validation failed: {e}")
        sys.exit(1)
    
    # Step 3: Validate all dependencies
    logger.info("Step 3: Validating all dependencies")
    dep_results = validate_dependencies()
    
    # Step 4: Report overall status
    logger.info("Step 4: Generating validation report")
    missing_deps = [name for name, result in dep_results.items() if result['status'] == 'missing']
    
    if missing_deps:
        logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
        logger.error("Please install missing packages before proceeding.")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Environment setup and validation COMPLETE")
    logger.info("  - CI constraints configured")
    logger.info("  - RDKit validated successfully")
    logger.info("  - All dependencies present")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())