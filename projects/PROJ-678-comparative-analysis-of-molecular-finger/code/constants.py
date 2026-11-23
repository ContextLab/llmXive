# Constants for the Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction
# This module defines all critical configuration parameters used across the pipeline.
# These constants MUST be imported by other modules (e.g., filter.py, split.py, fingerprints.py)
# rather than being hardcoded locally to ensure consistency and maintainability.

# SMARTS pattern for identifying organophosphates (phosphorus center with specific bonding)
# Pattern: Phosphorus double-bonded to Oxygen, single-bonded to (O, S, or C), and single-bonded to (O or S)
SMARTS_PATTERN = "[P](=O)([O,SC])[O,SC]"

# Tanimoto similarity threshold for maximal dissimilarity splitting
# Compounds with similarity < this value are considered dissimilar
TANIMOTO_THRESHOLD = 0.85

# Morgan fingerprint parameters
MORGAN_RADIUS = 2
MORGAN_BITS = 2048

# MACCS fingerprint parameters
MACCS_BITS = 166

# Cross-validation parameters
N_FOLDS = 5