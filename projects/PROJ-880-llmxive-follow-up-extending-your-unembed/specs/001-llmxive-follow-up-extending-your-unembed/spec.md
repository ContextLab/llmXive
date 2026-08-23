# Feature Specification: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Feature Branch**: `001-llmxive-crosslingual`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Does the 'edge spectrum' subspace identified by EmbedFilter encode a universal, language-agnostic 'common sense' prior invariant across linguistic typologies, or does its composition shift to reflect language-specific syntactic noise?"

## User Scenarios & Testing

### User Story 1 - Extract and Compare Edge Spectrum Subspaces (Priority: P1) (US-1)

The researcher needs to compute the “edge spectrum” subspace (the leading singular vectors) of the unembedding matrix ($W_U$) for three distinct models (Llama‑3, Mistral, BLOOM). and calculate the cosine similarity between the subspaces of English models versus the multilingual model to quantify the "rotation" or shift caused by linguistic typology.

**Why this priority**: This is the core experimental step. Without extracting the subspaces and measuring their geometric alignment, the hypothesis regarding universality vs. language‑specificity cannot be tested. It is the foundational data generation step for the entire study.

**Independent Test**: The system can be tested by running the SVD extraction on the three models and verifying that a non‑zero, computable cosine similarity matrix is produced between the English‑English, English‑BLOOM, and BLOOM‑BLOOM subspace pairs, confirming the geometric comparison pipeline works.

**Acceptance Scenarios**:

1. **Given** the weights for Llama‑3, Mistral, and BLOOM are loaded into memory, **When** the system performs SVD on each $W_U$ and extracts the top‑100 singular vectors, **Then** the system outputs a JSON report containing the cosine similarity scores between the subspace bases of all model pairs, together with appropriate bootstrap confidence intervals.
2. **Given** the models are loaded, **When** the system attempts to extract the subspace for a model with missing or corrupted weight files, **Then** the system logs a specific error for that model and proceeds to process the remaining valid models without crashing.

---

### User Story 2 - Quantify Cross‑Lingual Token Shift and External Validation (Priority: P2) (US-2)

The researcher needs to identify the specific tokens with the highest logit weights within the extracted edge spectrum subspace for each language and compare their semantic categories (e.g., English function words vs. language‑specific particles) to determine if the bias is universal or typologically specific. The methodology explicitly computes the 'mean embedding' (centroid) of the vocabulary weighted by frequency via matrix multiplication $W_U^{+} \times f$ (where $W_U^{+}$ is the Moore‑Penrose pseudo‑inverse of the unembedding matrix and $f$ is the frequency distribution); the hypothesis is that the *shift* in this centroid between languages reflects typological differences rather than a novel 'common sense prior'. Additionally, the researcher must validate the shift by correlating the subspace orientation changes with external typological features (WALS) and, crucially, with performance degradation on Multilingual SentEval benchmarks to ensure the validation target is independent of the training frequency data.

**Why this priority**: While the geometric similarity (US‑1) indicates *if* a shift exists, this story determines *what* the shift is and validates it against external linguistic theory and performance metrics. It validates the hypothesis that the "content" of the bias changes even if the structural role (anisotropy) remains constant.

**Independent Test**: The system can be tested by running the token attribution step on the BLOOM model's edge spectrum and verifying that the system outputs a JSON list of specific token IDs and their corresponding logit weights, confirming the lists are non‑empty and distinct from the English model's list. The system must also output a Pearson correlation coefficient between the shift vector and WALS feature differences, and a correlation with SentEval performance drop, each with 95 % confidence intervals.

**Acceptance Scenarios**:

1. **Given** the Common Crawl language‑filtered subset for a target language (e.g., French) is loaded, **When** the system counts token occurrences and normalizes by total tokens to generate a frequency distribution, **Then** the system outputs a vector of size $|V|$ representing the frequency distribution.
2. **Given** the frequency distribution and the edge spectrum subspace, **When** the system projects the frequency distribution onto the pseudo‑inverse of the unembedding matrix ($W_U^{+} \times f$) to compute the mean embedding, **Then** the system outputs the mean embedding vector.
3. **Given** the mean embeddings for English and non‑English models, **When** the system calculates the difference vector (shift) and compares it to the difference in WALS feature vectors, **Then** the system outputs a Pearson correlation coefficient $r$ and its 95 % confidence interval.
4. **Given** the ranked token lists for English and non‑English models, **When** the system applies the vocabulary mapping layer to align tokens and calculates the overlap ratio of the top‑N tokens, **Then** the system reports an overlap percentage compared against a baseline generated from 10 000 randomly generated orthogonal bases (geometric baseline).

---

### User Story 3 - Validate Statistical Significance of Shift (Priority: P3) (US-3)

The researcher needs to perform a permutation test to determine if the observed cross‑lingual similarity in the edge spectrum is statistically significantly lower than the similarity expected from within‑language variations, rejecting the null hypothesis that the shift is due to random noise or shared training dynamics. The null distribution is generated by comparing the observed similarity against similarities between the observed subspace and a set of within‑language similarity samples (shuffled language pairs or same‑language model pairs) **and** against an across‑model null distribution to capture model‑specific variability.

**Why this priority**: This provides the scientific rigor required to claim the observed shift is a real phenomenon rather than an artifact of the specific model initialization or random variation. It is the final validation step before drawing conclusions.

**Independent Test**: The system can be tested by running the permutation test with a fixed random seed and verifying that a p‑value is generated, and that the test completes within the CPU time limit without requiring GPU acceleration.

**Acceptance Scenarios**:

1. **Given** the observed cosine similarity between English and BLOOM subspaces, **When** the system generates at least 10 000 random orthogonal bases (minimum iteration count) to establish a geometric baseline, **AND** generates within‑language and across‑model similarity samples to establish a combined null distribution, **Then** the system outputs a p‑value (≥ 4 decimal places) indicating the probability of observing the current similarity under the null hypothesis.
2. **Given** the p‑value is computed, **When** the p‑value is below the conventional significance threshold., **Then** the system outputs both the exact p‑value and a flag "Statistically Significant Shift" in the final report.

---

### Edge Cases

- What happens when the SVD computation fails due to numerical instability in a specific model's $W_U$ matrix (e.g., extremely small singular values)?
- How does the system handle models where the vocabulary sizes differ significantly, making direct token comparison impossible without a mapping layer?
- What if the Common Crawl subset for a target language (e.g., French) is too small to generate a stable frequency distribution for the "average token" projection?

## Requirements

### Functional Requirements

- **FR-001**: System MUST perform Singular Value Decomposition (SVD) on the unembedding matrix ($W_U$) of loaded models to extract the matrix of the leading singular vectors that constitute the “edge spectrum” subspace. (See US‑1)
- **FR-002**: System MUST compute the cosine similarity between the subspace bases of different models to quantify the geometric rotation of the edge spectrum across linguistic typologies, and must report a bootstrap confidence interval at a conventional confidence level for each similarity measurement. (See US‑1)
- **FR-003**: System MUST identify and rank the tokens with the highest logit weights within the extracted edge spectrum subspace for each language to attribute semantic content. (See US‑2)
- **FR-004**: System MUST perform a permutation test with **≥ 10 000** iterations using a combined null distribution (within‑language similarity samples, across‑model similarity samples, and model‑specific variability) to assess the statistical significance of the observed cross‑lingual similarity differences. The system MUST output the p‑value with at least 4 decimal precision. (See US‑3) **The iteration count may not be reduced; if runtime exceeds the 5‑hour limit the system must log a warning and abort, requiring the user to allocate additional resources.**
- **FR-005**: System MUST compute the mean embedding vector for each language by multiplying the Moore‑Penrose pseudo‑inverse of the unembedding matrix ($W_U^{+}$) with the language‑specific token frequency vector $f$ (i.e., $W_U^{+} \times f$). (See US‑2)
- **FR-006**: System MUST acquire and validate **language‑filtered Common Crawl** subsets for **all target languages** (English, French, Chinese, Arabic, Swahili, German, Spanish, Hindi, Japanese, Portuguese). Each subset must contain **≥ 1,000,000 tokens**. Verified URLs and retrieval timestamps are recorded (e.g., (retrieved 2026‑08‑20 10:12 UTC)). (See US‑2)
- **FR-007**: System MUST acquire and process **WALS** features and **Multilingual SentEval** STS performance metrics for the target languages. All dataset URLs are verified against official sources and timestamps recorded (e.g., (retrieved 2026‑08‑20 11:05 UTC); https://github.com/facebookresearch/SentEval (retrieved 2026‑08‑20 11:12 UTC)). (See US‑2)
- **FR-008**: System MUST implement a vocabulary mapping layer using a **shared subword vocabulary of a size on the order of ten thousand.** (aligned with the FacebookResearch alignment vocab = 11200, see Q136293754) to align tokens across different model architectures. The mapping procedure must:
  1. Convert each model’s token IDs to the shared subword tokens.
  2. Transform raw token counts into probability distributions by dividing by the total token count.
  3. Apply length‑normalization to account for differing tokenization granularity.
  4. Compute overlap ratios on these normalized distributions rather than raw counts.
  This rigorous normalization eliminates confounding from vocabulary‑size differences. (See US‑2)
- **FR-009**: System MUST ensure that **all** frequency distributions are derived from the **same corpus source** (Common Crawl) for every language to guarantee comparability. (See US‑2)
- **FR-010**: System MUST include control analyses that account for model‑level confounds (architecture, training data, vocabulary size) by computing subspace similarity on matched‑architecture model pairs and reporting **adjusted similarity metrics** that isolate linguistic effects. (See US‑1)
- **FR-011**: System MUST store all generated artifacts under the `data/derived/` directory in accordance with the data model (e.g., `data/derived/subspace_similarity.json`). (See US‑1)
- **FR-012**: System MUST verify that all external dataset URLs (Common Crawl language‑filtered splits, WALS CSV, Multilingual SentEval repository) are confirmed against official sources prior to download, satisfying Constitution Principle II. Verification timestamps and source citations are recorded in the final report. (See US‑2)
- **FR-013**: System MUST exercise each defined contract schema (`edge_spectrum.schema.yaml`, `feasibility_report.schema.yaml`, `frequency_list.schema.yaml`, `similarity_matrix.schema.yaml`, `similarity_metric.schema.yaml`, `similarity_report.schema.yaml`) in the appropriate pipeline phase. (See US‑1)
- **FR-014**: System MUST produce an `edge_spectrum.json` file that conforms to `edge_spectrum.schema.yaml`, containing fields `model_pairs` (list of model‑pair identifiers) and `similarity_matrix` (2‑D array of cosine similarities). (See US‑1)
- **FR-015**: System MUST generate bootstrap confidence intervals (95 % CI, ≥ 1,000 replicates) for all reported cosine‑similarity measurements and include them in the `similarity_report.json`. (See SC‑006)
- **FR-016**: System MUST conduct correlation analyses on **at least ten** languages (English, French, Chinese, Arabic, Swahili, German, Spanish, Hindi, Japanese, Portuguese) to provide sufficient statistical power. Results must include Pearson $r$, two‑tailed $p$‑value, and 95 % confidence interval. (See SC‑007)
- **FR-017**: System MUST annotate every external URL with a verification timestamp and source citation in the final report to satisfy constitutional verification requirements. (See FR‑012)
- **FR-018**: System MUST enforce that **all** artifact file paths referenced in the plan and requirements use the `data/derived/` prefix, eliminating any `results/` path inconsistencies. (See FR‑011)
- **FR-019**: System MUST verify external URLs (Common Crawl, WALS, SentEval) against official sources and record verification timestamps, complying with Constitution Principle II. (See FR‑012)
- **FR-020**: System MUST ensure that no external dataset is used without prior verification; any unverified source must be rejected and an alternative verified source sourced. (See FR‑019)
- **FR-021**: System MUST exercise **all** listed JSON‑schema contracts (`edge_spectrum`, `feasibility_report`, `frequency_list`, `similarity_matrix`, `similarity_metric`, `similarity_report`) and validate generated artifacts against them. (See FR‑013)
- **FR-022**: System MUST generate `frequency_list.json` conforming to `frequency_list.schema.yaml` for each language. (See US‑2)
- **FR-023**: System MUST generate `similarity_matrix.json` conforming to `similarity_matrix.schema.yaml`. (See FR‑014)
- **FR-024**: System MUST generate `similarity_metric.json` conforming to `similarity_metric.schema.yaml`, reporting similarity scores and confidence intervals. (See FR‑015)
- **FR-025**: System MUST generate `feasibility_report.json` conforming to `feasibility_report.schema.yaml`, documenting computational resource usage and runtime. (See SC‑005)
- **FR-028**: System MUST perform paired‑architecture control analyses (e.g., Llama‑3 vs. a second Llama‑3 model, Mistral vs. a second Mistral model) and report **adjusted similarity metrics** that isolate the effect of linguistic typology from architecture‑specific variance. (See US‑1)

### Key Entities

- **Edge Spectrum Matrix**: A matrix containing the top‑100 singular vectors of the unembedding matrix $W_U$, representing the direction of anisotropy.
- **Mean Embedding Vector**: A computed embedding vector $\hat{\vh}$ derived by projecting the token frequency distribution onto the pseudo‑inverse of the unembedding matrix ($W_U^{+} \times f$), representing the centroid of the vocabulary.
- **Subspace Similarity Metric**: A scalar value (cosine similarity) representing the alignment between two edge spectrum matrices.
- **Permutation Null Distribution**: A set of similarity scores generated by comparing the observed subspace against within‑language, across‑model, and model‑specific variability samples to establish a baseline for statistical testing.
- **WALS Feature Vector**: A binary vector representing the typological properties of a language (e.g., word order, noun class system).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of the anisotropy bias (cosine similarity of subspaces) is measured against the within‑language baseline (self‑similarity) and reported with a 95 % bootstrap confidence interval. (See FR‑002, FR‑010, FR‑015)
- **SC-002**: The composition shift of dominant tokens is measured against the overlap ratio of the top tokens between English and non‑English models compared to a random orthogonal basis baseline (average overlap with random bases); the magnitude of the difference is the metric. (See FR‑003, FR‑008)
- **SC-003**: The statistical significance of the shift is measured against the p‑value derived from the permutation test combined null distribution (within‑language + across‑model + model‑specific). (See FR‑004)
- **SC-004**: The validity of the validation metric is measured against the Pearson correlation coefficient (with 95 % confidence interval) between the subspace shift vector and the difference in Multilingual SentEval STS task accuracy between language pairs. (See FR‑007)
- **SC-005**: The computational feasibility is measured against the constraint of completing the full SVD and permutation pipeline on a GitHub Actions ubuntu‑latest runner (multi‑core, 16 GB RAM) within 6 hours. (See FR‑001)
- **SC-006**: All cosine‑similarity measurements are reported with 95 % confidence intervals obtained via bootstrap sampling (≥ 1,000 bootstrap replicates). (See FR‑015)
- **SC-007**: Correlation analyses are performed on **at least ten languages**; results include Pearson $r$, two‑tailed $p$‑value, and 95 % confidence interval, ensuring sufficient statistical power. (See FR‑016)
- **SC-008**: All external dataset URLs are listed with verification timestamps and source citations in the final report, satisfying constitutional verification requirements. (See FR‑017)

## Implementation Plan

| Phase | Description | Primary Artifacts (stored under `data/derived/`) |
|-------|-------------|---------------------------------------------------|
| 1 | Load model weights, extract $W_U$, perform SVD to obtain top‑100 edge spectrum vectors. | `edge_spectrum.json` (conforms to `edge_spectrum.schema.yaml`) |
| 2 | Acquire language‑filtered Common Crawl subsets, compute token frequency distributions, generate `frequency_list.json` for each language. | `frequency_list_{lang}.json` |
| 3 | Apply vocabulary mapping layer, compute token attribution and overlap ratios, store `token_attribution_{model}.json`. | `token_attribution_{model}.json` |
| 4 | Compute mean embeddings via $W_U^{+} \times f$, correlate shifts with WALS features and SentEval STS drops, produce `validation.json`. | `validation.json` |
| 5 | Run permutation test with ≥10 000 iterations, generate `permutation_test.json` containing p‑value and significance flag. | `permutation_test.json` |
| 6 | Assemble all results, compute bootstrap CIs, produce `similarity_report.json` and `feasibility_report.json`. | `similarity_report.json`, `feasibility_report.json` |

All artifacts are validated against their respective JSON‑schema contracts (FR‑021) and timestamps/URL verifications are recorded (FR‑019, FR‑020).

## Assumptions

- The Hugging Face `transformers` library and `numpy` are available and sufficient to load the model weights and perform SVD on the unembedding matrices without GPU acceleration.
- The "edge spectrum" is defined as the top‑100 singular vectors where $k = 100$, relative to the full matrix dimension, ensuring the subspace extraction fits within available RAM constraints.
- The language‑filtered Common Crawl subsets for all target languages are publicly accessible via verified URLs and can be downloaded during the Data Acquisition phase.
- The permutation test is computationally tractable on a standard multi‑core CPU for **≥ 10 000** iterations; if the runtime exceeds the 5‑hour threshold the system must log a warning and abort, requiring the user to allocate additional resources.
- The "mean embedding" projection method using the pseudo‑inverse of $W_U$ is a valid approximation for the "common sense" prior as proposed in the original EmbedFilter paper, with the understanding that it computes the vocabulary centroid in the unembedding space.
- The models (Llama‑3, Mistral, BLOOM) are available in a format compatible with the `load_in_8bit` or `device_map="cpu"` parameters if necessary, but standard float32 loading is preferred to avoid CUDA dependencies.
- The WALS database is accessible via a public API or downloadable CSV, and the mapping from model language codes to WALS language identifiers is deterministic.
- Multilingual SentEval STS benchmarks are available for the target languages to provide an independent performance metric.
- All contract schemas referenced are defined in the `contracts/` directory and are syntactically valid JSON Schema files.
