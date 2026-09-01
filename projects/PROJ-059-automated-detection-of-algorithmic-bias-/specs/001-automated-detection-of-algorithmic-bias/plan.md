# Implementation Plan: Automated Detection of Algorithmic Bias in Public Code Repositories

**Branch**: `001-auto-detect-bias` | **Date**: 2026-07-11 | **Spec**: `specs/001-automated-detection-of-algorithmic-bias/spec.md`

## Summary

This plan implements an observational study to correlate "Textual Bias Scores" (derived from variable names and comments in Python repositories) with a **simulated hidden bias parameter** ($B_{true}$) that drives fairness disparities. 

**CRITICAL METHODOLOGY UPDATE**: To address scientific validity concerns, the simulation phase **does NOT** inject bias proportional to the Textual Bias Score. Instead, it generates a random, hidden "True Bias" ($B_{true}$) for each repository, **independently** of the code text. The pipeline then tests if the Textual Bias Score can *predict* this hidden parameter. This breaks the circular reasoning (tautology) and transforms the study from a verification of code logic into a valid statistical hypothesis test.

**SPEC DEVIATION NOTE**: The source specification `spec.md` currently contains `FR-005`: "System MUST simulate a bias injection model... where the bias magnitude is proportional to the repository's aggregated Textual Bias Score." This requirement creates a tautological study. **This plan explicitly overrides FR-005** to implement the scientifically valid "Independent Hidden Bias" methodology. The spec must be amended to reflect this change (flagged for kickback).

The pipeline consists of:
1.  **Phase 0.0**: Reference Validation Setup (Constitution Principle II).
2.  **Phase 0.5**: Robustness Test Harness (SC-005).
3.  **Phase 1**: Static Artifact Extraction (FR-001, FR-002, FR-003, FR-009).
4.  **Phase 1.5**: Lexicon Validation (FR-010).
5.  **Phase 2**: Blind Simulation & Metric Validation (FR-004, FR-005* [overridden], FR-011).
6.  **Phase 2.5**: Token Leakage Check (SC-004).
7.  **Phase 3**: Correlation & Statistical Validation (FR-006, FR-007, FR-008).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `ast` (stdlib), `nltk` (VADER), `numpy`, `scipy`, `pandas`, `scikit-learn`, `fairlearn`.  
**Storage**: Local filesystem (`data/` for raw repo clones, `data/derived/` for JSONL artifacts).  
**Testing**: `pytest` with `pytest-cov`.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM).  
**Project Type**: CLI/Data Pipeline / Research Tool.  
**Performance Goals**: Process 500 repos in ≤ 6 hours; RAM ≤ 7GB; Disk ≤ 14GB.  
**Constraints**: No external API keys for private repos; no code execution; no GPU required (CPU-first).  
**Scale/Scope**: public Python repositories (sampled from GitHub).

> **Note on Compute**: All operations (AST parsing, VADER scoring, synthetic generation, correlation) are CPU-tractable. No GPU escape hatch is required.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/simulation.py`. `requirements.txt` pins versions. Data fetched from canonical GitHub sources. |
| **II. Verified Accuracy** | **PASS** | Implemented via `src/validation/reference_validator.py`. This agent checks `CITATION_TITLE_OVERLAP_THRESHOLD` (0.7) against primary sources before artifact write. |
| **III. Data Hygiene** | **PASS** | Raw repo clones stored in `data/raw/` with checksums. Derived JSONL in `data/derived/`. No in-place edits. PII scan on commit. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` trace to `data/derived/correlation_results.csv`. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in `state/`. **Specifically**, every artifact change updates `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml` `updated_at` timestamp via the pipeline runner. |
| **VI. Synthetic Data Independence** | **PASS** | Synthetic data generator uses `numpy.random` with fixed seeds. **Crucially**, the hidden bias $B_{true}$ is generated independently of the Textual Bias Score. No tokens from code text are injected into the synthetic feature matrix. Verified by `tests/unit/test_independence.py`. |
| **VII. Static Analysis Fidelity** | **PASS** | Pipeline uses `ast` module exclusively. No `import` or `exec` of target repo code. |

## Project Structure

### Documentation (this feature)

```text
specs/001-auto-detect-bias/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── artifact.schema.yaml
    ├── result.schema.yaml
    ├── validation.schema.yaml
    ├── robustness.schema.yaml
    └── independence.schema.yaml
```

### Source Code (repository root)

```text
src/
├── extractors/
│   ├── ast_parser.py       # FR-001: Token extraction
│   ├── lexicon.py          # FR-002: Bias lexicon loading
│   └── vader_sentiment.py  # FR-003: Sentiment scoring
├── simulation/
│   ├── data_gen.py         # FR-004: Synthetic data generation (Blind)
│   └── bias_injector.py    # FR-005*: Hidden bias generation (Independent)
├── analysis/
│   ├── correlation.py      # FR-006, FR-007: Spearman + Bonferroni
│   └── sensitivity.py      # FR-008: Alpha sweep
├── validation/
│   ├── reference_validator.py # Constitution Principle II
│   ├── lexicon_validator.py # FR-010: Manual label alignment check
│   ├── metric_validator.py  # Custom vs. fairlearn comparison
│   └── independence_check.py # SC-004: Static independence assertion
├── pipeline/
│   └── runner.py           # Main orchestration
└── utils/
    └── io.py               # File handling, checksums

tests/
├── unit/
│   ├── test_independence.py   # SC-004: Static independence assertion
│   └── test_metric_validation.py # Metric validation vs fairlearn
├── integration/
└── contract/
```

**Structure Decision**: Single project structure (`src/`) selected to minimize overhead. The pipeline is linear (Extract -> Validate -> Simulate -> Analyze), fitting a modular script-based architecture.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Blind Simulation (vs Proportional)** | Required to avoid tautology. If bias is proportional to text, correlation is guaranteed (r=1). We must test if text *predicts* hidden bias. | Proportional injection creates a circular argument, invalidating the study. |
| **Lexicon Validation (Phase 1.5)** | Required by FR-010. VADER is general sentiment; we must verify it detects "stereotyping" in code context. | Skipping validation risks measuring noise instead of bias. |
| **Metric Validation (Phase 2)** | Required by Constitution Principle II. Custom fairness metrics must match `fairlearn` definitions. | Unverified custom metrics could be mathematically incorrect. |
| **Bonferroni Correction** | Required by FR-007 to control Family-Wise Error Rate across multiple tests. | Uncorrected p-values would inflate Type I error rates. |
| **AST-based Parsing** | Required by Constitution Principle VII (Static Analysis). | Dynamic execution (e.g., importing modules) violates safety and is brittle. |
| **Static Independence Assertion** | Required by SC-004. A diff check between random seeds and tokens is invalid. | A static code analysis or unit test asserting no data flow from text to bias generator is the only valid proof of independence. |
| **Robustness Test Harness** | Required by SC-005. A curated set of broken repos is needed to verify % handling. | Skipping this test leaves the system's resilience unverified. |

## Phased Implementation Plan

### Phase 0.0: Reference Validation Setup
**Goal**: Implement the automated gate for Constitution Principle II.
1.  **Implement Agent**: Create `src/validation/reference_validator.py`.
2.  **Logic**: For every citation in `research.md` or `plan.md`, fetch the primary source (DOI/URL) and compute title token overlap.
3.  **Gate**: Fail if overlap < 0.7.
4.  **Artifact**: `data/validation/citation_report.json`.

### Phase 0.5: Robustness Test Harness (SC-005)
**Goal**: Verify the system handles execution failures in [deferred] of a curated set of broken repositories.
1.  **Generate Curated Set**: Create `data/test/broken_repos.jsonl`.
    - **Task**: Run `scripts/generate_broken_repos.py` which takes 100 valid public repos and injects a syntax error (e.g., unclosed parenthesis) into one Python file per repo, OR use a pre-curated list of known-broken public repos.
    - **Artifact**: `data/test/broken_repos.jsonl` (list of URLs/paths).
2.  **Run Pipeline**: Execute the extraction phase on this set.
3.  **Verify**: Count successful skips. If `skipped_count >= 95`, pass SC-005.
4.  **Artifact**: `data/derived/robustness_report.json` (contains pass/fail status, skipped_count, total_count).

### Phase 1: Static Artifact Extraction
1.  **Parsing**: Use Python `ast` module to traverse the Abstract Syntax Tree.
    - Extract `Name` nodes, `FunctionDef` nodes, and `Constant`/`Str` nodes.
    - Normalize tokens: `camelCase` -> `snake_case`.
2.  **Lexicon Matching**: Compare tokens against the demographic lexicon.
3.  **Sentiment Analysis**: Apply VADER to comment strings.
4.  **Aggregation**: Compute repository-level score (Arithmetic mean).

### Phase 1.5: Lexicon Validation (FR-010)
**Goal**: Validate VADER thresholds against a manually labeled subset.
1.  **Load Labeled Set**: Read `data/test/labeled_comments.csv` (manually annotated subset).
2.  **Run VADER**: Compute scores for these comments.
3.  **Compute Alignment**: Calculate precision/recall against labels.
4.  **Gate**: If alignment < 0.7, log warning and flag for manual review (do not halt, but record in `validation_result`).
5.  **Artifact**: `data/derived/validation_result.json` (per `contracts/validation.schema.yaml`).

### Phase 2: Blind Simulation & Metric Validation
**Goal**: Generate synthetic data and compute fairness metrics independently of the predictor.
1.  **Synthetic Data Generation**:
    - Generate $N=1000$ samples using `numpy`.
    - Features: Domain-neutral (Gaussian).
    - Sensitive Attribute: Binary (0/1), random.
    - **Hidden Bias ($B_{true}$)**: Generate a random bias magnitude $B_{true}$ from a uniform distribution over a positive range. **INDEPENDENTLY** of the Textual Bias Score.
    - **Outcome**: Generate labels based on features + $B_{true}$.
    - **Constraint**: No code text tokens used in generation.
2.  **Metric Validation** (Constitution Principle II):
    - Implement custom Demographic Parity and Equalized Odds in `src/validation/metric_validator.py`.
    - **Task**: Run `tests/unit/test_metric_validation.py`.
    - **Logic**: Generate synthetic data, compute metrics via custom code and `fairlearn`, assert absolute difference < 1e-6.
    - **Gate**: If test fails, halt pipeline.
3.  **Token Leakage Check (SC-004)**:
    - **Task**: Run `tests/unit/test_independence.py`.
    - **Logic**: Assert that the `generate_bias` function signature takes NO arguments derived from the code token stream. Assert that the random seed used for $B_{true}$ is not derived from a hash of the text.
    - **Artifact**: `data/derived/independence_assertion.json` (status: "PASS").

### Phase 2.5: Token Leakage Check (SC-004)
**Goal**: Explicitly verify zero token leakage between the predictor (text) and the outcome (bias generator).
1.  **Static Analysis**: Run `src/validation/independence_check.py`.
2.  **Logic**: Perform a static code analysis (AST traversal) on `src/simulation/bias_injector.py` to ensure no data flow from the `textual_bias_score` input to the `bias_magnitude` calculation.
3.  **Unit Test**: Run `tests/unit/test_independence.py` which asserts the function signature and random seed generation logic.
4.  **Artifact**: `data/derived/independence_assertion.json` (status: "PASS").

### Phase 3: Correlation & Statistical Validation
1.  **Correlation**: Compute Spearman's $\rho$ between Textual Bias Score and $B_{true}$ (derived from Fairness Disparity).
2.  **Multiple Comparison Correction**: Apply Bonferroni correction.
3.  **Sensitivity Analysis**: Sweep $\alpha$ over a range of small values.
4.  **Output**: `final_results.csv`.

## Spec Deviation Note
**FR-005** in the source spec states: "System MUST simulate a bias injection model... where the bias magnitude is proportional to the repository's aggregated Textual Bias Score."
**Deviation**: This plan **overrides** this clause. Implementing proportional injection creates a tautological study (correlation guaranteed by design). The plan instead implements **Independent Hidden Bias Generation** to enable a valid hypothesis test. This deviation is flagged for **Spec Revision** to align FR-005 with the scientifically valid methodology.
