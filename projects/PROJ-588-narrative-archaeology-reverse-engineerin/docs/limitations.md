# Limitations and Deviations

## Dataset Limitations
- **Absence of "Told vs. Experienced" Control**: The dataset (ds000234) does not include a control condition comparing "told" versus "experienced" narratives as originally hypothesized in some theoretical frameworks.
- **Simulation Method**: To simulate null models, we employ "label shuffling" instead of a true control condition.

## Methodological Deviations
- **fMRIPrep -> nilearn Swap**: Per Plan override, we utilize nilearn's preprocessing capabilities alongside fMRIPrep wrappers rather than a full fMRIPrep standalone run, to better fit CI memory constraints.
- **Sequential Execution**: To respect the 7GB RAM limit on GitHub Actions free-tier, preprocessing is executed sequentially per subject rather than in parallel.

## Metric Adjustments
- **Chance Level (SC-003)**: The static `N` in the specification is replaced with `N_actual` (observed unique labels after aggregation) to ensure calculability in small-sample scenarios. Aggregation logic is documented in `code/models/decoder.py`.

## Memory Constraints
- All models are constrained to CPU-only inference. No GPU training or 8-bit quantization is used.
