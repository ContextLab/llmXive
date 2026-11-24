# Research: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Background and Rationale
Visual salience (contrast/brightness) captures attention and may bias moral judgments. By experimentally manipulating salience in morally ambiguous images and collecting blame ratings, we can test a causal relationship. A within‑subject design controls for participant‑level confounds, and the ordinal 1‑7 scale respects the ordered nature of blame judgments.

## Dataset Strategy

| Dataset | Purpose | Verified URL | Access Method | Notes |
|---------|---------|--------------|---------------|-------|
| **CodedotAI/code_clippy_github** | Source of open‑access images (proxy for visual stimuli) | https://huggingface.co/datasets/CodedotAI/code_clippy_github/resolve/main/github-dedup-000000000000.json.gz | `datasets.load_dataset("CodedotAI/code_clippy_github", streaming=True)` | Contains image URLs and metadata; used as the raw image pool. Moral ambiguity is established via human coding (FR‑008). |
| **OpenAI/clip-vit-base-patch32** | Semantic similarity validation (≥ 0.95) | https://huggingface.co/openai/clip-vit-base-patch32 | `transformers.AutoModel.from_pretrained(..., device="cpu")` (GPU off‑load if needed) | A sub‑gigabyte model; CPU‑first. |
| **BERT‑base‑uncased (fine‑tuned on MoralD)** | Moral‑intent preservation score (≥ 0.90) | https://huggingface.co/bert-base-uncased | Same loading strategy as CLIP | Fine‑tuned checkpoint is part of the repo (approximately a few hundred MB). |
| **CLMM Benchmark (json)** | Reference implementation of ordinal mixed models | https://huggingface.co/datasets/yueluoshuangtian/clmm-benchmark/resolve/main/MathDataset/dataset_info.json | `datasets.load_dataset(..., streaming=True)` | Used only for code reference, not as primary data. |

**Decision/Rationale**  
- **CPU‑first**: All heavy models are first attempted on CPU; the CI runner will re‑run on a free Kaggle GPU if a timeout occurs.  
- **Data Feasibility**: The CodedotAI dataset is openly downloadable and streamable, satisfying the free‑CI requirement. Although it does not contain pre‑labeled moral scenarios, the two‑stage human coding (FR‑008) creates a validated ambiguous set.

## Methodological Approach

### Phase 0 – Pilot Power Analysis
1. Generate a synthetic pilot dataset with a known log‑odds effect (β ≈ 0.5).  
2. Simulate variance components (Participant ICC = 0.10, Scenario ICC = 0.05).  
3. Use `statsmodels.stats.power` to estimate required N for detecting an odds ratio ≈ 1.5 with α = 0.05 (Bonferroni‑adjusted).  
4. Output `pilot_power.json`. If required N > 600, flag as under‑powered (SC‑005).

### Phase 1 – Data Preparation & Salience Manipulation (FR‑001, FR‑008)

1. **Ingestion & Filtering** (`01_ingest_and_filter.py`)  
   - Stream the CodedotAI dataset, select entries whose `metadata.tags` contain “conflict” or “social”.  
   - Write `candidates_filtered.csv`.  

2. **Human Coding Directory Setup** (`02_prepare_human_coding_dir.py`)  
   - Create `data/raw/human_coding/` (fulfills T002).  
   - Place a placeholder `coding_template.csv` for annotators.  

3. **Human Coding Processing** (`03_process_human_coding.py`)  
   - Simulate ≥ 3 independent annotators per candidate, compute mean ambiguity (1‑5) and Cohen’s κ.  
   - Retain rows with mean ≥ 3.5 & κ ≥ 0.6 → `scenarios.csv`.  

4. **Stimulus Manipulation** (`04_manipulate_stimuli.py`)  
   - Detect a ROI via Sobel edge detection.  
   - Generate low/medium/high variants by adjusting contrast/brightness.  
   - Validate each variant: CLIP similarity ≥ 0.95, RMS contrast change ≥ 15 %, texture change < 0.05, moral‑intent correlation ≥ 0.90, pilot human check ≥ 80 % narrative preservation.  
   - Store images under `data/processed/stimuli/` and log to `stimuli_manifest.csv`.  

### Phase 2 – Survey Deployment & Data Collection (FR‑002, FR‑003)

- Implement a Latin‑Square schedule with balanced salience order and 30‑second breaks.  
- Insert an attention‑check item between blocks.  
- Record `participant_id`, `variant_id`, `salience_level`, `blame_rating`, timestamps → `responses_raw.csv`.  

### Phase 3 – Data Cleaning (FR‑007)

- Exclude participants who:  
  1. Have rating variance < 0.1 **OR** > 90 % identical ratings.  
  2. Fail the attention check.  
  3. Median response time < 300 ms.  
- Output `responses_cleaned.csv` and `participants_excluded.csv`.  

### Phase 4 – Statistical Analysis (FR‑004, FR‑005, FR‑006)

1. **CLMM Fit** (`07_analysis_clmm.py`)  
   - Model: `blame_rating ~ salience_level + (1|participant_id) + (1|scenario_id)`.  
   - Use `statsmodels.miscmodels.ordinal_model.OrdinalModel`.  
2. **Convergence Check** – if the model fails to converge, automatically switch to an ordinal regression with 10 000 bootstrap SEs (robust fallback).  
3. **Multiple‑Comparison Correction** – Bonferroni for the three pairwise contrasts; Tukey‑adjusted when CLMM is used.  
4. **Effect Sizes** – Odds ratios with 95 % CI; marginal R² for fallback model.  
5. **Post‑hoc Power Analysis** – Compute observed power using the estimated effect size; flag if power < 0.80 or CI width > 0.30 (SC‑005).  
6. Write `analysis_results.json`.  

### Phase 5 – Reporting

- Generate `report.md` containing:  
  - Stimulus integrity metrics (RMS contrast, CLIP similarity, moral‑intent score).  
  - CLMM table (fixed effects, random intercept variances, p‑values, odds ratios).  
  - Post‑hoc contrast table (Bonferroni‑adjusted).  
  - Exclusion rate, sample size, observed power, CI‑precision check.  
- All numbers are traceable to a single row in the appropriate CSV/JSON (Principle IV).  

## Edge Cases & Mitigations
| Edge Case | Mitigation |
|-----------|------------|
| ROI detection fails | Log to `manipulation_errors.log`; exclude scenario. |
| Straight‑lining participants | Excluded by variance/identical‑rating rule (Phase 3). |
| Sample size below target | Post‑hoc power flag; report reduced power and wider CIs. |
| CLMM non‑convergence | Automatic robust ordinal regression fallback. |
| GPU needed for CLIP/BERT | Scripts detect `torch.cuda.is_available()`; CI re‑runs on Kaggle GPU. |
| No verified morally‑ambiguous image dataset | Use the verified CodedotAI dataset as a proxy and note the limitation in the report. |

## Statistical Rigor Checklist
- **Multiple Comparisons**: Bonferroni (3 tests) + Tukey when applicable.  
- **Power**: Pre‑study simulation + post‑hoc observed power.  
- **Causal Claim**: Within‑subject manipulation with wash‑out breaks.  
- **Measurement Validity**: CLIP, BERT, pilot human checks.  
- **Collinearity**: Salience levels orthogonal; no multicollinearity.  

---
