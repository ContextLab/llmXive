# Research: ShutterMuse: Capture-Time Photography Guidance with MLLMs

## Research Question
**Reframed (associational):** *Are errors in MLLM‑generated photography guidance *associated* with demographic or environmental factors, and do different architectures exhibit distinct patterns of **potential reasoning** versus data‑driven failures?*
We avoid causal language in line with the observational nature of the study (Principle VII).

## Dataset Strategy

The project relies on the following verified datasets and loaders. All sources are either canonical HuggingFace datasets or officially hosted scripts.

| Dataset / Source | Purpose | Verified URL / Loader | Notes |
|------------------|---------|-----------------------|-------|
| **AVA** | Ground‑truth composition tags (lighting, angle, rule‑of‑thirds, etc.) | Official AVA download script (`src/download.py` uses `) | Images and JSON metadata are fetched and verified via cryptographic checksums. |
| **COCO** | Diverse image pool and caption/pose context | `datasets.load_dataset("coco")` (HuggingFace) | Provides image IDs and optional pose captions. |
| **Hallucination_MLLMs** | Validation of “Hallucinated Object” categorization logic | `datasets.load_dataset("LongThan/Hallucination_MLLMs")` | Used only for internal validation, not for primary analysis. |
| **FairFace (weights via deepface)** | Demographic inference (gender, age, ethnicity) | `deepface` package (version 0.0.83) with bundled FairFace weights | Applied to cropped primary face region; only records with confidence ≥ 0.85 are retained for bias analysis (FR‑008). |
| **GPT‑4V** | Commercial model comparison | Cloud API (OpenAI) – requires `OPENAI_API_KEY` | Rate‑limit handling per FR‑006. |

### Dataset Variable Fit
- **Required variables:** image pixels, composition tags, lighting condition, (optional) subject demographics, face bounding box.
- **Fit check:** AVA supplies composition tags; COCO supplies diverse images. Demographics are *derived* via FairFace on detected faces (see Phase 1). Images lacking a detectable primary face are still processed for error categorization but excluded from bias analysis (FR‑007).

## Methodology

### Phase 1 – Data Ingestion & Preprocessing (FR‑001, FR‑008)
1. **Download & Sample** – `src/download.py` fetches AVA & COCO, then randomly samples **30 images per model** (90 total) using a fixed seed (`seed=42`).
2. **Face Detection** – `src/face_detect.py` extracts the primary face bounding box (`face_bbox`). Images without a detectable primary face are **excluded from bias analysis** but retained for general error logging (FR‑007).
3. **Demographic Inference** – `src/demographics.py` runs FairFace on the cropped face region. Records with `confidence ≥ 0.85` are kept; others are excluded from bias analysis but retained for error logging.
4. **Image Quality Metric** – Compute average brightness (`image_quality`) per image to serve as a covariate controlling for selection bias (see Scientific Soundness concerns).

### Phase 2 – MLLM Inference & Error Categorization (FR‑002, FR‑003, FR‑006)
1. **Prompt Library** – Two prompt types:
 - **Standard Prompt:** “Analyze this image for photography composition. Suggest capture‑time adjustments for lighting, angle, and rule of thirds.”
 - **Counterfactual Prompt:** “What if the lighting were *low‑light*? How would you change the composition?”
 Counterfactual prompts are **exploratory**; they do **not** change the visual input. Any logical inconsistency observed is recorded as **“Potential Reasoning Error (hypothesis)”** rather than a definitive reasoning failure.
2. **Retry / Rate‑Limit Handling** – Exponential backoff (max 3 retries). If cumulative wait > 5 min, the script pauses and logs a warning (Edge Case).
3. **Parsing & Categorization** – `src/categorization.py` maps model output to error categories:
 - “Hallucinated Object”
 - “Incorrect Rule Application”
 - “Missing Advice”
 - “Correct”
 - “Parsing Failure”
 - **“Potential Reasoning Error (hypothesis)”** – assigned only for counterfactual prompts where the response contradicts logical expectations while the visual input remains unchanged.

### Phase 3 – Statistical Analysis (FR‑004, US‑2)
1. **Contingency Tables** – Build tables for `Error Type` vs. `Demographic Group` (gender, age, ethnicity) and `Error Type` vs. `Lighting Condition`. Include `image_quality` as a covariate to control for confounding.
2. **Test Selection Logic**:
 - Compute expected cell frequencies.
 - **If all expected ≥ 5** → **Chi‑square** (`scipy.stats.chi2_contingency`).
 - **If any expected < 5** **and** the table is **2×2** → **Fisher’s Exact**.
 - **If any expected < 5** **and** the table has **more than 2 dimensions** → **Monte‑Carlo chi‑square** (`scipy.stats.chi2_contingency(..., monte_carlo=True, n_iter=10000)`).
3. **Multiple‑Comparison Correction** – Apply **Bonferroni** correction across all tested variable pairs; record the method in `correction_applied`.
4. **Effect Size & Confidence** – Report **Cramér’s V** with **bootstrap 95 % confidence intervals** (10 000 resamples). Optionally provide a **Bayesian posterior** for the effect size in supplemental material (addresses low‑power concerns).
5. **Bias Correlation Reporting** – For each demographic group, output error rates, test statistics, p‑values, and effect sizes. Non‑significant results are explicitly reported.

### Phase 4 – Architectural Comparison (US‑3)
1. **Aggregate Error Rates** – Compute per‑model error frequencies, separating “Potential Reasoning Errors (hypothesis)” from other categories.
2. **Counterfactual Insight** – Summarize each model’s consistency on counterfactual prompts; the model with the lowest proportion of hypothesis‑labeled errors is highlighted, **but** we note that this does **not** constitute proof of superior reasoning capability (Principle VII).
3. **Baseline Comparison** – Contrast model error rates with the deferred human‑expert baseline (SC‑003). Since the baseline is not directly comparable, we report relative differences only.
4. **Limitations & Future Work** – Emphasize that counterfactual prompts cannot definitively separate reasoning from data‑driven failures without a synthetic control dataset. Propose a future experiment with synthetic images where ground‑truth lighting changes are known, enabling causal attribution.

### Phase 5 – Reporting & Validation
1. **Report Generation** – `src/report.py` produces `results/report.md` containing tables, effect sizes, methodological notes, and explicit discussion of limitations.
2. **Contract Validation** – `src/validate_contracts.py` checks `error_records.csv` and `analysis_results.csv` against the schemas in `contracts/`.
3. **State Update** – `src/state_update.py` records SHA‑256 hashes of all output artifacts and updates `updated_at` in `state/project_state.yaml`.
4. **Reproducibility Check** – CI re‑runs the full pipeline on a **10‑image subset** to ensure end‑to‑end reproducibility (Principle I).

## Statistical Rigor & Feasibility
- **Multiple Comparisons:** Bonferroni correction applied.
- **Sample‑Size / Power:** With 90 images the study is **indicative**; power limitations are acknowledged and results are framed as trends rather than definitive population claims (addressing methodology‑bfdef8c4 and scientific_soundness‑667645ed).
- **Observational Design:** All claims are associational; no causal inference is made (addressing methodology‑bfdef8c4).
- **Collinearity & Confounding:** `image_quality` is included as a covariate to mitigate selection bias from confidence‑filtered demographics (addressing scientific_soundness‑c18e6e25).
- **Compute Feasibility:** All steps run on CPU‑only GitHub Actions runner within the prescribed wall‑clock limit.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| FairFace CPU latency | Reduce sample size to a manageable number of images per model; parallelize across two cores. |
| GPT‑4V rate limits | Exponential backoff, pause after >5 min of continuous failures. |
| Sparse contingency tables | Monte‑Carlo chi‑square fallback; collapse rare error categories into “Other”. |
| Selection bias from confidence filtering | Include `image_quality` covariate; perform stratified sensitivity analysis. |
| Counterfactual interpretation validity | Frame as hypothesis generation; outline synthetic‑data future experiment. |