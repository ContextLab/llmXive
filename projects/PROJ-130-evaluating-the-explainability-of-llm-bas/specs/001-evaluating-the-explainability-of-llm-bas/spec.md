# Specification: Evaluating the Explainability of LLM-Based Bug Fixes

## 1. Introduction

This project evaluates the explainability of Large Language Model (LLM) generated bug fixes using the Defects4J dataset. We analyze three dimensions: Attention-based heatmaps, Integrated Gradients saliency, and internal coherence of generated rationales.

## 2. User Stories

### US-1: Generate Patches and Assess Correctness
**As a** researcher,
**I want** to generate bug fixes using CodeLlama-7B-Instruct and validate them against the Defects4J test suites,
**So that** I have a ground-truth labeled dataset of correct vs. incorrect LLM patches.

**Acceptance Criteria:**
1. System downloads Defects4J v2.0 and extracts to `data/defects4j/`.
2. System generates patches and rationale text for each bug.
3. System executes test suites and records pass/fail/unsafe status.
4. Output includes `state/correctness_labels.json`.

### US-2: Extract Explainability Scores
**As a** researcher,
**I want** to compute attention weights, saliency maps, and coherence scores for generated patches,
**So that** I can quantify how well the model's internal mechanisms align with the code changes and its own explanations.

**Acceptance Criteria:**
1. System extracts attention weights from the last decoder layer.
2. System computes Integrated Gradients saliency for tokenized diffs.
3. System computes the internal coherence of generated rationales against the code change semantics using cosine similarity.
4. Output includes `explanations/<bug-id>_metadata.json` containing `attention_score`, `saliency_score`, and `coherence_score`.

**Acceptance Scenario 3 (Coherence):**
Given a generated patch and its rationale text:
1. The system encodes the rationale and the diff content using `sentence-transformers/all-MiniLM-L6-v2`.
2. The system calculates the cosine similarity between the two vectors.
3. The system records `coherence_score` (a float between 0 and 1) in the metadata file.
4. If the rationale is missing, the system records `coherence_score` as `null` and logs the event.

### US-3: Statistical Analysis and Correlation Testing
**As a** researcher,
**I want** to correlate explainability scores with patch correctness,
**So that** I can determine if higher explainability metrics predict correct bug fixes.

**Acceptance Criteria:**
1. System computes point-biserial correlations.
2. System fits logistic regression models and computes AUC-ROC.
3. System performs paired t-tests with Bonferroni correction.
4. Output includes `state/statistical_results.json`.

## 3. Functional Requirements

### FR-001: Data Ingestion
The system must download Defects4J v2.0 from the official GitHub repository, verify the SHA256 checksum, and extract it to `data/defects4j/`.

### FR-002: Patch Generation
The system must use CodeLlama-7B-Instruct (16-bit precision, temperature=0.7) to generate patches and rationale text.

### FR-003: Test Execution
The system must execute the Defects4J test suite with a 60s timeout per bug to determine correctness.

### FR-004: Attention Extraction
The system must extract per-token attention weights from the last decoder layer.

### FR-005: Saliency Computation
The system must apply Captum's Integrated Gradients to compute saliency magnitude.

### FR-006-REV: Internal Coherence (Replaces FR-006)
The system must compute the internal coherence of generated rationales against code change semantics using semantic similarity (cosine similarity).
- **Metric**: Cosine Similarity between the embedding of the rationale text and the embedding of the diff content.
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`.
- **Threshold**: A `coherence_score` >= 0.6 indicates valid coherence.
- **Handling**: Missing rationales result in a `null` score and a log entry.
- **Note**: This requirement overrides the previous FR-006 which specified BLEU/ROUGE metrics, as BLEU/ROUGE are unsuitable for evaluating semantic coherence of free-text rationales.

### FR-007: Correlation Analysis
The system must compute point-biserial correlations between explainability scores and correctness labels.

### FR-008: Predictive Modeling
The system must fit logistic regression models to predict correctness from explainability scores.

### FR-009: Statistical Significance
The system must perform paired t-tests with Bonferroni correction.

### FR-010: Timeout Handling
The system must handle test execution timeouts as "unsafe" or "inconclusive" states.

### FR-011: Reproducibility
The system must pin random seeds and record model revisions.

### FR-012: Integrity Verification
The system must verify dataset integrity via checksums.

## 4. Scenarios

### SC-001: Dataset Download
Given a clean environment, when the download script runs, then `data/defects4j/` contains the extracted dataset and the checksum matches the release page.

### SC-002: Patch Generation
Given a bug from Defects4J, when the generation script runs, then a patch file and rationale text are saved.

### SC-003: Correctness Labeling
Given a patch, when the test execution script runs, then the output contains `pass`, `fail`, or `unsafe`.

### SC-004: Attention Heatmap
Given a generated patch, when the attention extraction script runs, then a heatmap image is saved.

### SC-005: Saliency Map
Given a generated patch, when the saliency script runs, then a saliency magnitude value is recorded.

### SC-006: Coherence Calculation
Given a rationale and a diff, when the coherence script runs, then a `coherence_score` between 0 and 1 is recorded.

### SC-007: Coherence Score Range Definition
The `coherence_score` is defined as the cosine similarity between two vectors.
- **Expected Range**: [0, 1] (after normalization, though raw cosine similarity is [-1, 1], the context of semantic similarity for this task implies positive alignment is expected; however, the raw metric is cosine similarity).
- **Clarification**: The raw output of `cosine_similarity` from `scikit-learn` or `sentence-transformers` is in the range [-1, 1]. For the purpose of this study, scores in the range [0, 1] indicate positive semantic alignment, while negative scores indicate dissimilarity. The acceptance threshold of 0.6 specifically targets strong positive alignment.
- **Output Format**: The `coherence_score` in `metadata.json` will be a float representing the raw cosine similarity value.

## 5. Data Model

### Bug
- `id`: string (Defects4J bug ID, e.g., "Lang-1")
- `file_path`: string
- `test_suite`: list of strings
- `reference_text`: string (optional, ground truth)

### Patch
- `id`: string
- `bug_id`: string
- `diff_content`: string
- `rationale_text`: string

### CorrectnessLabel
- `bug_id`: string
- `pass_fail`: boolean (or "pass"/"fail"/"unsafe")
- `unsafe_flag`: boolean

### ExplainabilityScore
- `bug_id`: string
- `attention_score`: float (aggregated)
- `saliency_score`: float
- `coherence_score`: float | null

### StatisticalResult
- `correlation_coeff`: float
- `auc_roc`: float
- `p_value`: float

## 6. Non-Functional Requirements

### NFR-001: Performance
Test execution must complete within 60 seconds per bug.

### NFR-002: Reliability
The system must handle missing rationales gracefully (log and continue).

### NFR-003: Reproducibility
All random seeds must be pinned; model revisions must be recorded.

### NFR-004: Resource Constraints
CodeLlama-7B-Instruct must run in 16-bit precision on CPU.