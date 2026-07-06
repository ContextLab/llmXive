# Implementation Plan: Assessing the Trade-offs Between Static and Dynamic Analysis for LLM-Generated Code

**Branch**: `001-llm-analysis-tradeoffs` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-assessing-the-trade-offs-between-static/spec.md`

## Summary

This feature implements a research pipeline to assess the trade-offs between static analysis (security-focused) and dynamic analysis (functional correctness) for LLM-generated code. The system downloads code snippets from HumanEval, HumanEval-X, CodeXGLUE, and BigCode (TheStack). It executes static tools (CodeQL, SonarQube, with fallbacks) and dynamic unit tests. 

**Critical Methodological Revision**: 
- The plan explicitly **rejects** the use of Precision, Recall, and F1-score for static analysis due to the lack of security ground truth (per Spec Assumptions). Instead, it calculates **Issue Detection Rate** (issues found per snippet).
- The plan explicitly **rejects** McNemar's test for comparing static security vs. dynamic correctness, as they measure distinct constructs. Instead, it uses **Spearman's Rank Correlation** or **Chi-squared Test of Independence** to assess the association between static issue density and dynamic pass/fail status.
- **BigCode (TheStack)** samples are used for **Static-Only** analysis. They are excluded from the comparative statistical test (which requires paired dynamic oracles) but included in the "Static Detection Rate" report.
- **Java/JS** samples are sourced from HumanEval-X and CodeXGLUE to ensure unit tests exist. If a language stratum has <30 samples, it is excluded from stratified testing and reported as a limitation.

The implementation strictly adheres to resource constraints (2 CPU, 7GB RAM, 6h runtime) and reproducibility principles.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `pandas`, `scipy`, `pytest`, `requests`, `pyyaml`, `codeql-cli` (external binary), `sonar-scanner` (external binary)  
**Storage**: Local filesystem (`data/`), JSON logs for analysis results  
**Testing**: `pytest` (for pipeline unit tests), integration tests via GitHub Actions  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Research CLI / Data Pipeline  
**Performance Goals**: Complete analysis of ≥500 snippets within 6 hours on 2 CPU cores  
**Constraints**: CPU ≤ 2 cores, RAM ≤ 7 GB, Disk ≤ 14 GB, No GPU, No heavy LLM inference  
**Scale/Scope**: A diverse set of code snippets across Python, JavaScript, and Java (with stratification logic)  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All scripts pinned in `requirements.txt`; random seeds set; datasets fetched from canonical HuggingFace URLs; checksums recorded in `state/`. |
| **II. Verified Accuracy** | All dataset URLs cited strictly from the `# Verified datasets` block; no invented URLs; citations validated against primary sources. |
| **III. Data Hygiene** | Raw data downloaded to `data/raw/` with checksums; transformations write to `data/processed/`; no in-place modification; PII scan enabled. |
| **IV. Single Source of Truth** | All metrics in `paper/` derived directly from `data/processed/analysis_results.csv`; no hand-typed numbers. |
| **V. Versioning Discipline** | **Artifact Hashing Step**: A script `code/hash_artifacts.py` will generate SHA-256 hashes for all data/code and update `state/projects/...yaml` under `artifact_hashes`. |
| **VI. Toolchain Consistency** | **Tool Versioning Step**: CodeQL and SonarQube versions will be pinned in `requirements.txt` (via wrapper scripts or version strings) and logged in `state/` under `tool_versions`. |
| **VII. Benchmark Representativeness** | Stratified sampling (Python, JS, Java) enforced; sample IDs recorded in `data/manifest.csv`; sample size ≥ 500 (or max available with limitation reporting). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llm-analysis-tradeoffs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── analysis_log.schema.yaml
    ├── analysis_results.schema.yaml
    ├── dataset_manifest.schema.yaml
    └── statistical_report.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-227-assessing-the-trade-offs-between-static-/
├── data/
│   ├── raw/                 # Downloaded datasets (checksummed)
│   ├── processed/           # Cleaned snippets, merged logs
│   └── manifest.csv         # Sample IDs and language stratification
├── code/
│   ├── __init__.py
│   ├── download.py          # Data ingestion (FR-001)
│   ├── static_analysis.py   # CodeQL/SonarQube execution (FR-002)
│   ├── dynamic_analysis.py  # Unit test execution (FR-003)
│   ├── aggregation.py       # Metrics calculation (FR-004 - Revised)
│   ├── statistics.py        # Correlation/Chi-squared & sensitivity (FR-005, FR-007, FR-008 - Revised)
│   ├── hash_artifacts.py    # Versioning step (Constitution V)
│   └── main.py              # Orchestration script
├── tests/
│   ├── unit/                # Unit tests for pipeline components
│   └── integration/         # End-to-end pipeline tests
├── requirements.txt         # Pinned dependencies
└── state/
    └── projects/PROJ-227-assessing-the-trade-offs-between-static-.yaml
```

**Structure Decision**: Single project structure chosen for simplicity and alignment with research CLI requirements. No frontend/backend split needed; all processing is local and sequential.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | Constitution Check passed with full compliance. | N/A |

## Methodology & Execution Flow

### 1. Data Ingestion (FR-001)
- Download datasets from verified HuggingFace URLs (HumanEval, HumanEval-X, CodeXGLUE, TheStack).
- Verify checksums; abort on corruption.
- Parse snippets; extract code and test cases.
- **Stratification Validation**: Count samples per language. If any language has n < 30, flag for exclusion from stratified tests.
- **BigCode Handling**: TheStack samples are marked `static_only` (no dynamic oracle) and excluded from comparative tests.

### 2. Static Analysis (FR-002)
- **Primary Tools**: CodeQL (for security queries), SonarQube (for code smells/vulnerabilities).
- **Fallback**: PyLint (Python), ESLint (JavaScript) if primary tools fail.
- **Execution**: Run on each snippet; log results in `analysis_log.schema.yaml` format.
- **Timeout**: 15 minutes per snippet (aggregate limit).
- **Resource Limit**: Abort if CPU > 2 cores or RAM > 7 GB.
- **Output**: `Issue Detection Rate` (issues per snippet).

### 3. Dynamic Analysis (FR-003)
- **Oracle**: Unit tests from HumanEval/HumanEval-X/CodeXGLUE (pass/fail).
- **Execution**: Run tests via `pytest` (Python) or equivalent for JS/Java.
- **Handling Missing Tests**: Mark as `untestable_dynamic`; **exclude from comparative metrics** but include in static-only reporting if applicable.
- **Timeout**: 30 minutes per snippet.
- **Output**: `Pass Rate` (pass/fail status).

### 4. Aggregation & Statistics (FR-004, FR-005, FR-007, FR-008 - Revised)
- **Metrics**: 
  - Static: **Issue Detection Rate** (count of issues / total snippets).
  - Dynamic: **Pass Rate** (count of passes / total snippets with oracle).
  - **No Precision/Recall/F1** (ground truth unavailable).
- **Statistical Test**: 
  - **Spearman's Rank Correlation** or **Chi-squared Test of Independence** between static issue count and dynamic pass/fail status.
  - **No McNemar's Test** (inappropriate for distinct constructs).
  - Stratify by language if n ≥ 30 per stratum.
- **Sensitivity Analysis**: Sweep α over a range of small significance levels to evaluate model sensitivity. (FR-007).
- **Multiplicity Adjustment**: Apply Bonferroni correction to **independent statistical tests** (e.g., across languages), not derived metrics (FR-008).

### 5. Versioning & Hashing (Constitution V)
- Run `code/hash_artifacts.py` to generate SHA-256 hashes for all data/code artifacts.
- Update `state/projects/...yaml` with `artifact_hashes` and `tool_versions`.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Insufficient Java samples** | Use all available; if n < 30, exclude from stratified test and report limitation. |
| **Static tool crashes** | Retry up to 3 times; fallback to PyLint/ESLint; log `tool_failure`. |
| **Timeout during dynamic execution** | Mark as `timeout`; exclude from runtime metrics. |
| **Resource exhaustion** | Enforce CPU/RAM limits; abort with error code. |
| **No security ground truth** | Use "Issue Detection Rate" instead of Precision/Recall; frame findings as associational. |
| **BigCode lack of tests** | Use for static-only reporting; exclude from comparative statistical test. |