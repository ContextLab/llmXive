# Golden Set Creation Process

This document describes the manual process for creating the **Golden Set**, a curated dataset of student interactions labeled by domain experts with cognitive load scores. This dataset is critical for validating the Cognitive Load Estimation Model (User Story 1).

## Overview

The Golden Set serves as the ground truth for model validation. It consists of:
1. **Interaction Data**: Raw or processed student interaction logs (e.g., from ASSISTments or OULAD).
2. **Expert Labels**: Cognitive load scores (0–100) assigned by human experts based on a standardized rubric.

**Important**: This process is **manual** and **cannot be automated**. The `code/` directory contains scripts to generate the *template* for this process, but the actual labeling requires human domain expertise to ensure validity and avoid the "illusion of competence."

## Prerequisites

Before beginning, ensure the following:
- The project structure is initialized (Task T001).
- The `golden_set_template.csv` has been generated (Task T007).
- Domain experts (e.g., educational psychologists, experienced instructors) are available to perform the labeling.

## Step 1: Generate the Template

Run the following command to generate the initial template file. This file contains the interaction data but leaves the `expert_load_score` column empty for manual entry.

```bash
python code/generate_golden_set_template.py
```

This will create:
- `data/processed/golden_set_template.csv`: The spreadsheet-ready file for experts.
- `data/processed/golden_set_template_README.md`: Instructions for experts (automatically generated).

## Step 2: Expert Labeling Process

### The Rubric
Experts must assign a cognitive load score (0–100) to each interaction based on the following criteria:

| Score Range | Cognitive Load Level | Indicators (Behavioral Proxies) |
|:--- |:--- |:--- |
| **0–20** | Very Low | Immediate correct response, minimal hints, low latency, high confidence. |
| **21–40** | Low | Quick correct response, occasional hints, moderate latency. |
| **41–60** | Moderate | Correct response after some struggle, multiple hints, variable latency. |
| **61–80** | High | Incorrect responses, many hints, high latency, signs of frustration (e.g., rapid guessing). |
| **81–100** | Very High | Persistent errors, excessive hints, very high latency, or abandonment. |

### Instructions for Experts
1. Open `data/processed/golden_set_template.csv` in a spreadsheet editor (e.g., Excel, Google Sheets) or a CSV editor.
2. Review the `interaction_id` and associated features (e.g., `latency`, `hint_count`, `error_count`).
3. Assign an integer value between 0 and 100 to the `expert_load_score` column for each row.
4. **Do not** leave any rows blank. If an interaction is ambiguous, assign a score based on the most likely cognitive state and add a note in a separate log file.
5. Save the file as `golden_set.csv` (overwriting the template or creating a new version).

## Step 3: Validation and Integration

Once the experts have completed the labeling:

1. **Verify Data Integrity**: Ensure the file `data/processed/golden_set.csv` exists and contains:
 - At least 50 rows.
 - A valid `expert_load_score` column with values in the range [0, 100].
2. **Run Validation Script**: Execute the validation pipeline to confirm the data is ready for model training.

```bash
python code/validate_and_load_golden_set.py
```

If the validation passes, the pipeline will generate `validation_source.txt` and the model training (Task T015) can proceed.

## Troubleshooting

### "Validation Data Missing" Error
If the pipeline halts with "Validation Data Missing: Golden Set or required interaction features...", it means:
- `data/processed/golden_set.csv` does not exist, OR
- The file has fewer than 50 rows, OR
- The `expert_load_score` column contains invalid values.

**Action**: Re-run Step 2 to ensure all rows are labeled and the file is saved correctly.

### Synthetic Data Warning
**NEVER** use synthetic or randomly generated scores for the Golden Set. The model's validity depends on the quality of human expert judgment. Using synthetic data will result in a model that fails to generalize to real-world cognitive states.

## References

- **Task T007**: Generate Golden Set Template
- **Task T007c**: Validate and Load Golden Set
- **Task T015**: Train Load Model (requires Golden Set)
- **Research Note**: This process addresses the "illusion of competence" by relying on expert behavioral analysis rather than self-reported ease.