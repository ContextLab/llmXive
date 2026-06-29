# Feature Specification: Evaluating the Explainability of LLM-Based Bug Fixes

**Feature Branch**: `001-evaluating-explainability`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How well do different explainability techniques (attention visualization, code‑diff saliency maps, and generated natural‑language rationales) reflect the actual correctness and safety of bug fixes suggested by large language models for source‑code defects?"

## User Scenarios & Testing *(mandatory)*

### US-1 - Generate Patches and Assess Correctness (Priority: P1)

For each bug in the Defects4J dataset, generate a code patch using CodeLlama-7B-Instruct and determine whether the patch passes the test suite without introducing new failures.

**Why this priority**: This is the foundational data layer—without correctness labels (pass/fail/unsafe), no explainability analysis can proceed. This delivers the ground truth against which all explanation methods are evaluated.

**Independent Test**: Can be fully tested by running the patch generation pipeline on 50 bugs and verifying that each produces a binary correctness label (pass/fail) plus an unsafe flag if new test failures occur.

**Acceptance Scenarios**:

1. **Given** a buggy source file and failing test description from Defects4J, **When** the system prompts CodeLlama-7B-Instruct, **Then** the system outputs a patch in diff format and a correctness label after running the test suite
2. **Given** a generated patch, **When** the system applies it and runs all associated tests, **Then** the system records pass/fail status and flags any new test failures as unsafe changes
3. **Given** a target sample of 50 bugs from Defects4J v2.0, **When** the pipeline completes, **Then** valid correctness labels are recorded for the maximum feasible subset (coverage rate is a feasibility target, not a hard requirement)

---

### US-2 - Extract Explainability Scores (Priority: P2)

For each generated patch, compute three explainability metrics: attention weights on edited tokens, Integrated Gradients saliency on the diff, and BLEU/ROUGE similarity between generated and reference rationales.

**Why this priority**: This delivers the predictor variables for the core research question. Without these scores, we cannot measure the relationship between explanation fidelity and fix quality.

**Independent Test**: Can be fully tested by processing 10 patches and verifying that each produces three numerical scores (attention weight, saliency magnitude, BLEU/ROUGE) in the expected ranges.

**Acceptance Scenarios**:

1. **Given** a generated patch and the model's forward pass, **When** the system extracts attention weights from the last decoder layer, **Then** the system outputs file-level aggregated attention scores for edited tokens
2. **Given** a tokenized diff, **When** the system applies Captum's Integrated Gradients, **Then** the system outputs summed saliency magnitude scores for each edited line
3. **Given** a generated rationale and available reference (human-written explanation, developer commit message, or issue description), **When** the system computes BLEU/ROUGE similarity, **Then** the system outputs a BLEU score between 0-100 (percentage) or 0-1 (normalized) and ROUGE score in the same range

---

### US-3 - Statistical Analysis and Correlation Testing (Priority: P3)

Compute point-biserial correlations between each explainability score and correctness, fit logistic regression models, and perform paired t-tests with Bonferroni correction to compare predictive power.

**Why this priority**: This delivers the research findings—the statistical evidence answering whether explainability techniques reflect fix correctness. This is the final output that validates or challenges assumptions about interpretability methods.

**Independent Test**: Can be fully tested by running the analysis notebook on pre-computed scores from 50 bugs and verifying that correlation coefficients, logistic regression AUC-ROC values, and p-values are produced with Bonferroni correction applied.

**Acceptance Scenarios**:

1. **Given** 50 bugs with correctness labels and explainability scores, **When** the system computes point-biserial correlations, **Then** the system outputs correlation coefficients (r_pb) and p-values for each technique
2. **Given** the same dataset, **When** the system fits logistic regression models, **Then** the system outputs AUC-ROC scores and odds ratios for each explainability predictor
3. **Given** three paired technique comparisons, **When** the system performs t-tests, **Then** the system outputs Bonferroni-corrected p-values with α = 0.05

---

### Edge Cases

- What happens when a generated patch fails to apply cleanly (merge conflict or syntax error)? → The system records the patch as "invalid" and excludes it from statistical analysis, logging the error count
- How does the system handle bugs where Defects4J lacks human-written rationales for BLEU/ROUGE comparison? → The system records BLEU/ROUGE as `[missing]` and excludes those cases from rationale-based analysis, logging the count
- What happens when the model times out or fails to generate a patch within the CPU budget? → The system retries up to 3 times; after 3 failed attempts, the bug is marked "generation_failed" and excluded from analysis
- How does the system handle test suite timeouts exceeding 60 seconds per bug? → The system enforces a 60-second timeout per test run; timeouts are recorded as "timeout" and excluded from correctness labels

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download a standard bug repository dataset and extract buggy source files with associated test suites (See US-1)
- **FR-002**: System MUST prompt CodeLlama-Instruct with buggy files and failing test descriptions to generate patches in diff format (See US-1)
- **FR-003**: System MUST execute each generated patch against the Defects4J test suite and record binary pass/fail outcome plus unsafe flag for new failures (See US-1)
- **FR-004**: System MUST extract per-token attention weights from the last decoder layer and aggregate to file-level heatmaps for edited tokens (See US-2)
- **FR-005**: System MUST apply Captum's Integrated Gradients to tokenized diffs and compute summed saliency magnitude scores for edited lines (See US-2)
- **FR-006**: System MUST compute BLEU and ROUGE similarity between generated rationales and reference text (developer commit messages, issue descriptions, or human-written explanations where available) (See US-2)
- **FR-007**: System MUST compute point-biserial correlation between each explainability score and binary correctness outcome (See US-3)
- **FR-008**: System MUST fit logistic regression models to predict correctness from explainability scores and evaluate via AUC-ROC (See US-3)
- **FR-009**: System MUST perform paired t-tests comparing predictive power of the three techniques with α = 0.05 and Bonferroni correction (See US-3)
- **FR-010**: System MUST enforce a 60-second timeout per test run and exclude timeout cases from correctness labels (See US-1)
- **FR-011**: System MUST pin random seeds in all stochastic operations (model inference, data sampling, statistical resampling) to ensure reproducibility (See US-1, US-2, US-3)
- **FR-012**: System MUST record dataset checksums (the designated defect dataset) and model revision identifiers (CodeLlama-7B-Instruct commit/tag) in the output metadata (See US-1, US-2, US-3)

### Key Entities

- **Bug**: A Defects4J defect with buggy source files, test suite, and optional reference text (commit message, issue description, or human-written rationale)
- **Patch**: A generated code diff modifying buggy files to fix the defect
- **CorrectnessLabel**: Binary pass/fail outcome plus unsafe flag derived from test suite execution
- **ExplainabilityScore**: Three numerical metrics (attention weight, saliency magnitude, BLEU/ROUGE) per patch
- **StatisticalResult**: Correlation coefficients, AUC-ROC values, and Bonferroni-corrected p-values from analysis

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Point-biserial correlation coefficient (r_pb) between each explainability score and correctness is measured against the Defects4J ground-truth test suite outcomes (See US-3)
- **SC-002**: Logistic regression AUC-ROC for predicting correctness from explainability scores is measured against the same test suite ground truth (See US-3)
- **SC-003**: Bonferroni-corrected p-values for paired t-tests are measured against the α = 0.05 significance threshold (See US-3)
- **SC-004**: Dataset-variable fit is measured against the Defects4J v2.0 schema to confirm all required variables (buggy files, test suites, optional reference text) are present (See US-1)
- **SC-005**: Multiplicity correction is measured against the number of hypothesis tests performed (3 techniques × 2 tests = 6 comparisons) to verify Bonferroni adjustment is applied (See US-3)
- **SC-006**: Power limitation is documented as a constraint with sample size of 50 bugs; power analysis is deferred to implementation phase (See US-3)
- **SC-007**: Explainability scores are measured against expected numerical ranges for attention weights (0-1), saliency magnitudes (0-∞), and BLEU/ROUGE scores (0-100 or 0-1) to confirm valid output (See US-2)

## Assumptions

- A bug dataset contains buggy source files and test suites; human-written rationales are NOT available as a standard dataset component. Where reference text is required for BLEU/ROUGE computation, the system will use developer commit messages or issue descriptions as alternative references. If no reference text is available for a bug, BLEU/ROUGE will be recorded as `[missing]` and that case excluded from rationale-based analysis.
- The design is observational (no random assignment of patches to bugs), so all findings will be framed as ASSOCIATIONAL, not causal; no causal claims about explainability techniques causing higher correctness will be made
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h per job) is sufficient to process 50 bugs end-to-end; if runtime exceeds a predetermined threshold, the sample size will be reduced accordingly.
- CodeLlama-7B-Instruct will run in 16-bit (default) precision on CPU; 8-bit quantization (load_in_8bit, bitsandbytes) will NOT be used as it requires CUDA and is incompatible with the free-tier runner
- The sample size is chosen based on feasibility.; power analysis is deferred but will be documented as a limitation in the final report
- BLEU/ROUGE similarity will use the standard 4-gram configuration with smoothing; the threshold of BLEU > 30 for "strong predictor" is based on community-standard interpretation of BLEU scores in code-generation literature
- All statistical tests will use the Bonferroni correction for family-wise error control (α_corrected = 0.05 / 6 = 0.0083 for 6 comparisons)
- The 60-second timeout per test run is based on typical Defects4J test execution times; if a bug's test suite regularly exceeds this, it will be excluded from analysis
- Random seeds are pinned to ensure reproducibility of model inference, data sampling, and statistical resampling operations
- Dataset checksums and model revision identifiers are recorded in output metadata to enable replication and audit of the experimental setup