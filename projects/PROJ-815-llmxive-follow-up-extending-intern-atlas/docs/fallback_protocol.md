# Fallback Protocol: Ground Truth Label Availability

## 1. Trigger Condition
The fallback protocol is triggered when the data extraction pipeline (`code/data/run_extraction.py`) attempts to process the Intern-Atlas graph for the specified time window (2010–2018) and detects that **no ground truth retraction labels** are available for any node in the filtered dataset.

This check occurs after:
1. Loading and filtering the graph by year.
2. Filtering edges to ensure only human-annotated types are present (via `abort_if_llm_inferred()`).
3. Attempting to merge retraction data from external databases.

If the resulting merged dataset contains **zero rows** with a valid `retraction_status` label (values 0, 1, or 2), the trigger is active.

## 2. Action
Upon triggering, the pipeline **MUST ABORT immediately**. No further computation, modeling, or analysis is permitted.

The system must exit with the following **exact error message** to standard error:

```
No ground truth labels found for the specified time window; analysis cannot proceed.
```

The process must return a non-zero exit code (e.g., `sys.exit(1)`) to indicate a hard failure.

## 3. Constraints
- **NO Synthetic Data Generation**: Under no circumstances is the system permitted to generate synthetic labels, simulate retraction statuses, or fabricate data points to "fill the gap."
- **NO Fallback to Unlabeled Analysis**: The pipeline cannot proceed with a subset of unlabeled nodes or switch to an unsupervised mode. The scientific validity of the study depends on the presence of verified ground truth.
- **NO Silent Failure**: The system must not simply produce an empty output file or skip the labeling step. The abort must be explicit and logged.

## 4. Rationale
The core research hypothesis relies on predicting retraction status based on topological features. Without ground truth labels (Robust, Fragile, or Retraction-Only), the target variable for supervised learning is undefined. Proceeding without these labels would render any subsequent model training or evaluation scientifically invalid and potentially misleading.