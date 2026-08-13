# Project Limitations

## Dataset Constraints
- **Absence of Control Condition**: The OpenNeuro ds000234 dataset does not include a "told vs. experienced" control condition.
- **Simulation Method**: To simulate null models, we use "label shuffling" rather than a true control task.

## Methodological Adaptations
- **fMRIPrep vs. Nilearn**: The pipeline uses Nilearn for preprocessing where fMRIPrep is too resource-intensive for the CI environment.
- **Sequential Execution**: fMRIPrep is run sequentially per subject to comply with 7GB RAM constraints, overriding the default parallel execution.

## Metric Definitions
- **Chance Baseline**: Accuracy is calculated against `1/N_actual`, where `N_actual` is the number of unique labels observed in the test fold after aggregation of rare classes.
