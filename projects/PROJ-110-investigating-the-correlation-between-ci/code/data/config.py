"""
Configuration constants for the circadian-metabolic correlation project.

This module defines static lists and thresholds used throughout the pipeline,
specifically the core circadian gene list required for filtering and analysis.
"""

# List of core circadian clock genes based on current biological consensus
# Includes: PER family, CRY family, BMAL1 (ARNTL), CLOCK, NR1D1 (REV-ERBα), RORA (RORα)
CORE_CIRCADIAN_GENES = [
    "PER1",
    "PER2",
    "PER3",
    "CRY1",
    "CRY2",
    "ARNTL",   # Commonly known as BMAL1 in literature; using official symbol for GTEx compatibility
    "CLOCK",
    "NR1D1",   # REV-ERBα
    "RORA",    # RORα
]

# Mapping of common aliases to official gene symbols if the dataset uses aliases
# This ensures robustness if the input data uses 'BMAL1' instead of 'ARNTL'
GENE_SYMBOL_ALIASES = {
    "BMAL1": "ARNTL",
    "NR1D1": "REV-ERB1", # Optional alias if needed, but NR1D1 is standard
    "RORA": "RORALPHA",
}

# ATP-III Metabolic Syndrome Thresholds (Reference for T014/T042)
# These are used for classification logic
METABOLIC_THRESHOLDS = {
    "bmi_cutoff": 30.0,  # kg/m^2 (Note: ATP-III uses waist circumference, but BMI is often used as proxy in GTEx)
    "glucose_cutoff": 100.0,  # mg/dL (Fasting)
    "tg_cutoff": 150.0,  # mg/dL
    "hdl_male_cutoff": 40.0,  # mg/dL
    "hdl_female_cutoff": 50.0,  # mg/dL
    "sbp_cutoff": 130.0,  # mmHg
    "dbp_cutoff": 85.0,   # mmHg
}