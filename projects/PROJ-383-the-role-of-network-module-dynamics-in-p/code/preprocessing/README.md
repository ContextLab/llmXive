# Preprocessing Configuration Justification
## Project: Network Module Dynamics in Predicting Working Memory (PROJ-383)

This document provides the justification for the `fmriprep.conf` configuration file,
satisfying **Constitution Principle VI: Transparency and Reproducibility**.

### 1. Principle VI Compliance
Constitution Principle VI mandates that all preprocessing steps be explicitly defined,
reproducible, and justified to ensure scientific rigor. The `fmriprep.conf` file
serves as the single source of truth for the preprocessing pipeline, eliminating
ambiguity in parameter selection.

### 2. Configuration Decisions

#### 2.1 Spatial Normalization (MNI152NLin2009cAsym)
We selected the **MNI152NLin2009cAsym** template (2mm resolution) to align with
the Human Connectome Project (HCP) standards. This ensures compatibility with
the HCP-MMP parcellation atlas, which is the basis for our network module analysis.
Using a non-standard template would introduce unnecessary variability and hinder
comparison with existing literature.

#### 2.2 Skull Stripping Strategy
We utilize the **HCP-MMP derived brain mask** for skull stripping. This choice
is critical because:
- It preserves the cortical ribbon accurately, which is essential for connectivity
 analysis.
- It avoids the over- or under-stripping issues common in generic skull-stripping
 algorithms.
- It ensures consistency across subjects, reducing noise in the time series data.

#### 2.3 Confound Regressors
The configuration explicitly requests **motion parameters, derivatives, global signal,
white matter, CSF, and aCompCor components**. This is not merely for completeness;
it is a prerequisite for **Task T012b**, which implements motion scrubbing and
regression. Without these specific confounds, we cannot control for motion artifacts,
violating **FR-005** (motion control) and compromising the validity of the
flexibility metric.

#### 2.4 Boundary-Based Registration (BBR)
We enable **BBR** for functional-to-structural alignment. BBR is the gold standard
for fMRI preprocessing, particularly for HCP data, as it minimizes distortion
at the gray-white matter boundary. This improves the accuracy of the subsequent
parcellation and connectivity estimation.

### 3. Reproducibility and Audit Trail
The `verbose: true` and `log-level: INFO` settings ensure that every step of the
preprocessing pipeline is logged. This audit trail is essential for:
- Debugging pipeline failures.
- Verifying that the correct parameters were used.
- Satisfying the reproducibility requirements of Constitution Principle VI.

### 4. Conclusion
The `fmriprep.conf` file is not a generic template; it is a carefully curated
configuration that aligns with HCP standards, supports downstream analysis requirements,
and ensures the transparency and reproducibility mandated by Constitution Principle VI.
Any deviation from this configuration would require a formal justification and
re-evaluation of the pipeline's validity.