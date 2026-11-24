# Feature Specification: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Feature Branch**: `001-llmxive-crosslingual`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Does the 'edge spectrum' subspace identified by EmbedFilter encode a universal, language-agnostic 'common sense' prior invariant across linguistic typologies, or does its composition shift to reflect language-specific syntactic noise?"

## User Scenarios & Testing

### User Story 1 - Extract and Compare Edge Spectrum Subspaces (Priority: P1) (US-1)

The researcher needs to compute the “edge spectrum” subspace (the leading singular vectors) of the unembedding matrix ($W_U$) for three distinct models (Llama‑3, Mistral, BLOOM) and calculate the cosine similarity between the subspaces of English models versus the multilingual model to quantify the "rotation" or shift caused by linguistic typology.

**Why this priority**: This is the core experimental step. Without extracting the subspaces and measuring their geometric alignment, the hypothesis regarding universality vs. language‑specificity cannot be tested. It is the foundational data generation step for the entire study.

**Independent Test**: The system can be tested by running the SVD extraction on the three models and verifying that a non‑zero, computable cosine similarity matrix is produced between the English‑English, English‑BLOOM, and BLOOM‑BLOOM subspace pairs, confirming the geometric comparison pipeline works.

**Acceptance Scenarios**:

1. **Given** the weights for Llama‑3, Mistral, and BLOOM are loaded into memory, **When** the system performs SVD on each $W_U$ and extracts the top‑100 singular vectors, **Then** the system outputs a JSON report containing the cosine similarity scores between the subspace bases of all model pairs, together with appropriate bootstrap confidence intervals. *(Backed by FR‑001, FR‑040)*
2. **Given** the models are loaded, **When** the system attempts to extract the subspace for a model with missing or corrupted weight files, **Then** the system logs a specific error for that model and proceeds to process the remaining valid models without crashing. *(Backed by FR‑030)*

### User Story 2 - Quantify Cross‑Lingual Token Shift and External Validation (Priority: P2) (US-2)

The researcher needs to identify the specific tokens with the highest logit weights within the extracted edge spectrum subspace for each language and compare their semantic categories (e.g., English function words vs. language‑specific particles) to determine if the bias is universal or typologically specific. The methodology explicitly computes the 'mean embedding' (centroid) of the vocabulary weighted by frequency via matrix multiplication $W_U^{+} \times f$ (where $W_U^{+}$ is the Moore‑Penrose pseudo‑inverse of the unembedding matrix and $f$ is the frequency distribution); the hypothesis is that the *shift* in this centroid between languages reflects typological differences rather than a novel 'common sense prior'. Additionally, the researcher must validate the shift by correlating the subspace orientation changes with external typological features (WALS) and, crucially, with performance degradation on the multilingual XTREME probing benchmark to ensure the validation target is independent of the training frequency data.

**Why this priority**: While the geometric similarity (US‑1) indicates *if* a shift exists, this story determines *what* the shift is and validates it against external linguistic theory and performance metrics. It validates the hypothesis that the "content" of the bias changes even if the structural role (anisotropy) remains constant.

**Independent Test**: The system can be tested by running the token attribution step on the BLOOM model's edge spectrum and verifying that the system outputs a JSON list of specific token IDs and their corresponding logit weights, confirming the lists are non‑empty and distinct from the English model's list. The system must also output a Pearson correlation coefficient between the shift vector and WALS feature differences, and a correlation with XTREME benchmark performance drop, each with 95 % confidence intervals.

**Acceptance Scenarios**:

1. **Given** the Common Crawl language‑filtered subset for a target language (e.g., French) is loaded, **When** the system counts token occurrences and normalizes by total tokens to generate a frequency distribution, **Then** the system outputs a vector of size $|V|$ representing the frequency distribution. *(Backed by FR‑006)*
2. **Given** the frequency distribution and the edge spectrum subspace, **When** the system projects the frequency distribution onto the pseudo‑inverse of the unembedding matrix ($W_U^{+} \times f$) to compute the mean embedding, **Then** the system outputs the mean embedding vector. *(Backed by FR‑005)*
3. **Given** the mean embeddings for English and non‑English models, **When** the system calculates the difference vector (shift) and compares it to the difference in WALS feature vectors, **Then** the system outputs a Pearson correlation coefficient $r$ and its 95 % confidence interval. *(Backed by FR‑016)*
4. **Given** the ranked token lists for English and non‑English models, **When** the system applies the vocabulary mapping layer to align tokens and calculates the overlap ratio of the top‑N tokens, **Then** the system reports an overlap percentage compared against a baseline generated from 10 000 randomly generated orthogonal bases (geometric baseline). *(Backed by FR‑031)*
5. **Given** the mean embeddings for two languages, **When** the system projects the mean embedding of language A onto the edge‑spectrum subspace of language B (and vice‑versa) and computes cosine similarity of the projected vectors, **Then** the system records this cross‑lingual projection similarity. *(Backed by FR‑036, FR‑040)*

### User Story 3 - Validate Statistical Significance of Shift (Priority: P3) (US-3)

The researcher needs to perform a permutation test to determine if the observed cross‑lingual similarity in the edge spectrum is statistically significantly lower than the similarity expected from within‑language variations, rejecting the null hypothesis that the shift is due to random noise or shared training dynamics. The null distribution is generated by comparing the observed similarity against similarities between the observed subspace and a set of within‑language similarity samples (shuffled language pairs or same‑language model pairs) **and** against an across‑model null distribution to capture model‑specific variability.

**Why this priority**: This provides the scientific rigor required to claim the observed shift is a real phenomenon rather than an artifact of the specific model initialization or random variation. It is the final validation step before drawing conclusions.

**Independent Test**: The system can be tested by running the permutation test with a fixed random seed and verifying that a p‑value is generated, and that the test completes within the CPU time limit without requiring GPU acceleration.

**Acceptance Scenarios**:

1. **Given** the observed cosine similarity between English and BLOOM subspaces, **When** the system generates at least 10 000 random orthogonal bases (minimum iteration count), **AND** generates within‑language and across‑model similarity samples to establish a combined null distribution, **Then** the system outputs individual component p‑values (with at least 4 decimal places) and flags significance using a Bonferroni‑adjusted α = 0.05/3. *(Backed by FR‑004)*
2. **Given** the p‑values are computed, **When** any component p‑value is below its Bonferroni‑adjusted threshold, **Then** the system outputs the corresponding component flag (e.g., “Significant within‑language shift”) in the final report.

### Edge Cases

- What happens when the SVD computation fails due to numerical instability in a specific model's $W_U$ matrix (e.g., extremely small singular values)? *(Handled by FR‑033)*
- How does the system handle models where the vocabulary sizes differ significantly, making direct token comparison impossible without a mapping layer? *(Handled by FR‑008)*
- What if the Common Crawl subset for a target language (e.g., French) is too small to generate a stable frequency distribution for the "average token" projection? *(Handled by FR‑034)*

## Requirements

### Functional Requirements

- **FR-001**: System MUST perform Singular Value Decomposition (SVD) on the unembedding matrix ($W_U$) of loaded models to extract the matrix of the leading singular vectors that constitute the “edge spectrum” subspace. (See US‑1)
- **FR-002**: System MUST compute a rotation‑invariant subspace similarity metric defined as the sum of squared cosines of the principal angles between two subspace bases **after aligning each model’s edge vectors to the common 11200‑dimensional subword space (FR‑040)**. This metric equals *k − ½‖P₁ − P₂‖_F²* and MUST report a 95 % bootstrap confidence interval for each measurement. (See US‑1)  
  *Justification*: Geometric alignment of edge‑spectrum bases captures shared anisotropy, which according to the original EmbedFilter study (Gauthier et al.) reflects a language‑agnostic “common‑sense” prior. Divergence therefore indicates language‑specific bias.
- **FR-003**: System MUST identify and rank the tokens with the highest logit weights within the extracted edge spectrum subspace for each language to attribute semantic content. (See US‑2)
- **FR-004**: System MUST perform a permutation test with **≥ 10 000** iterations using a combined null distribution (within‑language similarity samples, across‑model similarity samples, and model‑specific variability). Separate p‑values are computed for each component and significance is assessed using a Bonferroni‑adjusted threshold α = 0.05/3. The system MUST abort the pipeline if runtime exceeds **6 hours** and log a warning. (See US‑3)
- **FR-005**: System MUST compute the mean embedding vector for each language by multiplying the Moore‑Penrose pseudo‑inverse of the unembedding matrix ($W_U^{+}$) with the language‑specific token frequency vector $f$ (i.e., $W_U^{+} \times f$). (See US‑2)
- **FR-006**: System MUST acquire and validate language‑filtered corpora:  
  - English: RedPajama (https://huggingface.co/datasets/allenai/redpajama-1b) (retrieved 2026‑07‑10 09:00 UTC)  
  - French: Common Crawl French subset (https://huggingface.co/datasets/ccnet/fr)  
  - Chinese: Common Crawl Chinese subset (https://huggingface.co/datasets/ccnet/zh)  
  - Arabic: Common Crawl Arabic subset (https://huggingface.co/datasets/ccnet/ar)  
  - Swahili: Common Crawl Swahili subset (https://huggingface.co/datasets/ccnet/sw)  
  - German: Common Crawl German subset (https://huggingface.co/datasets/ccnet/de)  
  - Spanish: Common Crawl Spanish subset (https://huggingface.co/datasets/ccnet/es)  
  - Hindi: Common Crawl Hindi subset (https://huggingface.co/datasets/ccnet/hi)  
  - Japanese: Common Crawl Japanese subset (https://huggingface.co/datasets/ccnet/ja)  
  - Portuguese: Common Crawl Portuguese subset (https://huggingface.co/datasets/ccnet/pt)  
  Each subset must contain **≥ 1 000 000** tokens. (See US‑2)
- **FR-007**: System MUST acquire and process WALS typological features (official repository https://github.com/cldf-datasets/wals) and multilingual XTREME probing benchmark results (e.g., XNLI accuracy) for the target languages. All dataset URLs are verified against official sources and timestamps recorded. (See US‑2)
- **FR-008**: System MUST implement a vocabulary mapping layer using a shared subword vocabulary of size **11 200** (source: Q136293754, https://www.wikidata.org/wiki/Q136293754). The mapping procedure must:  
  1. Convert each model’s token IDs to the shared subword tokens.  
  2. Transform raw token counts into probability distributions by dividing by the total token count.  
  3. Apply length‑normalization to account for differing tokenization granularity.  
  4. Compute overlap ratios on these normalized distributions rather than raw counts.  
  This rigorous normalization eliminates confounding from vocabulary‑size differences. (See US‑2)
- **FR-009**: System MUST ensure that **all** frequency distributions are derived from the same corpus source per language: English from RedPajama, all other languages from their respective Common Crawl subsets, satisfying Constitution Principle VII. (See US‑2)
- **FR-010**: System MUST compute an **adjusted similarity metric** defined as Δ similarity = observed subspace similarity – mean similarity of matched‑architecture control pairs (see FR‑027). This isolates linguistic effects from architecture‑specific variance. (See US‑1)
- **FR-011**: System MUST store all generated artifacts under the `data/derived/` directory in accordance with the data model (e.g., `data/derived/subspace_similarity.json`). (See US‑1)
- **FR-012**: System MUST verify that all external dataset URLs (Common Crawl language‑filtered splits, RedPajama, WALS CSV, XTREME repository) are confirmed against official sources prior to download, satisfying Constitution Principle II. Verification timestamps and source citations are recorded in the final report. (See US‑2) **(See FR‑038)**
- **FR-013**: System MUST exercise each defined contract schema (`edge_spectrum.schema.yaml`, `feasibility_report.schema.yaml`, `frequency_list.schema.yaml`, `similarity_matrix.schema.yaml`, `similarity_metric.schema.yaml`, `similarity_report.schema.yaml`, `bootstrap_test.schema.yaml`, `permutation_test.schema.yaml`). (See US‑1)
- **FR-014**: System MUST produce an `edge_spectrum.json` file that conforms to `edge_spectrum.schema.yaml`, containing fields `model_name`, `top_k`, `edge_vectors`, `checksum`, and `generated_at`. (See US‑1)
- **FR-015**: System MUST generate bootstrap confidence intervals (95 % CI, ≥ 1 000 replicates) for all reported subspace similarity measurements by resampling rows of the unembedding matrix (or token samples when FR‑028 is active) and include them in the `similarity_report.json`. (See SC‑006)
- **FR-016**: System MUST conduct correlation analyses on **at least ten** languages (English, French, Chinese, Arabic, Swahili, German, Spanish, Hindi, Japanese, Portuguese). For each language pair, compute the scalar Δ similarity magnitude and the Hamming distance between their WALS feature vectors; report Pearson $r$, two‑tailed $p$‑value, and 95 % confidence interval. (See SC‑007)
- **FR-028**: System MUST extract edge‑spectrum subspaces **per language** by applying a language‑specific token mask to the unembedding matrix *after* the vocabulary mapping layer (FR‑008). The mask is constructed by selecting tokens whose frequency in language L (from FR‑006) is at least **0.1 %** of the total token count for that language. This ensures the masked matrix reflects language‑specific usage patterns while preserving comparability across models. *Note*: To assess potential confounds introduced by the mask, FR‑042 (see below) requires running the full pipeline **without** the mask as a sensitivity analysis. (See US‑1)  
- **FR-029**: System MUST compute a **uniform‑frequency baseline** by projecting a uniform token frequency vector (all tokens assigned equal probability) through the same pseudo‑inverse pipeline ($W_U^{+} \times f_{uniform}$) to obtain a baseline mean embedding. This baseline shift vector is then compared against language‑specific shift vectors in correlation analyses to test whether observed effects exceed what would be expected under a null uniform distribution. (See US‑2, SC‑010)
- **FR-030**: System MUST detect missing or corrupted model weight files, log a clear error message identifying the affected model, and continue processing any remaining valid models without aborting the pipeline. (Addresses Acceptance Scenario 2 of US‑1)
- **FR-031**: System MUST generate a geometric baseline by creating **10 000** random orthogonal bases, compute overlap percentages for token‑ranking comparisons against this baseline, and report the deviation of the observed overlap from the baseline mean. (Supports Acceptance Scenario 4 of US‑2)
- **FR-032**: System MUST conduct an ablation analysis that randomizes the language‑specific token mask (while preserving overall token count) and repeats the full pipeline; a loss of correlation with WALS (p > 0.05) validates that the original relationship is not artefactual. (See US‑2)
- **FR-033**: System MUST detect numerical instability during SVD (e.g., singular values below 1e‑12 or failure to converge) and, in such cases, log a warning, skip the affected model, and continue with remaining models. (Addresses Edge Case 1)
- **FR-034**: System MUST verify that each language‑filtered Common Crawl subset contains at least **1 000 000** tokens; if a subset falls below this threshold, the system must raise a `DataInsufficiencyError`, log the deficiency, and abort processing for that language while continuing for others. (Addresses Edge Case 3)
- **FR-035**: System MUST perform a power analysis to determine the minimum number of languages required to detect a Pearson correlation of magnitude $r=0.5$ with 80 % power at $\alpha=0.05$ (result: **≥ 29** languages). The analysis result is reported in `feasibility_report.json`; the current study with a limited set of languages is noted as under‑powered. (New requirement)
- **FR-036**: System MUST perform cross‑lingual projection of mean embeddings: for each ordered language pair (A → B), project language A’s mean embedding onto language B’s edge‑spectrum subspace **after aligning both to the common 11200‑dimensional space (FR‑040)** and compute cosine similarity; store all pairwise projection similarities in `cross_projection.json`. (New requirement, See US‑2)
- **FR-037**: System MUST monitor the conditioning of $W_U$ when computing the Moore‑Penrose pseudo‑inverse. If the condition number exceeds $1\times10^{8}$, apply Tikhonov regularization with $\lambda=1\times10^{-5}$ and log a warning. (New requirement)
- **FR-038**: System MUST enforce dataset verification: for each external URL, compute and record a checksum (e.g., SHA‑256) and compare against the official source metadata before download; any mismatch aborts the acquisition and logs the issue. (New requirement)
- **FR-040**: System MUST align all model representations to a common 11200‑dimensional subword space using the shared vocabulary mapping layer (FR‑008) and a linear projection derived from the shared embedding matrix. The alignment must preserve cosine similarity and is applied before any subspace similarity or projection calculations. (See US‑1)
- **FR-042**: System MUST run a **sensitivity analysis** by executing the entire pipeline **without** the language‑specific token mask (FR‑028) and compare the resulting Δ similarity and correlation metrics to the masked run. The analysis must be documented in `sensitivity_analysis.json` and used to assess whether the mask introduces systematic bias. (Addresses methodological soundness of FR‑028)

### Key Entities

- **Edge Spectrum Matrix**: A matrix containing the top‑100 singular vectors of the unembedding matrix $W_U$, representing the direction of anisotropy.
- **Mean Embedding Vector**: A computed embedding vector $\hat{\vh}$ derived by projecting the token frequency distribution onto the pseudo‑inverse of the unembedding matrix ($W_U^{+} \times f$), representing the centroid of the vocabulary.
- **Subspace Similarity Metric**: A scalar value derived from the sum of squared cosines of principal angles between two subspace bases, providing a rotation‑invariant measure of alignment.
- **Permutation Null Distribution**: A set of similarity scores generated by comparing the observed subspace against within‑language similarity samples, across‑model similarity samples, and model‑specific variability samples to establish a baseline for statistical testing.
- **WALS Feature Vector**: A binary vector representing the typological properties of a language (e.g., word order, noun class system).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of the anisotropy bias (subspace similarity metric) is measured against the within‑language baseline (self‑similarity) and reported with a 95 % bootstrap confidence interval. (See FR‑002, FR‑010, FR‑015)
- **SC-002**: The composition shift of dominant tokens is measured against the overlap ratio of the top tokens between English and non‑English models compared to a random orthogonal basis baseline (average overlap with random bases); the magnitude of the difference is the metric. (See FR‑003, FR‑031)
- **SC-003**: The statistical significance of the shift is measured against the component p‑values from the permutation test with Bonferroni‑adjusted α = 0.05/3. (See FR‑004, FR‑026)
- **SC-004**: The validity of the validation metric is measured against the Pearson correlation coefficient (with 95 % confidence interval) between the **baseline‑adjusted** shift vector and the difference in XTREME probing benchmark performance between language pairs. (See FR‑007, FR‑029)
- **SC-005**: The computational feasibility is measured against the constraint of completing the full SVD and permutation pipeline on a GitHub Actions ubuntu‑latest runner (multi‑core, 16 GB RAM) within **6 hours**. (See FR‑001, FR‑004)
- **SC-006**: All subspace similarity measurements are reported with 95 % confidence intervals obtained via bootstrap sampling of rows of $W_U$ (≥ 1 000 replicates). (See FR‑015)
- **SC-007**: Correlation analyses are performed on **at least ten** languages; results include Pearson $r$, two‑tailed $p$‑value, and 95 % confidence interval, ensuring sufficient statistical power is *reported* (see FR‑035). (See FR‑016)
- **SC-008**: All external dataset URLs are listed with verification timestamps, source citations, and checksum validation in the final report, satisfying constitutional verification requirements. (See FR‑012, FR‑038)
- **SC-009**: The ablation analysis (FR‑032) must yield a non‑significant correlation with WALS (p > 0.05), confirming that the original correlation is not driven by spurious mask structure. (See FR‑032)
- **SC-010**: The uniform‑frequency baseline (FR‑029) must show that language‑specific shift vectors differ significantly from the uniform baseline (p < 0.05), demonstrating genuine language‑driven effects.

## Implementation Plan

| Phase | Description | Primary Artifacts (stored under `data/derived/`) |
|-------|-------------|---------------------------------------------------|
| 1 | Load model weights, extract $W_U$, perform SVD to obtain top‑100 edge spectrum vectors (per language mask as per FR‑028 when enabled) **and align them to the common 11200‑dimensional space (FR‑040)**. | `edge_spectrum.json` (conforms to `edge_spectrum.schema.yaml`) |
| 2 | Acquire language‑filtered corpora (RedPajama for English, Common Crawl for others), compute token frequency distributions, generate `frequency_list_{lang}.json` for each language. | `frequency_list_{lang}.json` |
| 3 | Apply vocabulary mapping layer (size 11 200), compute token attribution and overlap ratios, store `token_attribution_{model}.json`. | `token_attribution_{model}.json` |
| 4 | Compute mean embeddings via $W_U^{+} \times f$, compute **uniform‑frequency baseline** (FR‑029), perform correlation analyses (FR‑016) and cross‑lingual projection (FR‑036) **in the aligned space (FR‑040)**. Produce `validation.json`, `cross_projection.json`, and `baseline_report.json`. | `validation.json`, `cross_projection.json`, `baseline_report.json` |
| 5 | Run permutation test with ≥ 10 000 iterations, generate `permutation_test.json` containing component p‑values and Bonferroni‑adjusted significance flags, and create `similarity_metric.json`. | `permutation_test.json`, `similarity_metric.json` |
| 6 | Conduct bootstrap resampling of rows of $W_U$, generate `bootstrap_test.json` (FR‑015) and `similarity_report.json` with 95 % CIs. | `bootstrap_test.json`, `similarity_report.json` |
| 7 | Perform paired‑architecture control analyses (FR‑027) and ablation study (FR‑032), generate adjusted similarity reports and ablation results. | `control_analysis.json`, `ablation_report.json` |
| 8 | Assemble all results, compute final feasibility metrics (including power analysis FR‑035) and produce `feasibility_report.json`. | `feasibility_report.json` |
| 9 | Execute sensitivity analysis without language‑specific mask (FR‑042) and store `sensitivity_analysis.json`. | `sensitivity_analysis.json` |

All artifacts are validated against their respective JSON‑schema contracts (FR‑013) and timestamps/URL verifications are recorded (FR‑012, FR‑038, FR‑042).

## Assumptions

- The Hugging Face `transformers` library and `numpy` are available and sufficient to load the model weights and perform SVD on the unembedding matrices without GPU acceleration.
- The "edge spectrum" is defined as the top‑100 singular vectors where $k = 100$, relative to the full matrix dimension, ensuring the subspace extraction fits within available RAM constraints.
- The language‑filtered RedPajama (English) and Common Crawl subsets for other languages are publicly accessible via the verified URLs listed in FR‑006 and can be downloaded during the Data Acquisition phase.
- The permutation test is computationally tractable on a standard multi‑core CPU for **≥ 10 000** iterations; if the runtime exceeds the 6‑hour threshold the system must log a warning and abort, requiring the user to allocate additional resources (as enforced by FR‑004).
- The "mean embedding" projection method using the pseudo‑inverse of $W_U$ is a valid approximation for a "common sense" prior as proposed in the original EmbedFilter paper, with the understanding that it computes the vocabulary centroid in the unembedding space.
- The models (Llama‑3, Mistral, BLOOM) are available in a format compatible with the `load_in_8bit` or `device_map="cpu"` parameters if necessary, but standard float32 loading is preferred to avoid CUDA dependencies.
- The WALS database is accessible via a public CSV download, and the mapping from model language codes to WALS language identifiers is deterministic.
- XTREME probing benchmark results are available for the target languages via the official GitHub repository (https://github.com/google-research/xtreme) and can be retrieved programmatically.
- All contract schemas referenced are defined in the `contracts/` directory and are syntactically valid JSON Schema files.
