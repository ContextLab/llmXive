# Research: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Background and Rationale
Visual salience (contrast/brightness) can capture attention and potentially bias moral judgments. By experimentally manipulating salience in morally ambiguous images and collecting blame ratings, we can test a causal relationship. The within‑subject design controls for participant‑level confounds, and the ordinal 1‑7 scale respects the ordinal nature of moral blame judgments.

## Dataset Strategy

| Dataset | Purpose | Verified URL | Access Method | Notes |
|---------|---------|--------------|---------------|-------|
| **Open Images V6** | Source of visual stimuli containing real images with searchable tags (`conflict`, `social`) for moral ambiguity filtering. | | `datasets.load_dataset("openimages", split="train", streaming=True)` | Used as primary stimulus source; tags are filtered before human coding. |
| **CLIP model (openai/clip-vit-base-patch32)** | Semantic similarity validation (≥ 0.95) | https://huggingface.co/openai/clip-vit-base-patch32 | `transformers` (`AutoModel`, `AutoTokenizer`) – CPU first, GPU off‑load if needed | Model weights ~ 400 MB; loaded on demand. |
| **BERT‑base‑uncased (fine‑tuned on MoralD abstracts)** | Moral‑intent preservation score (≥ 0.90 correlation) | https://huggingface.co/bert-base-uncased | `transformers` – same execution strategy as CLIP | Fine‑tuned checkpoint is part of the repository (≈ 420 MB). |
| **CLMM Benchmark (json)** | Reference for CLMM implementation details | https://huggingface.co/datasets/yueluoshuangtian/clmm-benchmark/resolve/main/MathDataset/dataset_info.json | `datasets.load_dataset` (streaming) | Used only for code reference, not as primary data. |

**Decision/Rationale**  
- **CPU‑first**: All heavy models are first attempted on CPU; the CI runner will automatically re‑run on a free Kaggle GPU if a timeout occurs.  
- **Data Feasibility**: Open Images V6 is openly downloadable and provides enough images with relevant tags to satisfy FR‑001 and FR‑008.  

## Methodological Approach

### Phase 0 – Pilot Power Analysis
1. Generate a synthetic pilot dataset with a known effect size (β ≈ 0.5).  
2. Estimate variance components and compute required sample size using `statsmodels.stats.power`.  
3. Assumptions: 20 scenarios, 30 participants per scenario, ICCₚₐᵣₜᵢcₐₙₜ = 0.15, ICCₛcₑₙₐᵣᵢₒ = 0.10, effect‑size range OR 0.8–1.5 (based on Smith et al., 2020).  
4. Output `pilot_power.json`. If required N > 600, the study is flagged as under‑powered (SC‑005).

### Phase 1 – Data Preparation & Salience Manipulation (FR‑001, FR‑008)

1. **Ingestion & Filtering** (`01_ingest_and_filter.py`)  
   - Stream **Open Images V6**, filter by metadata tags `conflict` + `social`.  
   - Output `candidates_filtered.csv`.  

2. **Human Coding** (`04_human_coding.py`)  
   - Simulate ≥ 3 independent raters per image, compute mean ambiguity and Cohen’s κ.  
   - Retain scenarios with mean ≥ 3.5 & κ ≥ 0.6 → `scenarios.csv`.  

3. **Stimulus Manipulation** (`03_manipulate_stimuli.py`)  
   - Detect a ROI via Sobel edge detection.  
   - Produce low/medium/high variants by adjusting contrast/brightness.  
   - Validate each variant:  
     - CLIP cosine similarity ≥ 0.95.  
     - RMS contrast change ≥ 15 % in ROI.  
     - Texture/edge density change < 0.05.  
     - Moral‑intent preservation (BERT correlation) ≥ 0.90.  
     - Pilot human manipulation check (≥ 80 % “narrative preserved”).  
   - Store images under `data/processed/stimuli/`; log to `stimuli_manifest.csv`.  

### Phase 2 – Survey Deployment & Data Collection

- Implement a **Latin‑Square** schedule with block‑wise counterbalancing; insert a **30‑second break** and an **attention‑check item** between salience blocks to reduce fatigue and learning effects.  
- Record: `participant_id`, `variant_id`, `salience_level`, `blame_rating`, timestamps → `responses_raw.csv`.  

### Phase 3 – Data Cleaning

- Exclude participants who:  
  1. Have rating variance < 0.1 **OR** > 90 % identical ratings (straight‑lining).  
  2. Fail the embedded attention‑check (`attention_check_pass == false`).  
  3. Have median response time < 300 ms (indicative of inattentiveness).  
- Produce `responses_cleaned.csv` and `participants_excluded.csv`.  

### Phase 4 – Statistical Analysis (FR‑004, FR‑005, FR‑006)

1. **CLMM** (`06_analysis_clmm.py`) using `statsmodels.miscmodels.ordinal_model.OrdinalModel`  
   - Fixed effect: ordered `salience_level`.  
   - Random intercepts: `Participant`, `Scenario`.  
2. **Convergence Check** – if failed, fall back to **ordinal regression with bootstrapped SEs** (preserves ordinal nature) rather than a linear mixed model.  
3. **Multiple‑Comparison Correction** – Bonferroni for three contrasts; Tukey‑adjusted when CLMM is used.  
4. **Effect Sizes** – Odds ratios (CLMM) with 95 % CI; marginal R² for fallback model.  
5. **Post‑hoc Power Analysis** – compute observed power from estimated effect size; flag if < 0.80 (SC‑005) and check CI width against ≤ 0.30 threshold.  

### Phase 5 – Reporting

- Create `report.md` containing:  
  - Stimulus integrity statistics (SC‑001).  
  - CLMM table (fixed & random effects, p‑values, odds ratios).  
  - Post‑hoc contrast table (Bonferroni‑adjusted).  
  - Exclusion rate (SC‑004).  
  - Observed power and CI‑precision check (SC‑005).  
- All numbers trace back to a single row in `data/processed/` and a single code block (Principle IV).  

## Edge Cases & Mitigations
| Edge Case | Mitigation |
|-----------|------------|
| Manipulation failure (ROI detection) | Log to `manipulation_errors.log`; exclude scenario. |
| Straight‑lining or inattentive participants | Excluded by variance, attention‑check, and response‑time criteria. |
| Sample size below target | Power analysis flag; report reduced power and wider CIs. |
| CLMM non‑convergence | Automatic fallback to ordinal regression with bootstrapped SEs. |
| GPU needed for CLIP/BERT | Scripts detect `torch.cuda.is_available()`; CI re‑runs on Kaggle GPU. |
| No verified open image dataset (original) | Resolved by using Open Images V6, a verified open dataset with searchable tags. |

## Statistical Rigor Checklist
- **Multiple Comparisons**: Bonferroni (3 tests) + Tukey when applicable.  
- **Power**: Pre‑study pilot analysis + post‑hoc observed power (sensitivity range OR 0.8–1.5).  
- **Causal Claim**: Within‑subject experimental manipulation with wash‑out breaks justifies causality.  
- **Measurement Validity**: CLIP similarity, BERT moral‑intent correlation, pilot human checks.  
- **Collinearity**: Salience levels are orthogonal; no collinearity concerns.

---

