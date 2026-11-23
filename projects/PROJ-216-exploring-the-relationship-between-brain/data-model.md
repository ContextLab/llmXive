# Data Model

This document defines the core data entities used throughout the `PROJ-216-exploring-the-relationship-between-brain` pipeline.
It aligns with `specs/amendment-001-fluid-intelligence-n10.md` regarding the focus on Fluid Intelligence.

## Subject

Represents a single participant in the study, containing demographic information and paths to their data.

- `id`: string (e.g., "sub-001", "sub-002")
 - **Constraint**: Must match the BIDS subject ID format.
- `fluid_intelligence_score`: float (optional)
 - **Constraint**: Normalized score (0.0 to 1.0) or raw score depending on the source dataset.
 - **Source**: Derived from `participants.tsv` or `sub-XX_task-rest_bold.json` sidecars in the OpenNeuro dataset.
- `age`: integer (optional)
 - **Constraint**: Age in years at the time of scanning.
- `gender`: string (optional)
 - **Constraint**: Categorical value (e.g., "M", "F", "Other").
- `fMRI_path`: string
 - **Constraint**: Absolute or relative path to the raw or preprocessed NIfTI file associated with this subject.
 - **Usage**: Used by `code/preprocess.py` and `code/graph_metrics.py` to locate input data.

## GraphMetric

Represents a specific graph theoretical metric calculated for a subject's brain network.

- `subject_id`: string
 - **Constraint**: Foreign key referencing `Subject.id`.
- `metric_name`: string
 - **Example Values**: "global_efficiency", "clustering_coefficient", "modularity".
 - **Constraint**: Must correspond to one of the metrics implemented in `code/graph_metrics.py`.
- `value`: float
 - **Constraint**: The calculated numerical value of the metric.
- `confidence_interval`: string (optional)
 - **Format**: "95% CI: [lower_bound, upper_bound]"
 - **Usage**: Stores the confidence interval range if calculated (e.g., via bootstrapping).

## BehavioralScore

Represents a behavioral measurement associated with a subject, distinct from the primary Fluid Intelligence score if multiple measures exist.
This entity supports the analysis of correlations between graph metrics and various behavioral outcomes.

- `subject_id`: string
 - **Constraint**: Foreign key referencing `Subject.id`.
- `score_value`: float
 - **Constraint**: The numeric value of the behavioral score.
- `source_type`: string
 - **Example Values**: "fluid_intelligence", "musical_creativity" (deprecated per amendment), "age", "gender".
 - **Constraint**: Must match the expected types defined in `code/stats.py` for correlation analysis.
- `sub_scale_names`: list of strings (optional)
 - **Usage**: If the score is composite, lists the names of the sub-scales included.