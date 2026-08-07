"""
Configuration constants for the circadian-metabolic correlation project.

This module defines static lists and thresholds used throughout the pipeline,
specifically the core circadian gene list required for filtering and analysis.
"""

# List of core circadian clock genes based on current biological consensus
# Includes: PER family, CRY family, BMAL1 (ARNTL), CLOCK, NR1D1 (REV-ERBα), RORA (RORα)
# Note: Using official HUGO symbols (ARNTL for BMAL1) for GTEx compatibility.
CORE_CIRCADIAN_GENES = [
    "PER1",
    "PER2",
    "PER3",
    "CRY1",
    "CRY2",
    "ARNTL",   # Official symbol for BMAL1
    "CLOCK",
    "NR1D1",   # REV-ERBα
    "RORA",    # RORα
]

# Mapping of common aliases to official gene symbols if the dataset uses aliases
# This ensures robustness if the input data uses 'BMAL1' instead of 'ARNTL'
GENE_SYMBOL_ALIASES = {
    "BMAL1": "ARNTL",
    "REV-ERB1": "NR1D1",
    "RORALPHA": "RORA",
}

# ATP-III Metabolic Syndrome Thresholds (Reference for T014/T042)
# These are used for classification logic.
# Note: ATP-III traditionally uses waist circumference, but GTEx often lacks this,
# so BMI >= 30 is used as the proxy for abdominal obesity in this context.
METABOLIC_THRESHOLDS = {
    "bmi_cutoff": 30.0,        # kg/m^2 (Proxy for waist circumference)
    "glucose_cutoff": 100.0,   # mg/dL (Fasting)
    "tg_cutoff": 150.0,        # mg/dL
    "hdl_male_cutoff": 40.0,   # mg/dL
    "hdl_female_cutoff": 50.0, # mg/dL
    "sbp_cutoff": 130.0,       # mmHg
    "dbp_cutoff": 85.0,        # mmHg
}