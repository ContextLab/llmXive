# Tasks: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Inputs**: The active `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback from `david-krakauer-simulated`.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 Establish project structure, provenance, and dataset checksum verification.
  - For each external dataset URL, retrieve the official SHA‑256 checksum from source metadata, compute the checksum **before** downloading, abort on mismatch, then download and record timestamps and checksums in `data/derived/dataset_checksums.json`.
  - Paths: `code/`, `data/raw/`, `data/derived/`, `specs/001-llmxive-crosslingual/quickstart.md`.
  - Verification: `quickstart.md` contains an init command; `dataset_checksums.json` exists and matches official source hashes.

- [ ] T002 Detect and log missing or corrupted model weight files (FR‑030).
  - For each model (Llama‑3, Mistral, BLOOM) verify presence and integrity of `W_U` weights; on failure log a clear error and continue with remaining models.
  - Paths: `code/pipeline/model_loader.py`, `data/derived/model_load_log.json`.
  - Verification: `model_load_log.json` lists any missing/corrupted models.

- [ ] T003 Apply language‑specific token mask to the unembedding matrix **before** SVD extraction (FR‑028).
  - Construct per‑language token masks using frequency thresholds (≥ 0.1 % of total tokens) and mask $W_U$ accordingly.
  - Paths: `code/pipeline/mask.py`, `data/derived/masked_WU_{lang}.json`.
  - Verification: Masked matrices have correct dimensions and mask statistics recorded.

- [ ] T004 Perform SVD on each masked $W_U$ with numerical‑instability detection (FR‑001, FR‑033).
  - Compute top‑100 singular vectors; if any singular value < 1e‑12, log a warning and skip that model.
  - Paths: `code/pipeline/svd.py`, `data/derived/edge_spectrum.json`.
  - Verification: `edge_spectrum.json` conforms to `edge_spectrum.schema.yaml`; instability warnings are present in `svd_log.json`.

- [ ] T005 Align $U$ bases to the shared 11 200‑dim subword space (FR‑008, FR‑040).
  - Use the shared vocabulary mapping layer to project left singular vectors onto the common subword space.
  - Paths: `code/pipeline/align_u.py`, `data/derived/aligned_U_{model}.json`.
  - Verification: Alignment matrices have shape `(top_k, 11200)`.

- [ ] T006 Align $V$ bases across models via Procrustes alignment to a common hidden space (addresses hidden‑space dimensionality mismatch for FR‑002, FR‑036).
  - Compute Procrustes transforms so that $V$ from Llama‑3, Mistral, and BLOOM reside in the same ambient space.
  - Paths: `code/pipeline/align_v.py`, `data/derived/aligned_V_{model}.json`.
  - Verification: Pairwise Procrustes error recorded; alignment log present.

- [ ] T007 Run a thin end‑to‑end analysis on a reduced set (2 models: Llama‑3, BLOOM; 2 languages: EN, FR).
  - Compute rotation‑invariant subspace similarity (principal angles) in the aligned $V$‑space and produce a small similarity matrix.
  - Paths: `code/pipeline/orchestrator.py`, `data/derived/similarity_matrix_thin.json`.
  - Verification: Matrix contains non‑zero scores and conforms to `similarity_matrix.schema.yaml`.

## Phase 2: Full data acquisition and processing

- [ ] T008 Stream language‑filtered corpora and enforce token‑count guard (FR‑006, FR‑009, FR‑034).
  - Use `datasets.load_dataset(..., streaming=True)` for RedPajama (EN) and the ten Common Crawl subsets; abort language if < 1 000 000 tokens, logging `DataInsufficiencyError`.
  - Paths: `code/pipeline/frequency.py`, `data/derived/frequency_list_{lang}.json`, `data/derived/token_count_guard.json`.
  - Verification: Guard JSON shows PASS/FAIL per language; frequency files conform to `frequency_list.schema.yaml`.

- [ ] T009 Compute mean embedding projection with Tikhonov regularization when needed (FR‑005, FR‑037).
  - Calculate $W_U^{+} \times f$; if condition number > 1e⁸, apply regularization λ = 1e‑5 and log a warning.
  - Paths: `code/pipeline/projection.py`, `data/derived/mean_embedding_{lang}.json`.
  - Verification: Embedding files include `condition_number` and `regularization_applied` fields.

- [ ] T010 Generate uniform‑frequency baseline projection and compare shift vectors (FR‑029, SC‑010).
  - Project a uniform token frequency vector through the same pipeline and compute statistical significance of differences from language‑specific shift vectors.
  - Paths: `code/pipeline/baseline.py`, `data/derived/baseline_report.json`.
  - Verification: Report includes $p$‑values < 0.05 for significant deviations.

- [ ] T011 Rank tokens by logit weight within the edge spectrum and compute overlap ratios versus a geometric baseline of 10 000 random orthogonal bases (FR‑003, FR‑031).
  - Produce token attribution files and overlap statistics.
  - Paths: `code/pipeline/token_attribution.py`, `data/derived/token_attribution_{model}.json`.
  - Verification: Attribution files conform to `token_attribution.schema.yaml`; overlap report includes deviation from baseline mean.

- [ ] T012 Acquire and verify external WALS typological features and XTREME probing benchmark results (FR‑007).
  - Download WALS CSV and XTREME results, compute SHA‑256 checksums, and store processed feature vectors.
  - Paths: `code/pipeline/wals_xtreme.py`, `data/derived/wals_features.json`, `data/derived/xtreme_results.json`.
  - Verification: Checksums recorded; JSON conforms to appropriate schemas.

## Phase 3: Similarity, Δ‑similarity, and control analyses

- [ ] T013 Compute full similarity matrix for all model‑language pairs (producing `similarity_matrix.json`).
  - Use aligned $V$ bases from T006; store principal‑angle similarity scores.
  - Paths: `code/pipeline/similarity.py`, `data/derived/similarity_matrix.json`.
  - Verification: Matrix conforms to `similarity_matrix.schema.yaml`.

- [ ] T014 Compute matched‑architecture control pair similarities (baseline for Δ‑similarity) (FR‑010).
  - Pair models of the same architecture (e.g., Llama‑3 vs. another Llama variant) and compute similarity; store results.
  - Paths: `code/pipeline/control_pairs.py`, `data/derived/control_similarity.json`.
  - Verification: Control similarities recorded; used in Δ‑similarity calculation.

- [ ] T024 Generate matched‑architecture control analysis (control_analysis.json) (FR‑010).
  - Aggregate `control_similarity.json` to compute mean and variance of control pair similarities; output `control_analysis.json` for use in Δ‑similarity computation.
  - Paths: `code/pipeline/control_analysis.py`, `data/derived/control_analysis.json`.
  - Verification: Control analysis JSON includes mean similarity and confidence interval.

- [ ] T015 Compute Δ‑similarity metric using the baseline from T024 (FR‑010).
  - Δ = observed similarity − mean control similarity; store in `similarity_metric.json`.
  - Paths: `code/pipeline/delta_similarity.py`, `data/derived/similarity_metric.json`.
  - Verification: Metric conforms to `similarity_metric.schema.yaml`.

## Phase 4: Statistical testing and validation

- [ ] T016 Perform permutation test (≥ 10 000 iterations) with combined null distribution (within‑language, across‑model, model‑specific) and Bonferroni‑adjusted significance (FR‑004).
  - Paths: `code/pipeline/permutation.py`, `data/derived/permutation_test.json`.
  - Verification: Output conforms to `permutation_test.schema.yaml`.

- [ ] T017 Compute Pearson correlations between Δ‑similarity / shift vectors and WALS typological features and XTREME performance drops (FR‑016).
  - Paths: `code/pipeline/correlation.py`, `data/derived/validation.json`.
  - Verification: Validation file conforms to `validation.schema.yaml`.

- [ ] T018 Conduct ablation analysis with a randomized token mask (FR‑032).
  - Paths: `code/pipeline/ablation_random_mask.py`, `data/derived/ablation_random_mask.json`.
  - Verification: Ablation results show loss of correlation (p > 0.05).

- [ ] T019 Conduct sensitivity analysis **without** the language‑specific token mask (FR‑042).
  - Paths: `code/pipeline/sensitivity_no_mask.py`, `data/derived/sensitivity_analysis.json`.
  - Verification: Sensitivity report compares metrics to masked run.

## Phase 5: Uncertainty, feasibility, and reproducibility

- [ ] T020 Generate bootstrap confidence intervals (≥ 1 000 replicates) for all similarity measurements (FR‑015).
  - Paths: `code/pipeline/bootstrap.py`, `data/derived/bootstrap_test.json`.
  - Verification: Bootstrap files conform to `bootstrap_test.schema.yaml`.

- [ ] T021 Perform power analysis to assess ability to detect Pearson $r$ = 0.5 with 80 % power (FR‑035) and record in feasibility report.
  - Paths: `code/pipeline/power_analysis.py`, `data/derived/feasibility_report.json`.
  - Verification: Report conforms to `feasibility_report.schema.yaml`.

- [ ] T022 Implement reproducibility audit and final handoff (previous T008).
  - Re‑run pipeline from raw inputs, compare artifact hashes, and emit `reproducibility_audit.json`.
  - Paths: `code/pipeline/orchestrator.py`, `data/derived/reproducibility_audit.json`.
  - Verification: Audit JSON shows `passed: true` and matches stored hashes.

- [ ] T023 Validate uniform‑frequency baseline significance (SC‑010).
  - Compare language‑specific shift vectors against the uniform‑frequency baseline using statistical tests (e.g., two‑sample t‑test); report $p$‑values and flag significant deviations.
  - Paths: `code/pipeline/baseline_significance.py`, `data/derived/baseline_significance.json`.
  - Verification: Report includes $p$ < 0.05 for significant deviations.
