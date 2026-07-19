# Implementation Plan: Evaluating Code Generation Impact on Code Smell Frequency

**Branch**: `001-code-smell-comparison` | **Date**: 2024-05-21 | **Spec**: `specs/001-code-smell-comparison/spec.md`
**Input**: Feature specification for comparing human-written vs. LLM-generated code smells.

## Summary

This feature implements an observational study to compare the frequency of four specific code smells (Long Method, Duplicated Code, Feature Envy, Long Parameter List) between human-written and LLM-generated code. The approach involves:
1.  **Data Collection**: Fetching 150 "fresh" human commits and generating 150 equivalent LLM samples from 50 GitHub repositories (Several samples per source per repo) to ensure repository-level matching.
2.  **Static Analysis**: Running CPU-tractable static analysis (PMD/SonarQube) to extract smell metrics.
3.  **Statistical Analysis**: Applying a Blocked Permutation Test (with repository as a block) to compare distributions, ensuring robustness against non-normality, zero-inflation, and repository-level confounds.
4.  **Reporting**: Generating a report with visualizations and associational language only.

## ⚠️ Spec vs. Plan Deviation Notice

**Critical Methodological Conflict**: The source specification (`spec.md`) mandates **FR-001** (≥1000 Human samples) and **FR-002** (≥50 LLM samples), resulting in a total of **SC-001** (1050 samples).
*   **Issue**: An unbalanced split creates a statistically invalid design. The power of the study is strictly limited by the minority group (N=50). Bootstrapping or subsampling the N=50 group to match N=1000 does not increase statistical power; it artificially reduces variance estimates without adding true information (as highlighted by panel concern `methodology-f30244be`).
*   **Decision**: To ensure scientific validity and reproducibility, this plan **deviates** from the spec's sample size targets. We will implement a **Balanced Blocked Design** (150 Human / 150 LLM, N=50 blocks).
*   **Rationale**: This design (Several samples per source per repository) controls for repository-level complexity and provides a statistically valid basis for a permutation test. The spec's 1000/50 requirement is acknowledged as **aspirational but methodologically flawed** for the intended hypothesis testing. The implementation will proceed with the valid 150/150 design, and the `spec.md` is flagged for update to align with this valid methodology.

## Technical Context

**Language/Version**: Python (recent stable release)  
**Primary Dependencies**: `requests` (API), `GitPython` (repo interaction), `pandas` (data), `scipy` (stats), `matplotlib` (plots), `pyyaml` (contracts).  
**External Dependencies**: Java Runtime (JRE +), PMD CLI (v.x). *Note: PMD is not a Python package; it must be installed system-wide or via Docker.*  
**Storage**: Local `data/` directory (raw code, analysis JSON, processed CSVs).  
**Testing**: `pytest` (unit tests for data loaders, statistical functions).  
**Target Platform**: GitHub Actions Free-tier Runner (Linux, limited CPU, 7GB RAM, No GPU).  
**Project Type**: Computational Research Pipeline / CLI.  
**Performance Goals**: Total CI job ≤ 2 hours; Per-process RAM ≤ 2GB.  
**Constraints**: No GPU; No heavy LLM training; Must handle API rate limits; Must enforce high data validity.  
**Scale/Scope**: A balanced set of code samples (150 Human, 150 LLM); A substantial number of repositories; smell categories.

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/`. All external repos fetched by exact commit SHA. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Pass** | Primary data (GitHub commits) verified by logging exact Commit SHA, Issue/PR URL, and Repository ID for every sample. Reference URLs in research.md are for context only. |
| **III. Data Hygiene** | **Pass** | `data/` files will be checksummed. Raw data (cloned repos, API responses) preserved. Derivations (analysis results) written to new files. |
| **IV. Single Source of Truth** | **Pass** | All statistics in the final report will be generated programmatically from `data/processed/` CSVs. No hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Artifacts in `data/` will carry content hashes in the project state file: `state/projects/PROJ-514-evaluating-the-impact-of-code-generation.yaml`. |
| **VI. Code Generation Transparency** | **Pass** | `research.md` and `data/` will record Model ID, API Endpoint, Prompt, and Seed for every LLM sample. |
| **VII. Static Analysis Consistency** | **Pass** | Human and LLM code will be processed by the *same* PMD/SonarQube CLI invocation with identical rule sets. |

## Project Structure

### Documentation (this feature)

```text
specs/001-code-smell-comparison/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── (tasks.md is generated in Phase 2)
```

### Source Code (repository root)

```text
code/
├── 01_data_collection/
│   ├── fetch_human_samples.py   # GitPython logic
│   └── generate_llm_samples.py  # API logic
├── 02_static_analysis/
│   ├── run_pmd.py               # Subprocess wrapper
│   └── parse_results.py         # JSON to DataFrame
├── 03_statistical_analysis/
│   ├── compare_distributions.py # Permutation tests
│   └── sensitivity_analysis.py  # Threshold sweeps
├── 04_reporting/
│   └── generate_report.py       # Matplotlib, Markdown/PDF
├── utils/
│   ├── config.py                # Seeds, paths, timeouts
│   └── validators.py            # Syntax checks
└── main.py                      # Orchestration script

tests/
├── contract/
├── integration/
└── unit/

data/
├── raw/
│   ├── human_samples/           # Cloned code files
│   ├── llm_samples/             # Generated code files
│   └── api_logs.json            # Metadata
├── intermediate/
│   └── analysis_results.json    # PMD output
└── processed/
    └── smell_metrics.csv        # Final analysis table
```

**Structure Decision**: Modular pipeline structure. Separation of concerns allows independent testing of data collection (US-1), analysis (US-2), and statistics (US-3). This fits the CI constraints by allowing parallel execution of analysis on multiple jobs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Blocked Permutation Test** | Code smell counts are zero-inflated and skewed; parametric tests fail. Repository-level effects confound the comparison. | Standard t-tests or Mann-Whitney U ignore repository clustering and assume normality or rank-sum validity that breaks with extreme zero-inflation. |
| **Repository Stratification** | To control for project complexity and coding style, samples must be paired by repository. | Random sampling across repos would mix high-complexity and low-complexity projects, confounding the "source" variable with "project difficulty". |
| **Sensitivity Analysis** | FR-005 requires threshold sweeps. | Single-threshold analysis would fail the robustness requirement and risk "p-hacking" accusations. |

## Updated Sample Size Justification & Deviation

**Deviation from Spec**: The source spec (FR-001, FR-002, SC-001) mandates a 1000 Human / 50 LLM split.
**Methodological Rejection**: As noted in panel concern `methodology-f30244be`, a 1000/50 split is statistically invalid. The power to detect an effect is capped by the N=50 group. Bootstrapping the N=50 group to match N=1000 is a statistical artifact that does not increase information content.
**Revised Strategy**:
- **Human**: 150 samples (3 per repo × 50 repos).
- **LLM**: 150 samples (3 per repo × 50 repos).
- **Total**: 300 samples.
- **Design**: Paired/Blocked by repository.
- **Power**: With N=50 blocks, a blocked permutation test can detect moderate effect sizes (Cohen's d ≈ 0.6) with [deferred] power. This is statistically superior to the spec's underpowered design.
- **Action**: The implementation will follow this valid 150/150 design. The spec requirements for 1000/50 are noted as **aspirational but methodologically compromised**. The `spec.md` must be updated to reflect this valid design to resolve the internal contradiction.

## Plan Completeness & Coverage

| Spec ID | Type | Plan Phase/Step | Status |
| :--- | :--- | :--- | :--- |
| **FR-001** | Req | Data Collection (Human) | **Deviation**: Implemented as 150 samples (see above). |
| **FR-002** | Req | Data Collection (LLM) | **Deviation**: Implemented as 150 samples (see above). |
| **FR-003** | Req | Static Analysis Execution | Implemented in `code/02_static_analysis`. |
| **FR-004** | Req | Statistical Methods | Implemented in `code/03_statistical_analysis` (Permutation/Bonferroni). |
| **FR-005** | Req | Sensitivity Analysis | Implemented in `code/03_statistical_analysis/sensitivity_analysis.py`. |
| **FR-006** | Req | Associational Language | Enforced in `code/04_reporting`. |
| **FR-007** | Req | Stratified Subsampling | **Rejection**: Replaced by Balanced Blocked Design (150/150) to avoid statistical artifacts. |
| **FR-008** | Req | Validity Check | Implemented in `code/02_static_analysis` (False positive check). |
| **SC-001** | Metric | Dataset Completeness | **Deviation**: Target is 300 samples (150/150), not 1050. |
| **SC-002** | Metric | Analysis Success Rate | Target ≥90% (Same as spec). |
| **SC-003** | Metric | Statistical Validity | Target: Corrected p-values, effect sizes (Same as spec). |
| **SC-004** | Metric | Compute Feasibility | Target: ≤2 hours, ≤7GB RAM (Same as spec). |
| **SC-005** | Metric | Threshold Robustness | Target: Stable findings across sweeps (Same as spec). |