# Specification: Evaluating the Explainability of LLM-Based Bug Fixes

## Overview
This project evaluates the correlation between the explainability of LLM-generated bug fixes and their correctness. We use the Defects4J dataset to generate patches, assess correctness, and compute explainability metrics (attention, saliency, and internal coherence).

## User Stories

### US-1: Generate Patches and Assess Correctness
**Goal**: Download Defects4J, generate patches using CodeLlama-7B-Instruct, and determine correctness via test suite execution.

**Acceptance Criteria**:
1. Defects4J v2.0 is downloaded and extracted to `data/defects4j/`.
2. Patches are generated for each bug using the specified prompt template.
3. Correctness labels (pass/fail/unsafe) are recorded for each patch.
4. Complexity metrics (LOC, cyclomatic) are computed and stored.

### US-2: Extract Explainability Scores
**Goal**: Compute attention weights, Integrated Gradients saliency, and rationale coherence scores.

**Acceptance Criteria**:
1. Attention heatmaps are extracted and saved as images.
2. Saliency magnitudes are computed and saved as numpy arrays.
3. Rationale coherence scores are computed using semantic similarity.
4. All explainability artifacts are saved in the `explanations/` directory.

**Acceptance Scenario 3**:
Given a generated patch with rationale text:
1. The system computes the cosine similarity between the rationale embedding and the code change embedding.
2. The system outputs a `coherence_score` (float) in the range [0, 1].
3. If the rationale is missing, the score is recorded as `null`.

### US-3: Statistical Analysis and Correlation Testing
**Goal**: Compute correlations, fit logistic regression models, and perform paired t-tests.

**Acceptance Criteria**:
1. Point-biserial correlations between scores and correctness are computed.
2. Logistic regression models predict correctness from scores.
3. Paired t-tests with Bonferroni correction are performed.
4. Results are saved to `state/statistical_results.json`.

## Functional Requirements

### FR-001: Data Download
The system shall download Defects4J v2.0 from the official GitHub repository and verify the SHA256 checksum.

### FR-002: Patch Generation
The system shall generate patches using CodeLlama-7B-Instruct with temperature=0.7 and max_tokens=512.

### FR-003: Test Execution
The system shall run the Defects4J test suite with a 60s timeout per bug.

### FR-004: Attention Extraction
The system shall extract per-token attention weights from the last decoder layer.

### FR-005: Saliency Computation
The system shall apply Integrated Gradients to compute saliency magnitudes.

### FR-006-REV: Internal Coherence
The system shall compute the internal coherence of generated rationales using cosine similarity with `sentence-transformers/all-MiniLM-L6-v2`.
- **Metric**: Cosine similarity between rationale embedding and code change embedding.
- **Threshold**: A coherence score >= 0.6 is considered valid.
- **Range**: Expected range is [0, 1].
- **Handling Missing Data**: If rationale text is missing, `coherence_score` is recorded as `null`.

### FR-007: Correlation Analysis
The system shall compute point-biserial correlations between explainability scores and correctness.

### FR-008: Logistic Regression
The system shall fit logistic regression models to predict correctness from scores.

### FR-009: Statistical Testing
The system shall perform paired t-tests with Bonferroni correction (α_corrected = 0.0083).

### FR-010: Timeout Handling
The system shall handle test execution timeouts gracefully.

### FR-011: Random Seed Pinning
The system shall pin random seeds for reproducibility.

### FR-012: Checksum Verification
The system shall verify SHA256 checksums for downloaded data.

## Scenarios

### SC-001: Data Download
Given a network connection, the system downloads Defects4J v2.0 and verifies the checksum.

### SC-002: Patch Generation
Given a bug from Defects4J, the system generates a patch and rationale.

### SC-003: Correctness Assessment
Given a patch, the system runs the test suite and records the result.

### SC-004: Attention Extraction
Given a generated patch, the system extracts attention weights.

### SC-005: Saliency Computation
Given a generated patch, the system computes saliency magnitudes.

### SC-006: Coherence Scoring
Given a rationale and code change, the system computes the cosine similarity score.

### SC-007: Coherence Score Range
Given a computed coherence score, the value must be in the range [0, 1].
- **Definition**: Cosine similarity between two normalized vectors is always in [-1, 1], but for semantic similarity of text embeddings, values are typically in [0, 1] after ReLU or similar processing. The system expects values in [0, 1].

## Data Model

### Bug
- id: str
- file_path: str
- test_suite: str
- reference_text: str

### Patch
- id: str
- bug_id: str
- diff_content: str
- rationale_text: str

### CorrectnessLabel
- bug_id: str
- pass_fail: bool
- unsafe_flag: bool

### ExplainabilityScore
- bug_id: str
- attention_score: float
- saliency_score: float
- coherence_score: float | null

### StatisticalResult
- correlation_coeff: float
- auc_roc: float
- p_value: float

## Non-Functional Requirements

### NFR-001: Reproducibility
The system must be reproducible with pinned random seeds.

### NFR-002: Performance
The system must handle test execution within 60s per bug.

### NFR-003: Accuracy
The system must use verified real data sources (Defects4J).

## Limitations

- CodeLlama-7B-Instruct runs in 16-bit precision on CPU.
- Sample size may be limited by computational resources.
- Coherence scores are based on semantic similarity, which may not perfectly capture human judgment.