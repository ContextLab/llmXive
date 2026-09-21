"""
Constants for the survey application.
"""

# Latin Square Matrix for stimulus ordering
# Each row represents a unique permutation of the 4 stimuli conditions.
# This ensures that each stimulus appears in each position exactly once across the cohort.
LATIN_SQUARE_MATRIX = [
    ["Professional", "Minimalist", "Low-Quality", "Neutral"],
    ["Minimalist", "Low-Quality", "Neutral", "Professional"],
    ["Low-Quality", "Neutral", "Professional", "Minimalist"],
    ["Neutral", "Professional", "Minimalist", "Low-Quality"]
]

# Stimuli file names (without extension)
STIMULI_FILES = ["professional", "minimalist", "low_quality", "neutral"]
