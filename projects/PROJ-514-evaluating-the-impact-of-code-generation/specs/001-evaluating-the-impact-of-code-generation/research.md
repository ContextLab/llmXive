# Research: Evaluating Code Generation Impact on Code Smell Frequency

## Project ID
PROJ-514-evaluating-the-impact-of-code-generation

## Balanced Blocked Design Implementation

This document summarizes the current implemented design for the study, reflecting the "Balanced Blocked Design" strategy adopted to ensure statistical validity and repository-level matching.

### Design Overview
The study employs a **Balanced Blocked Design** where code samples are collected in matched sets from the same repositories to control for repository-specific coding styles and environments.

**Sample Allocation**:
- **Human-Written Samples**: 150 samples (3 samples × 50 repositories)
- **LLM-Generated Samples**: 150 samples (3 samples × 50 tasks derived from human issues)
- **Total Dataset**: 300 samples

This allocation ensures equal statistical power for both groups, facilitating robust permutation testing without the imbalance issues inherent in the original aspirational 1000/50 split.

### Implementation Details

1. **Repository Selection**:
 - 50 distinct repositories selected based on GitHub API criteria (`stars:>100`, `created:<5 years`).
 - Each repository must have at least 3 distinct commits adding `.py` or `.java` files.
 - Repositories are sorted by stars (descending) then name (ascending) for deterministic selection.

2. **Human Sample Extraction**:
 - For each of the 50 repositories, exactly 3 commits adding code are extracted.
 - Function-level code is isolated and saved with full metadata (commit SHA, issue URL, file path).
 - Source: `code/01_data_collection/fetch_human_samples.py`

3. **LLM Sample Generation**:
 - Tasks are derived from the issue descriptions of the human samples (`data/intermediate/tasks.json`).
 - 3 samples generated per task using HuggingFace Inference API with pinned random seeds.
 - Source: `code/01_data_collection/generate_llm_samples.py`

4. **Blocking Variable**:
 - The `repository_id` serves as the blocking variable in the statistical analysis.
 - This controls for inter-repository variance, isolating the effect of the generation source (Human vs. LLM).

### Deviation from Original Spec
The original specification (Section 4.3 of `spec.md`) initially proposed an aspirational 1000 human / 50 LLM split. Due to practical constraints in LLM generation costs and the statistical need for balanced groups for permutation testing, this design was updated to a **150/150 balanced split**.

- **Reason for Change**: To ensure sufficient power for the Blocked Permutation Test and to avoid the high variance associated with highly unbalanced sample sizes in non-parametric tests.
- **Reference**: See `spec.md`, Section 4.3 "Deviation Log" for the official record of this design change.

### Data Hygiene & Traceability
- All samples are validated for syntax correctness.
- SHA-256 checksums are calculated for every file and recorded in `state/projects/PROJ-514-evaluating-the-impact-of-code-generation.yaml`.
- Full API logs (commit SHAs, issue URLs, prompt hashes) are stored in `data/raw/api_logs.json`.

### Next Steps
Proceed to User Story 2 (Static Analysis) to compute smell metrics for the 300 samples, followed by User Story 3 (Statistical Comparison) to execute the Blocked Permutation Test.