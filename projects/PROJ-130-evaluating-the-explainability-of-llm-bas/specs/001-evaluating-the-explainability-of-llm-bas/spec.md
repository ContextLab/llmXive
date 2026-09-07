# Specification: Evaluating the Explainability of LLM-Based Bug Fixes

## 1. Introduction

### 1.1 Purpose
This document defines the requirements for a research pipeline that evaluates the
explainability of Large Language Model (LLM)-generated bug fixes. The system
generates patches for bugs from the Defects4J dataset, assesses their correctness,
and computes explainability metrics (attention, saliency, and internal coherence).

### 1.2 Scope
The project covers data ingestion, patch generation, test execution, explainability
metric computation, and statistical analysis. It does not cover the training of
the LLM itself or the deployment of a web interface.

## 2. User Stories

### US-1: Generate Patches and Assess Correctness
As a researcher, I want to automatically generate bug fixes using an LLM and
determine if they pass the original test suite, so that I can establish a ground
truth for correctness.

**Acceptance Criteria:**
1. Defects4J v2.0 data is downloaded and verified.
2. Patches are generated for selected bugs using CodeLlama-7B-Instruct.
3. Test suites are executed with a timeout; pass/fail/unsafe status is recorded.

### US-2: Extract Explainability Scores
As a researcher, I want to compute attention weights, saliency maps, and rationale
coherence scores for generated patches, so that I can quantify the explainability
of the model's decisions.

**Acceptance Criteria:**
1. Attention weights are extracted from the last decoder layer.
2. Integrated Gradients saliency is computed for tokenized diffs.
3. **Rationale coherence is computed as the cosine similarity between the
 generated rationale and the semantic embedding of the code change.**
4. **Output includes a `coherence_score` for each processed patch.**

### US-3: Statistical Analysis and Correlation Testing
As a researcher, I want to correlate explainability scores with correctness
labels and complexity metrics, so that I can determine if more explainable
fixes are more likely to be correct.

**Acceptance Criteria:**
1. Point-biserial correlations are computed.
2. Logistic regression models are fit and evaluated via AUC-ROC.
3. Bonferroni-corrected p-values are reported.

## 3. Functional Requirements

### FR-001: Data Ingestion
The system must download Defects4J v2.0 from the official GitHub repository and
verify the SHA256 checksum.

### FR-002: Patch Generation
The system must prompt CodeLlama-7B-Instruct (16-bit CPU) to generate patches
and rationale text.

### FR-003: Test Execution
The system must execute the Defects4J test suite with a 60s timeout per bug.

### FR-004: Attention Extraction
The system must extract per-token attention weights from the last decoder layer.

### FR-005: Saliency Computation
The system must compute Integrated Gradients saliency magnitude using Captum.

### FR-006-REV: Internal Coherence (Replaces FR-006)
**The system must compute the internal coherence of generated rationales by
calculating the cosine similarity between the rationale text embedding and the
code change semantic embedding using `sentence-transformers/all-MiniLM-L6-v2`.**
**The system must output a `coherence_score` (float) representing this similarity.**
**If no rationale is provided, the score is recorded as null.**

### FR-007: Correlation Analysis
The system must compute point-biserial correlations between scores and correctness.

### FR-008: Predictive Modeling
The system must fit logistic regression models to predict correctness from scores.

### FR-009: Statistical Significance
The system must perform paired t-tests with Bonferroni correction.

### FR-010: Error Handling
The system must log invalid patches, timeouts, and missing rationales.

### FR-011: Reproducibility
The system must pin random seeds and record model revisions.

### FR-012: Data Verification
The system must verify data integrity via checksums.

## 4. Scenario Definitions

### SC-001: Data Download
1. System downloads `defects4j-v2.0.0.zip`.
2. System verifies SHA256 checksum.
3. System extracts to `data/defects4j/`.

### SC-002: Patch Generation
1. System loads bug `Lang-1`.
2. System prompts LLM with reference text.
3. System receives patch and rationale.

### SC-003: Test Execution
1. System applies patch to `Lang-1`.
2. System runs tests.
3. System records `pass` if all tests pass.

### SC-004: Attention Extraction
1. System loads generated patch.
2. System extracts attention weights.
3. System saves heatmap.

### SC-005: Saliency Computation
1. System tokenizes patch.
2. System runs Integrated Gradients.
3. System saves saliency magnitude.

### SC-006: Coherence Computation
1. System loads rationale text and code change.
2. System computes embeddings.
3. System calculates cosine similarity.

### SC-007: Coherence Score Range Definition
**The system defines the expected range for the cosine similarity score (`coherence_score`)
as [0, 1], where 1 indicates perfect semantic alignment and 0 indicates orthogonality.**
**A threshold of `>= 0.6` is used to flag a rationale as "coherent" for downstream analysis.**

### SC-008: Statistical Analysis
1. System loads scores and correctness labels.
2. System computes correlations and p-values.
3. System saves results.

## 5. Non-Functional Requirements

### NFR-001: Performance
The system must process bugs within a reasonable timeframe (e.g., < 5 minutes per bug
excluding model generation time).

### NFR-002: Resource Constraints
The system must run on CPU with 16-bit precision for the LLM.

### NFR-003: Reproducibility
All experiments must be reproducible with pinned seeds and recorded metadata.

## 6. Glossary

- **Defects4J**: A dataset of real Java bugs.
- **Coherence**: The semantic alignment between the rationale and the code change.
- **Saliency**: The importance of input tokens to the model's output.
- **Attention**: The weight assigned to input tokens by the model.