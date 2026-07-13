"""
Project constants for molecular fingerprint analysis.
"""

# SMARTS pattern for organophosphate detection
SMARTS_PATTERN = "[P](=O)([O,SC])[O,SC]"

# Tanimoto similarity threshold for splitting
TANIMOTO_THRESHOLD = 0.85

# Morgan fingerprint parameters
MORGAN_RADIUS = 2
MORGAN_BITS = 2048

# MACCS fingerprint parameters
MACCS_BITS = 166

# Cross-validation parameters
N_FOLDS = 5

# Model training parameters
N_TREES = 100
MAX_DEPTH = 15

# Statistical test parameters
SIGNIFICANCE_LEVEL = 0.05
BOOTSTRAP_ITERATIONS = 1000

# Feature importance threshold for SC-003
SC003_THRESHOLD = 0.15  # 15% improvement
