# Feature Specification: Evaluating the Effectiveness of Retrieval‑Augmented Generation for Code Search

**Feature Branch**: `001-evaluating-rag-code-search`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Evaluating the Effectiveness of Retrieval‑Augmented Generation for Code Search"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproducible RAG vs. Baseline Evaluation Pipeline (Priority: P1)

A researcher needs to run a complete, end-to-end comparison of a Retrieval-Augmented Generation (RAG) system against keyword (BM25) and neural dual-encoder baselines on the CodeSearchNet dataset to determine if RAG provides a measurable performance lift.

**Why this priority**: This is the core value proposition. Without a functioning pipeline that generates the performance metrics (nDCG, Precision@10) for all three methods, no analysis of *why* RAG works can occur. It establishes the ground truth for the entire study. The 45-minute limit for 50 queries is a scaled test constraint; 50 queries × (45 min / 50) = 45 min, which extrapolates to 200 queries in 180 minutes (3 hours), safely within the 6-hour production limit.

**Independent Test**: The system can be tested by executing the pipeline on a subset of CodeSearchNet queries and verifying that it outputs a CSV file containing three distinct rows (one per method) with valid nDCG@10 scores, without requiring any external API calls or GPU resources.

**Acceptance Scenarios**:

1. **Given** the CodeSearchNet Python subset is downloaded and pre-processed, **When** the pipeline executes the RAG, BM25, and Dual-Encoder retrieval steps on 50 test queries, **Then** the system outputs a CSV file where each row contains a query ID, method name, and a calculated nDCG@10 score between 0.0 and 1.0.
2. **Given** the pipeline runs on a CPU-only environment with 2 cores and 7GB RAM, **When** the full retrieval and scoring process completes, **Then** the job finishes within 45 minutes and does not trigger an Out-Of-Memory (OOM) error.
3. **Given** the pipeline is executed with a fixed random seed, **When** the run is repeated immediately, **Then** the resulting nDCG@10 scores for all methods match the previous run exactly (bit-for-bit reproducibility).

---

### User Story 2 - Semantic Descriptor Correlation Analysis (Priority: P2)

A data scientist needs to correlate specific code-level semantic properties (API density, documentation density, naming consistency) with the performance delta (RAG score minus Baseline score) to identify which code characteristics drive RAG superiority.

**Why this priority**: This addresses the specific research question ("What semantic properties... determine whether..."). It transforms raw performance numbers into actionable insights about code structure.

**Independent Test**: The system can be tested by feeding it a pre-computed CSV of performance deltas and code descriptors, verifying that it outputs a JSON report containing Spearman correlation coefficients and p-values for each descriptor against the performance delta.

**Acceptance Scenarios**:

1. **Given** a dataset of 200 queries with calculated performance deltas and three semantic descriptors (API density, doc density, naming consistency), **When** the analysis module runs, **Then** it outputs a correlation matrix showing Spearman's *ρ* and p-values for each descriptor vs. the delta.
2. **Given** the analysis detects a non-normal distribution of performance deltas, **When** the statistical test selection logic runs, **Then** the system automatically switches from a paired t-test to a Wilcoxon signed-rank test for that specific comparison.
3. **Given** the correlation analysis completes, **When** the results are formatted, **Then** the output explicitly flags any correlation with p < 0.05 as "statistically significant" and others as "non-significant" to prevent false-positive interpretation.

---

### User Story 3 - Resource Constraint Degradation Study (Priority: P3)

A DevOps engineer needs to understand how strict resource limits (e.g., 1GB RAM for indexing, 2-layer model for generation) degrade the RAG advantage to determine if the method is viable for lightweight CI/CD environments.

**Why this priority**: This addresses the "under what conditions" part of the research question. It ensures the findings are practical for real-world, resource-constrained deployment scenarios.

**Independent Test**: The system can be tested by running the pipeline with the "strict resource" flags enabled, verifying that the FAISS index size stays below 1GB and the model parameter count is reduced, while still producing valid (though potentially lower) nDCG scores.

**Acceptance Scenarios**:

1. **Given** the pipeline is configured with a 1GB RAM limit for the FAISS index, **When** the indexing step begins, **Then** the process enforces the memory cap by subsampling the dataset or using a quantized index type, preventing the process from exceeding 1.1GB RAM.
2. **Given** the pipeline is configured to use a 2-layer transformer (approx. 150M params) for generation, **When** the generation step executes, **Then** the model loads successfully on CPU without requiring CUDA or GPU memory.
3. **Given** the resource-constrained run completes, **When** the results are compared to the standard run, **Then** the system outputs a "degradation report" quantifying the drop in nDCG@10 and Precision@10 as absolute percentage points.

---

### Edge Cases

- **What happens when** a code snippet exceeds the 256-token truncation limit during pre-processing?
  - *System Behavior*: The system truncates the snippet and logs a warning; it does not crash. The semantic descriptors (API density, etc.) are recalculated based on the truncated content to ensure consistency.
- **How does system handle** a query that yields zero matches in the keyword (BM25) baseline?
  - *System Behavior*: The system assigns a Precision@k of 0.0 and nDCG@k of 0.0 for that query in the baseline, ensuring the performance delta calculation remains valid (RAG score - 0).
- **What happens when** the semantic descriptor calculation (e.g., naming consistency via embeddings) fails for a specific language variant?
  - *System Behavior*: The system skips the specific descriptor for that snippet, marks it as `NaN` (represented as the string "NaN" in CSV output), and excludes that specific data point from the correlation analysis while retaining the snippet for the retrieval performance metrics.
- **What happens when** the RAG prompt context window is exceeded?
  - *System Behavior*: The system truncates the concatenated list of retrieved snippets. A per-snippet token limit applies; the system concatenates up to the top 3 retrieved snippets. If the total token count of multiple snippets exceeds a defined maximum window, the system truncates the last snippet to fit the token window.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess the CodeSearchNet Python and Java subsets, stripping non-ASCII characters and truncating files to ≤ 256 tokens, to serve as the ground truth dataset (See US-1).
- **FR-002**: System MUST compute three specific semantic descriptors for every code snippet: API density (ratio of API calls to total tokens), Documentation density (ratio of comment tokens), and Naming-consistency score (average pairwise cosine similarity of identifier embeddings within the snippet using `CodeBERT-base`), to enable correlation analysis (See US-2).
- **FR-003**: System MUST implement three distinct retrieval pipelines: () BM keyword search, () Dual-encoder neural retrieval, and (3) RAG using `sentence-transformers/all-MiniLM-L6-v2` for indexing and `Salesforce/codegen-350M-mono` for generation. The RAG prompt MUST use a fixed template (e.g., "Question: {query}\nContext: {snippet}\nAnswer:") with temperature set to 0.0 and select the top 3 retrieved snippets, concatenating them within the 2048-token limit, to allow comparative evaluation (See US-1).
- **FR-004**: System MUST calculate evaluation metrics (Precision@10, Recall@10, nDCG@10) for every query against the CodeSearchNet ground truth labels for all three pipelines, to quantify performance (See US-1).
- **FR-005**: System MUST perform statistical significance testing on the performance deltas (RAG vs. Baseline). For correlation analysis between descriptors and deltas, the system MUST use Spearman's rho (ρ) with a significance threshold of p < 0.05. For paired mean differences, the system MUST use a paired t-test or Wilcoxon signed-rank test if normality is violated (See US-2).
- **FR-006**: System MUST support a "resource-constrained" mode that limits FAISS index memory to ≤ 1.05GB (measured as peak process RSS via `psutil`) and restricts the generation model to a 2-layer transformer, to simulate CI/CD environments (See US-3).
- **FR-007**: System MUST output all results in CSV format with columns for Query ID, Method, Metric Name, Metric Value, and Semantic Descriptors. Missing descriptor values MUST be represented as the string "NaN" (See US-1).
- **FR-008**: System MUST ensure the Naming-consistency score uses `CodeBERT-base` embeddings while the RAG retriever uses `all-MiniLM-L6-v2` to prevent circular validation where the predictor and target rely on identical semantic representations (See US-2).
- **FR-009**: System MUST implement a control experiment where API and documentation tokens are masked in the code snippets to verify that observed correlations are not mere artifacts of the retrieval algorithm's token weighting (See US-2).
- **FR-010**: System MUST perform a manual spot-check validation of a sample of the CodeSearchNet ground truth labels to estimate label noise, and report this noise estimate (See Assumptions).

### Key Entities

- **CodeSnippet**: Represents a single unit of code from the dataset, containing the source text, truncated version, and computed semantic descriptors (API density, doc density, naming score).
- **QueryResult**: Represents the output of a retrieval attempt for a specific query, containing the ranked list of snippets, the ground truth relevance labels, and the calculated metrics (nDCG, Precision).
- **PerformanceDelta**: A derived entity representing the difference in metric scores between the RAG method and a specific baseline for a given query, used for correlation analysis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The performance delta (nDCG@10 of RAG minus nDCG@10 of Baseline) is measured against the CodeSearchNet ground truth relevance labels to determine if RAG provides a statistically significant lift (See US-1).
- **SC-002**: The Spearman correlation coefficient (ρ) between each semantic descriptor (API density, doc density, naming consistency) and the performance delta is measured against the computed performance deltas to identify predictive code properties (See US-2).
- **SC-003**: The degradation in nDCG@10 under resource-constrained settings (≤1GB RAM, 2-layer model) is measured against the standard resource run to quantify the cost of lightweight deployment (See US-3).
- **SC-004**: The system's throughput (queries processed per hour) is measured against a target of ≥ 33 queries/hour to ensure the entire experiment (200 queries, 3 methods, multiple runs) completes within the 6-hour CI/CD job limit (See US-1).
- **SC-005**: The statistical significance of the performance difference is measured against a p-value threshold of 0.05 using Spearman's rho or Wilcoxon signed-rank tests to confirm the validity of the findings (See US-2).
- **SC-006**: The estimated label noise (percentage of mislabeled ground truth) is measured against the manual spot-check sample to validate the reliability of the nDCG metric (See Assumptions).

## Assumptions

- The `CodeSearchNet` dataset hosted on HuggingFace contains the necessary ground-truth relevance labels for the Python and Java subsets required to calculate nDCG and Precision@10.
- The `Salesforce/codegen-350M-mono` model is small enough to run inference on a CPU-only environment with 7GB RAM without requiring quantization libraries that mandate CUDA (e.g., bitsandbytes).
- The `sentence-transformers/all-MiniLM-L6-v2` model provides sufficient embedding quality for code retrieval to serve as a valid baseline for the RAG comparison.
- The CodeSearchNet test split contains at least 200 queries to ensure adequate statistical power for the Spearman correlation and Wilcoxon tests.
- The FAISS library, when configured with `IndexFlatIP` and standard float32 precision, will fit the vector index for the CodeSearchNet subset within the 7GB RAM limit of the runner.
- The "naming-consistency score" calculation using `CodeBERT-base` embeddings is computationally feasible on CPU within the 6-hour time limit for the full dataset.
- The `rank_bm25` implementation is compatible with the pre-processed, truncated code snippets without requiring special tokenization adjustments.
- The manual spot-check of [deferred] of labels will reveal a noise rate of ≤ 5%, validating the use of the dataset for high-level trend analysis.