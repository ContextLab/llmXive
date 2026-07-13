# Feature Specification: llmXive Follow-up: Extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Feature Branch**: `001-llmxive-crosslingual-edge-spectrum`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings'"

## User Scenarios & Testing

### User Story 1 - Cross-Lingual Edge Spectrum Extraction (Priority: P1)

**User Journey**: As a researcher, I want to compute the top-$k$ singular vectors (edge spectrum) for the unembedding matrices of three distinct language models (Llama-3-8B, BLOOM-7B, Qwen-1.5-7B) without materializing the full matrix in RAM, so that I can establish the geometric baseline for each language's representation space within strict memory constraints.

**Why this priority**: This is the foundational data acquisition and processing step. Without successfully extracting the edge spectrum for each model, no comparative analysis can occur. It validates the pipeline's ability to handle different model architectures and tokenizers on CPU-only hardware while respecting memory limits.

**Independent Test**: Can be fully tested by running the extraction script on a single model (e.g., Llama-3-8B) and verifying that the resulting SVD output (singular values and vectors) matches the expected dimensions, that peak RAM usage remains ≤7 GB (verified via `/usr/bin/time`), and that the top-$k$ vectors capture ≥90% of the matrix variance, independent of the other languages.

**Acceptance Scenarios**:

1. **Given** the script has access to the Llama-3-8B model weights and tokenizer, **When** the script executes the TruncatedSVD on the unembedding matrix, **Then** it outputs a CSV of the top-50 singular values and vectors without running out of memory (peak RSS ≤7 GB as reported by `/usr/bin/time`).
2. **Given** the script has access to the BLOOM-7B model weights, **When** the script executes the TruncatedSVD, **Then** it successfully handles the multilingual vocabulary size and outputs the edge spectrum without crashing due to dtype mismatches.
3. **Given** a Qwen-1.5-7B model, **When** the script processes the matrix, **Then** it correctly identifies and logs the top-$k$ vectors corresponding to the "edge spectrum" as defined by the largest singular values.

---

### User Story 2 - Frequency-Weighted Average Token Projection (Priority: P2)

**User Journey**: As a researcher, I want to compute the "average token" embedding vector ($\hat{\vh}$) for each language by performing a frequency-weighted sum of the model's vocabulary embeddings, validate that the input and unembedding spaces are aligned, and project these vectors onto the edge spectrum to measure anisotropy and bias.

**Why this priority**: This step operationalizes the "bias" concept. It transforms raw frequency data into a geometric vector that can be mathematically compared against the singular vectors derived in User Story 1. It tests the integration of external corpus data with model weights and the critical alignment step required for valid comparisons.

**Independent Test**: Can be tested by running the projection logic on a synthetic dataset with known frequencies and verifying that the resulting $\hat{\vh}$ vector has a projection magnitude > 0.01 onto the top singular vector of the English edge spectrum, and that the Procrustes alignment between $E$ and $W_U$ yields a cosine similarity > 0.95 for the top singular vectors.

**Acceptance Scenarios**:

1. **Given** a frequency list for English tokens and the Llama-3-8B embeddings, **When** the script calculates the frequency-weighted sum and applies Procrustes alignment, **Then** the resulting $\hat{\vh}$ vector has a projection magnitude > 0.01 onto the top singular vector of the English edge spectrum.
2. **Given** a frequency list for Chinese tokens and the Qwen-1.5-7B embeddings, **When** the script calculates the sum and applies alignment, **Then** it correctly handles the tokenization differences (e.g., subword units) to produce a valid average vector.
3. **Given** the computed $\hat{\vh}$ vectors, **When** the system projects them onto the *own* model's edge spectrum (after alignment), **Then** it records the cosine similarity value for subsequent statistical comparison against a null distribution.

---

### User Story 3 - Cross-Lingual Similarity & Statistical Validation (Priority: P3)

**User Journey**: As a researcher, I want to calculate the cosine similarity between the "average token" vectors of different languages when projected onto cross-language edge spectra (after Procrustes alignment) and perform a permutation test using a spherical null baseline, so that I can statistically validate whether the edge spectrum encodes universal or language-specific priors.

**Why this priority**: This delivers the final research answer. It synthesizes the data from the previous two stories to answer the core research question. It tests the statistical rigor, the ability to handle null hypothesis generation on CPU, and the validity of cross-lingual comparisons.

**Independent Test**: Can be fully tested by running the permutation test on a small subset of data (e.g., N=100 iterations) and verifying that the p-value calculation logic correctly rejects the null hypothesis when a synthetic signal is injected, and that the stability check (sweep) confirms p-value convergence (Δp < 0.01).

**Acceptance Scenarios**:

1. **Given** the English and Chinese average vectors and their respective edge spectra (aligned via Procrustes), **When** the script projects the English vector onto the Chinese edge spectrum, **Then** it outputs a cosine similarity score distinct from the self-spectrum projection.
2. **Given** the observed similarity scores, **When** the script runs the permutation test (generating null vectors from a spherical distribution N times, where N is swept across 100, 1000, 10000), **Then** it outputs the calculated p-value.
3. **Given** the final results, **When** the script generates the report, **Then** it explicitly lists the top-10 tokens with the highest loadings in the top singular vectors for each language, categorized by semantic type (function word vs. content word).

---

### Edge Cases

- **What happens when** a model's vocabulary size exceeds the available RAM during SVD computation? The system MUST fallback to a randomized SVD approximation (e.g., `scikit-learn`'s `TruncatedSVD`) with a fixed random seed to ensure reproducibility, ensuring the relative error compared to an exact SVD on a subsample is ≤ 1e-3.
- **How does the system handle** tokenizers that map a single character to multiple tokens (common in Asian languages)? The frequency weighting MUST normalize for token count per character to avoid biasing the average vector toward languages with higher tokenization granularity.
- **What happens when** the frequency data for a specific language (e.g., French) is missing or incomplete? The system MUST raise a `DataMissingError` and halt execution rather than proceeding with a null or zero-filled frequency vector. The French analysis is explicitly mapped to the BLOOM-7B model, and Chinese analysis to Qwen-1.5-7B. If the language list is missing, the process MUST NOT continue.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST stream and compute the top-k singular vectors of the unembedding matrices for Llama-3-8B, BLOOM-7B (for French/English), and Qwen-1.5-7B (for Chinese) using CPU-optimized TruncatedSVD, ensuring total RAM usage remains ≤ 7 GB without materializing the full matrix. (See US-1)
- **FR-002**: The system MUST compute the top 50 singular vectors (k=50) of the unembedding matrix using TruncatedSVD exclusively (full SVD is prohibited), ensuring the cumulative variance explained is ≥ 90%. (See US-1)
- **FR-003**: The system MUST ingest external frequency lists (RedPajama/CC subsets), verify frequency vector convergence (KL-divergence < 0.01 against a larger sample), and compute a frequency-weighted average embedding vector ($\hat{\vh}$) for each language, handling tokenization mismatches between the corpus and the model. If model-specific frequencies are unavailable, the system MUST document the sampling bias as a limitation. (See US-2)
- **FR-004**: The system MUST apply Orthogonal Procrustes alignment to map the average token vectors and edge spectra into a shared basis before calculating cosine similarities, ensuring valid cross-lingual comparisons. (See US-3)
- **FR-005**: The system MUST execute a permutation test with a configurable number of iterations to generate a null distribution using random unit vectors (spherical baseline) and compute a p-value for the observed cross-lingual similarity shifts. The system MUST perform a sensitivity analysis by sweeping the iteration count (N=100, 1000, 10000) and verify convergence (p-value change < 0.01 between sweeps). The process MUST log the total duration of execution. (See US-3)
- **FR-006**: The system MUST identify and output the top tokens with the highest loadings in the top singular vectors, mapping them to semantic categories (function words, particles, content words) using the Universal Dependencies (UD) treebank resources; if a token is not found in the lexicon, it MUST be categorized as 'unknown' and excluded from the numerator and denominator of the semantic proportion calculation. (See US-3)
- **FR-007**: The system MUST log all intermediate data dimensions and variance explained ratios to ensure the SVD results are mathematically valid and not artifacts of numerical instability. (See US-1)
- **FR-008**: The system MUST log the actual number of permutation iterations executed and the hardware profile (CPU cores, RAM) used during the run. (See US-3)

### Key Entities

- **Edge Spectrum**: The subspace spanned by the top-$k$ singular vectors of the unembedding matrix, representing the dominant geometric bias.
- **Average Token Vector ($\hat{\vh}$)**: The frequency-weighted centroid of the vocabulary embeddings for a specific language, aligned to a shared basis.
- **Cross-Lingual Similarity Score**: A scalar value representing the cosine similarity between an average token vector and a foreign edge spectrum, computed after Procrustes alignment.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, thresholds, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variance explained by the top-50 singular vectors is measured against the total variance of the unembedding matrix to ensure the edge spectrum captures the dominant bias structure (See US-1).
- **SC-002**: The cosine similarity between the native average token vector and the native edge spectrum is measured against the similarity between the native vector and the cross-language edge spectrum to quantify language-specific bias (See US-3).
- **SC-003**: The p-value of the permutation test is measured against the significance threshold (α = 0.05) to determine if the observed cross-lingual shifts are statistically significant (See US-3).
- **SC-004**: The total runtime of the full pipeline (SVD, projection, permutation) is measured against the CI time limit of 60 minutes to ensure compute feasibility (See US-3).
- **SC-005**: The proportion of top-loading tokens identified as function words vs. content words is measured against the proportion of function/content words in the source frequency corpus (RedPajama/CC) to validate the semantic interpretation (See US-3).
- **SC-006**: The stability of the p-value is measured against a sensitivity analysis where the permutation count is varied across N=100, 1000, 10000, ensuring the standard deviation of p-values across sweeps is < 0.005. If SC-006 fails, the result is considered inconclusive regardless of SC-003 (See US-3).

## Assumptions

- **Assumption about data availability**: Publicly available frequency lists (RedPajama for English, Common Crawl subsets for French/Chinese) contain sufficient token frequency data to approximate the "average token" vector without significant sampling bias, or the sampling bias is documented as a limitation.
- **Assumption about model access**: The unembedding matrices for Llama-3-8B, BLOOM-7B, and Qwen-1.5-7B are accessible via Hugging Face Hub in a format compatible with `torch.load` or `safetensors` on CPU.
- **Assumption about methodological framing**: The analysis is strictly observational; any findings regarding "bias" or "anisotropy" will be framed as associational statistical properties of the matrix geometry, not causal claims about model behavior.
- **Assumption about compute constraints**: The use of `TruncatedSVD` or randomized SVD is sufficient to approximate the top singular vectors within the 7 GB RAM and standard CI runner limits, even for models with large vocabularies (e.g., BLOOM).
- **Assumption about threshold justification**: A cutoff of $k=50$ for the edge spectrum is selected based on the "elbow" method in variance explained plots, which is a standard community practice for identifying dominant subspaces in high-dimensional data; a sensitivity analysis will sweep $k$ over a range of small integer values to ensure results are robust to this choice.
- **Assumption about heuristic inspection**: A cosine similarity threshold is used as a heuristic for initial visual inspection of alignment, but the system does not enforce this as a pass/fail criteria; statistical significance is determined by the permutation test p-value.