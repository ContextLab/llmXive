# Feature Specification: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Feature Branch**: `001-llmxive-crosslingual`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Does the 'edge spectrum' subspace identified by EmbedFilter encode a universal, language-agnostic 'common sense' prior invariant across linguistic typologies, or does its composition shift to reflect language-specific syntactic noise?"

## User Scenarios & Testing

### User Story 1 - Extract and Compare Edge Spectrum Subspaces (Priority: P1)

The researcher needs to compute the "edge spectrum" subspace (top-$k$ singular vectors) of the unembedding matrix ($W_U$) for three distinct models (Llama, Mistral, BLOOM) and calculate the cosine similarity between the subspaces of English models versus the multilingual model to quantify the "rotation" or shift caused by linguistic typology.

**Why this priority**: This is the core experimental step. Without extracting the subspaces and measuring their geometric alignment, the hypothesis regarding universality vs. language-specificity cannot be tested. It is the foundational data generation step for the entire study.

**Independent Test**: The system can be tested by running the SVD extraction on the three models and verifying that a non-zero, computable cosine similarity matrix is produced between the English-English, English-BLOOM, and BLOOM-BLOOM subspace pairs, confirming the geometric comparison pipeline works.

**Acceptance Scenarios**:

1. **Given** the weights for Llama-3, Mistral, and BLOOM are loaded into memory, **When** the system performs SVD on each $W_U$ and extracts the top-100 singular vectors, **Then** the system outputs a JSON report containing the cosine similarity scores between the subspace bases of all model pairs.
2. **Given** the models are loaded, **When** the system attempts to extract the subspace for a model with missing or corrupted weight files, **Then** the system logs a specific error for that model and proceeds to process the remaining valid models without crashing.

---

### User Story 2 - Quantify Cross-Lingual Token Shift and External Validation (Priority: P2)

The researcher needs to identify the specific tokens with the highest logit weights within the extracted edge spectrum subspace for each language and compare their semantic categories (e.g., English function words vs. language-specific particles) to determine if the bias is universal or typologically specific. The methodology explicitly computes the 'mean embedding' (centroid) of the vocabulary weighted by frequency via matrix multiplication $W_E \\times f$ (where $f$ is the frequency distribution); the hypothesis is that the *shift* in this centroid between languages reflects typological differences rather than a novel 'common sense prior'. Additionally, the researcher must validate the shift by correlating the subspace orientation changes with external typological features (WALS) and, crucially, with performance degradation on Multilingual SentEval benchmarks to ensure the validation target is independent of the training frequency data.

**Why this priority**: While the geometric similarity (US-1) indicates *if* a shift exists, this story determines *what* the shift is and validates it against external linguistic theory and performance metrics. It validates the hypothesis that the "content" of the bias changes even if the structural role (anisotropy) remains constant.

**Independent Test**: The system can be tested by running the token attribution step on the BLOOM model's edge spectrum and verifying that the system outputs a JSON list of specific token IDs and their corresponding logit weights, confirming the lists are non-empty and distinct from the English model's list. The system must also output a correlation coefficient between the shift vector and WALS feature differences, and a correlation with SentEval performance drop.

**Acceptance Scenarios**:

1. **Given** the Common Crawl subset for a target language (e.g., French) is loaded, **When** the system counts token occurrences and normalizes by total tokens to generate a frequency distribution, **Then** the system outputs a vector of size $|V|$ representing the frequency distribution.
2. **Given** the frequency distribution and the edge spectrum subspace, **When** the system projects the frequency distribution onto the embedding matrix $W_E$ (computing $W_E \\times f$) to compute the mean embedding, **Then** the system outputs the mean embedding vector.
3. **Given** the mean embeddings for English and non-English models, **When** the system calculates the difference vector (shift) and compares it to the difference in WALS feature vectors, **Then** the system outputs a correlation coefficient $r$.
4. **Given** the ranked token lists for English and non-English models, **When** the system applies the vocabulary mapping layer to align tokens and calculates the overlap ratio of the top-10 tokens, **Then** the system reports an overlap percentage compared against a baseline generated from [deferred] randomly generated orthogonal bases (geometric baseline).

---

### User Story 3 - Validate Statistical Significance of Shift (Priority: P3)

The researcher needs to perform a permutation test to determine if the observed cross-lingual similarity in the edge spectrum is statistically significantly lower than the similarity expected from within-language variations, rejecting the null hypothesis that the shift is due to random noise or shared training dynamics. The null distribution is generated by comparing the observed similarity against similarities between the observed subspace and a set of within-language similarity samples (shuffled language pairs or same-language model pairs).

**Why this priority**: This provides the scientific rigor required to claim the observed shift is a real phenomenon rather than an artifact of the specific model initialization or random variation. It is the final validation step before drawing conclusions.

**Independent Test**: The system can be tested by running the permutation test with a fixed random seed and verifying that a p-value is generated, and that the test completes within the CPU time limit without requiring GPU acceleration.

**Acceptance Scenarios**:

1. **Given** the observed cosine similarity between English and BLOOM subspaces, **When** the system generates N random orthogonal bases (where N is determined by convergence criteria, minimum 1,000) to establish a geometric baseline, AND generates within-language similarity samples to establish a null distribution, **Then** the system outputs a p-value indicating the probability of observing the current similarity under the null hypothesis of within-language variation.
2. **Given** the p-value is computed, **When** the p-value is less than 0.05, **Then** the system outputs both the exact p-value and a flag "Statistically Significant Shift" in the final report.

---

### Edge Cases

- What happens when the SVD computation fails due to numerical instability in a specific model's $W_U$ matrix (e.g., extremely small singular values)?
- How does the system handle models where the vocabulary sizes differ significantly, making direct token comparison impossible without a mapping layer?
- What if the Common Crawl subset for a target language (e.g., French) is too small to generate a stable frequency distribution for the "average token" projection?

## Requirements

### Functional Requirements

- **FR-001**: System MUST perform Singular Value Decomposition (SVD) on the unembedding matrix ($W_U$) of loaded models to extract the matrix of the top-$k$ singular vectors constituting the "edge spectrum" subspace. (See US-1)
- **FR-002**: System MUST compute the cosine similarity between the subspace bases of different models to quantify the geometric rotation of the edge spectrum across linguistic typologies. (See US-1)
- **FR-003**: System MUST identify and rank the tokens with the highest logit weights within the extracted edge spectrum subspace for each language to attribute semantic content. (See US-2)
- **FR-004**: System MUST perform a permutation test with a minimum of 1,000 iterations using a within-language similarity null distribution (generated by shuffling language pairs or using same-language model pairs) to assess the statistical significance of the observed cross-lingual similarity differences. The system MUST output the p-value with at least 4 decimal precision. (See US-3)
- **FR-005**: System MUST project external frequency distributions (from RedPajama/Common Crawl) onto the embedding matrix ($W_E$) to compute the "mean embedding" vector for each language via matrix multiplication $W_E \\times f$. (See US-2)
- **FR-006**: System MUST acquire and validate the Common Crawl subsets (French/Chinese) and RedPajama lists as raw datasets, ensuring they meet the minimum size requirement of ≥ 1,000,000 tokens OR the maximum available subset for stable frequency distribution estimation. (See US-2)
- **FR-007**: System MUST acquire and process WALS (World Atlas of Language Structures) features for the target languages (English, French, Chinese) and map them to the model's language identifiers. System MUST also acquire Multilingual SentEval performance metrics (specifically STS task accuracy) to serve as an independent validation target for the shift. (See US-2)
- **FR-008**: System MUST implement a vocabulary mapping layer using a shared subword vocabulary or translation map to align tokens across different model architectures before calculating the overlap ratio. (See US-2)

### Key Entities

- **Edge Spectrum Matrix**: A matrix containing the top-$k$ singular vectors of the unembedding matrix $W_U$, representing the direction of anisotropy.
- **Mean Embedding Vector**: A computed embedding vector $\hat{\vh}$ derived by projecting the token frequency distribution onto the embedding matrix $W_E$ (via $W_E \\times f$), representing the centroid of the vocabulary.
- **Subspace Similarity Metric**: A scalar value (cosine similarity) representing the alignment between two edge spectrum matrices.
- **Permutation Null Distribution**: A set of similarity scores generated by comparing the observed subspace against within-language similarity samples to establish a baseline for statistical testing.
- **WALS Feature Vector**: A binary vector representing the typological properties of a language (e.g., word order, noun class system).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of the anisotropy bias (cosine similarity of subspaces) is measured against the within-language baseline (self-similarity) to determine the magnitude of deviation from the hypothesized null, including a confidence interval. (See FR-002)
- **SC-002**: The composition shift of dominant tokens is measured against the overlap ratio of the top tokens between English and non-English models compared to a random orthogonal basis baseline (average overlap with random bases); the magnitude of the difference is the metric. (See FR-003, FR-008)
- **SC-003**: The statistical significance of the shift is measured against the p-value derived from the permutation test null distribution (within-language similarity). (See FR-004)
- **SC-004**: The validity of the validation metric is measured against the correlation coefficient between the subspace shift vector and the difference in Multilingual SentEval STS task accuracy (performance degradation) between language pairs. (See FR-007)
- **SC-005**: The computational feasibility is measured against the constraint of completing the full SVD and permutation pipeline on a GitHub Actions ubuntu-latest runner (A multi‑core (several vCPU) configuration, 16 GB RAM) within 6 hours. (See FR-001)

## Assumptions

- The Hugging Face `transformers` library and `numpy` are available and sufficient to load the model weights and perform SVD on the unembedding matrices without GPU acceleration.
- The "edge spectrum" is defined as the top-$k$ singular vectors where $k$ is a fixed small integer, relative to the full matrix dimension, ensuring the subspace extraction fits within available RAM constraints.
- The RedPajama and Common Crawl frequency lists are raw datasets to be downloaded and pre-processed; the system assumes access to the internet or a local mirror to retrieve these datasets during the Data Acquisition phase.
- The permutation test is computationally tractable on a standard multi-core CPU for N iterations (minimum 1,000); if the runtime exceeds a predefined threshold, the iteration count will be reduced to a lower, predefined limit, and this limitation will be noted in the final report.
- The "mean embedding" projection method (linear algebra on CPU, $W_E \\times f$) is a valid approximation for the "common sense" prior as proposed in the original EmbedFilter paper, with the understanding that it computes the vocabulary centroid.
- The models (Llama-3, Mistral, BLOOM) are available in a format compatible with the `load_in_8bit` or `device_map="cpu"` parameters if necessary, but standard float32 loading is preferred to avoid CUDA dependencies.
- The WALS database is accessible via a public API or downloadable CSV, and the mapping from model language codes to WALS language identifiers is deterministic.
- Multilingual SentEval STS benchmarks are available for the target languages to provide an independent performance metric.