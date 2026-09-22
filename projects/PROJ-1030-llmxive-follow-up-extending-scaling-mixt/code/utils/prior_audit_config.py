"""
Configuration for the Prior Audit (Label Independence) metric.
Defines the threshold and algorithm parameters.
"""

# Threshold for Pearson correlation between depth_confidence_score and physical_label.
# If correlation > CORRELATION_THRESHOLD, the audit fails (shared priors detected).
CORRELATION_THRESHOLD = 0.1

# Description of the algorithm:
# 1. Load the full labels.csv (including 'null' rows).
# 2. Filter out rows where label == 'null'.
# 3. Extract 'depth_confidence_score' and 'physical_label' (mapped to 0 for valid, 1 for invalid).
# 4. Calculate Pearson correlation coefficient.
# 5. Return True if correlation > CORRELATION_THRESHOLD (Shared Priors Detected), False otherwise.

ALGORITHM_DESCRIPTION = (
    "Calculates Pearson correlation between depth_confidence_score and physical_label "
    "on non-null rows. Fails if correlation exceeds threshold."
)
