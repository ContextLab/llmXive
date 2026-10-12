# Research: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## 1. Research Question & Hypotheses

**Primary Question**: Is *derived* prime valence associated with IAT response times toward ambiguous social stimuli, and is that association moderated by stimulus ambiguity?

| Hypothesis | Direction |
|------------|-----------|
| **H1** (Main effect) | Negative-valence primes associated with longer RTs vs. positive-valence primes |
| **H2** (Interaction) | The valence–RT association is amplified for high-ambiguity targets |
| **H3** (Framing) | All relationships reported as **associational** (FR-003) |

## 2. Dataset Strategy

| Dataset | Purpose | Verified URL | Load Method | Notes |
|---|---|---|---|---|
| **ia_test_embeddings** (primary ingest target) | Candidate IAT dataset | `https://huggingface.co/datasets/davanstrien/ia_test_embeddings/resolve/main/data/train-00000-of-00001-82feb90c086b8e08.parquet` | direct HTTP GET / `datasets.load_dataset` | **Dataset-variable audit: this dataset does NOT contain trial-level `response_time`, `participant_id`, or `stimulus_id` columns** (it is an embeddings dataset). The ingestion gate will therefore halt with `Data Gap: Schema Mismatch`. |
| Other verified URLs (iati, osf_loglikelihood, GET, OAuth datasets) | Reviewed as candidate substitutes | See verified-sources block | programmatic loaders | **None contain IAT response-time data with stimulus linkage** — they are aid-transparency, NLP-loglikelihood, and API-security datasets. No substitute for the research question exists among verified sources. |

### Data Availability Assessment (fatal-flaw audit, stated explicitly)

- The spec requires trial-level response times, stimulus IDs, prime/target images, and (optionally) demographics. **No dataset in the verified block contains these variables.** Per the planning rules this is a **fatal dataset-variable mismatch**: the plan does not proceed as if any verified dataset fits, does not invent a mirror URL, and does not synthesize trial data.
- **Required scope action**: the spec must name a verified open IAT dataset (e.g., an OSF project with direct file URLs — currently unverified, so no URL is cited here) or reframe the question to variables present in a verified dataset.
- The pipeline is nevertheless fully implemented: the ingestion gate produces a real data-gap artifact, and all downstream statistical/reporting code is unit-tested against small fixture files (clearly labeled as test fixtures, never presented as study results).

## 3. Statistical Methodology

### 3.1 Model Specification (conditional on demographics availability)

**Case A – demographics present**:
RT_ij = β0 + β1·Valence_i + β2·Ambiguity_i + β3·(Valence×Ambiguity)_i + β_age·Age + β_gender·Gender + β_edu·Education + u_j + ε_ij

**Case B – demographics missing**: drop the covariate terms (no imputation; a `Demographics Missing` flag is logged).

- `u_j` = random intercept for participant j (repeated measures).
- Robust (Huber-White) SE because predictors are derived (FR-001/FR-002).
- **Valence-only fallback**: if ambiguity is unavailable, `stimulus_ambiguity` remains as an empty column, `state/analysis_scope.json` records `scope: "valence_only"`, and only the valence main effect is fit.

### 3.2 Rigor & Corrections

- **Multiple comparisons**: Benjamini-Hochberg FDR over all fixed-effect p-values (FR-004).
- **Collinearity**: VIF computed on the design matrix **before** fitting; VIF > 5.0 flags and suppresses independent-effect claims (FR-005). Pearson |r| > 0.7 between valence and ambiguity drops the interaction term with a logged warning.
- **Power**: a priori approximation via `statsmodels.stats.power` (small-to-medium effect f = 0.15, α = 0.05, power = 0.80 → N ≈ 350 trials, `[deferred]` exact figure to implementation). If the post-filter dataset is smaller, a "Power Limitation" note is added to the PDF. Given the current data gap, the power limitation is acknowledged as binding until a valid dataset is supplied.
- **Causal framing**: observational secondary analysis with derived predictors → all claims associational (FR-003).
- **Measurement validity**: derived valence/ambiguity scores are model-based proxies, not validated instruments; this limitation is stated in the report. Human-validated valence norms would be preferred but are not available in verified sources.

### 3.3 Derivation Strategy (mutually independent)

- **Valence**: lexical valence dictionary for word stimuli; CPU emotion classifier (`torch` CPU) for image stimuli (FR-002).
- **Ambiguity**: WordNet sense-count Lexical Ambiguity Index for words; Laplacian texture variance for images.
- The two derivations share no inputs, avoiding circular validation.

### 3.4 Sensitivity Analysis (FR-006)

α ∈ {0.01, 0.05, 0.10}; FDR-corrected p-values re-evaluated at each α; results in `reports/sensitivity_analysis.csv` and summarized in the PDF.

## 4. Compute Feasibility

- **CPU-only**: all steps fit 2 cores / 7 GB RAM / 6 h. No GPU methods are planned; the spec's CPU-only assumption is honored.
- **Streaming**: `code/streaming.py` handles >7 GB inputs via `datasets.load_dataset(..., streaming=True)`; verified with a synthetic >7 GB temp Parquet (mechanics test only, never analysis data).

## 5. Decision Rationale

| Decision | Rationale |
|---|---|
| Hardcoded single URL in `config.py` | Deterministic ingestion (resolves verifier concern about "which URL"); validated against `data/verified_sources.json` (the authoritative artifact, schema-defined). |
| Threshold in `config.py` | Eliminates the circular threshold-definition dependency. |
| VIF before fitting | VIF is a design-matrix property; computing it pre-fit prevents fitting a collinear model (FR-005). |
| FDR over Bonferroni | Retains power for exploratory interaction tests while controlling FDR. |
| PDF always generated | Guarantees `reports/final_report.pdf` exists even on data-gap halt (SC-003; resolves rejected T036). |
| Data-gap halt instead of substitution | No verified dataset fits the research question; fabricating data would violate the fabrication gate. Scope revision flagged to the spec. |
| `pip.conf` with `--extra-index-url https://download.pytorch.org/whl/cpu` | Deterministic CPU-torch install in clean environments. |
| Logging created by first CLI run | `code/logs/pipeline.log` is produced by executing `python code/main.py --step ingest` (resolves rejected T009); the verification step runs the CLI and checks log entries exist. |
