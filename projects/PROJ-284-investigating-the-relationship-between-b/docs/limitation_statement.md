# Limitation Statement

This document outlines the limitations and assumptions of the current research pipeline and findings.

## 1. Proxy for Proprioceptive Accuracy

**Statement:** "Motor Task Performance is a proxy for proprioceptive accuracy."

**Explanation:** The behavioral data used in this study (HCP Motor Task scores) is designed to assess motor function and performance. While motor control relies heavily on proprioceptive feedback, the task itself does not directly measure proprioceptive acuity (e.g., joint position sense thresholds). Therefore, any correlations observed between brain network dynamics and motor scores should be interpreted as associations with motor performance, which serves as an indirect indicator of proprioceptive processing.

## 2. Associational Relationship

**Statement:** "The findings represent an associational relationship, not causation."

**Explanation:** This study employs a correlational design. While significant correlations between network metrics (e.g., Participation Coefficient) and motor scores may be identified, these results do not imply that changes in network dynamics *cause* changes in motor performance, or vice versa. Unmeasured confounding variables (e.g., age, sex, general cognitive ability, or genetic factors) could influence both brain network organization and motor behavior. Longitudinal or interventional studies would be required to establish causal links.

## 3. Data Limitations

- **Sample Size:** The statistical power of the analysis is constrained by the available sample size in the HCP dataset. While power analysis is conducted to determine detectable effect sizes, small effect sizes may remain undetected.
- **Data Quality:** Despite rigorous preprocessing (motion correction, tSNR filtering), residual artifacts (e.g., physiological noise, head motion) may persist and influence connectivity estimates.
- **Atlas Resolution:** The use of the Schaefer 400-parcel atlas provides a high-resolution parcellation, but it may not capture fine-grained subcortical or cerebellar dynamics relevant to motor control.

## 4. Methodological Assumptions

- **Linear Relationships:** The primary correlation analyses (Pearson/Spearman) assume monotonic or linear relationships between variables. Non-linear associations may be missed.
- **Network Construction:** Functional connectivity is estimated using Pearson correlation of time-series. Alternative methods (e.g., partial correlation, dynamic connectivity) were not employed in this baseline pipeline.
- **Covariate Control:** Framewise Displacement (FD) is used as a covariate to control for motion, but other potential confounds (e.g., global signal, physiological noise) are not explicitly modeled in the primary analysis.

## 5. Generalizability

The results are specific to the HCP population (healthy adults, 22-35 years old). Generalization to other age groups, clinical populations, or different cultural contexts should be made with caution.
