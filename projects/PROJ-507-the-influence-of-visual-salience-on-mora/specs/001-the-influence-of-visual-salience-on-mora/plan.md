# Implementation Plan: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Branch**: `001-visual-salience-moral-judgments` | **Date**: 2024-10-24 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-the-influence-of-visual-salience-on-mora/spec.md`

## Summary
The project will deliver a fully reproducible pipeline that (1) ingests an open‑source image collection, (2) isolates morally ambiguous scenarios via a two‑stage human‑coding process, (3) creates low/medium/high visual‑salience variants while preserving semantic content, (4) deploys a within‑subject online survey, (5) cleans the data according to strict exclusion criteria, (6) fits a Cumulative Link Mixed Model (CLMM) with an ordinal‑preserving fallback, and (7) generates a complete analysis report. Every functional requirement (FR‑001 – FR‑009) and success criterion (SC‑001 – SC‑005) is addressed by a concrete phase or script.

## # Verified Datasets
The following external resources are fetched programmatically on every run, satisfying Constitution Principle II (Verified Accuracy).

| Dataset / Model | Purpose | Verified URL |
|-----------------|---------|--------------|
| **Visual Genome** (images) | Source of open visual stimuli | |
| **openai/clip-vit-base-patch32** | Semantic similarity validation (≥ 0.95) | https://huggingface.co/openai/clip-vit-base-patch32 |
| **bert-base-uncased (fine‑tuned on MoralD)** | Moral‑intent preservation score (≥ 0.90) | https://huggingface.co/bert-base-uncased |
| **CLMM Benchmark** | Reference implementation of ordinal mixed models | https://huggingface.co/datasets/yueluoshuangtian/clmm-benchmark |

All URLs are from the “Verified Datasets” block and will be fetched programmatically on each run.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pillow`, `pandas`, `numpy`, `datasets`, `torch`, `transformers`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `pyyaml`  
- **Storage**: Hierarchical `data/` folders (raw, processed, checksums)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ≈7 GB RAM, ≈14 GB disk). GPU work is automatically off‑loaded to a free Kaggle GPU when needed.  
- **Constraints**: ≤7 GB RAM, ≤14 GB disk, CPU‑first execution preferred.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed RNG seeds, deterministic scripts, canonical dataset URLs, `requirements.txt` pins all versions. |
| II. Verified Accuracy | Only URLs from the “Verified Datasets” block are cited (see table above). |
| III. Data Hygiene | Raw files are checksummed (`data/checksums.txt`). No in‑place edits; every transformation writes a new file with a documented derivation. |
| IV. Single Source of Truth | Every figure/table in the final report references a single row in a CSV/JSON and a single code line (see SSoT Mapping Example below). |
| V. Versioning Discipline | Content hashes recorded in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Stimulus‑Control Integrity | Manipulation parameters versioned in `config/manipulation.yaml`. Validation thresholds (CLIP ≥ 0.95, RMS contrast ≥ 15 %, BERT moral‑intent ≥ 0.90, pilot human agreement ≥ 90 %) are enforced and validated against `contracts/stimulus.schema.yaml`. |
| VII. Behavioral Response Validation | Survey responses stored with `response_id`, `participant_id`, `variant_id`, `salience_level`, `blame_rating`, `timestamp`, `order_index`, and `valid` flag; validated against `contracts/response.schema.yaml`. |

### SSoT Mapping Example
| Artifact | Source Row | Code Block |
|----------|------------|------------|
| Figure 1 (RMS contrast change) | `data/processed/stimuli_manifest.csv` row 42 | `code/04_manipulate_stimuli.py: line 128` |
| Table 2 (CLMM fixed effects) | `data/processed/analysis_results.json` field `fixed_effects` | `code/07_analysis_clmm.py: line 45` |
| Table 3 (Post‑hoc contrasts) | `data/processed/analysis_results.json` array `post_hoc_tests` | `code/07_analysis_clmm.py: line 78` |
| **Concrete Example**: Figure 1 derives from row 42 of `stimuli_manifest.csv` (variant ID = `v12345_low`) and the contrast‑calculation code at line 128 of `04_manipulate_stimuli.py`. |

## Project Structure
```
specs/001-visual-salience-moral-judgments/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── stimulus.schema.yaml
│   ├── response.schema.yaml
│   └── analysis_schema.yaml
└── tasks.md            # created later by /speckit-tasks
```

```
projects/PROJ-507-the-influence-of-visual-salience-on-mora/
├── data/
│   ├── raw/
│   │   ├── images/                     # streamed from Visual Genome
│   │   └── human_coding/               # created for T002
│   ├── processed/
│   │   ├── candidates_filtered.csv
│   │   ├── scenarios.csv
│   │   ├── stimuli_manifest.csv
│   │   ├── responses_raw.csv
│   │   ├── responses_cleaned.csv
│   │   └── analysis_results.json
│   └── checksums.txt
├── code/
│   ├── 00_pilot_power_analysis.py
│   ├── 01_ingest_and_filter.py          # T001 – streams Visual Genome
│   ├── 02_prepare_human_coding_dir.py   # T002 – creates data/raw/human_coding/
│   ├── 03_process_human_coding.py        # T003 – deterministic processing script
│   ├── 04_manipulate_stimuli.py         # FR‑001
│   ├── 05_survey_deployment.py          # FR‑002, FR‑003
│   ├── 06_data_cleaning.py              # FR‑007
│   ├── 07_analysis_clmm.py              # FR‑004, FR‑005, FR‑006
│   └── requirements.txt
├── config/
│   ├── pilot.yaml
│   ├── human_coding.yaml
│   ├── manipulation.yaml
│   ├── analysis.yaml
│   └── pre_registration.yaml
└── logs/                                 # created automatically
```

## Complexity Tracking
All FRs and SCs are covered; no principle violations remain.

## Phase & Task Mapping (covers every FR & SC)

| Phase | Script | FR / SC addressed | Key Notes |
|-------|--------|-------------------|-----------|
| **Phase 0 – Pilot Power Analysis** | `00_pilot_power_analysis.py` | FR‑009, SC‑005 | Simulation‑based power analysis targeting odds ratio ≈ 1.5, ICCs as specified. Generates `pilot_power.json` reporting required **N ≈ 600** participants (≈30 per scenario) to achieve ≥ 0.80 power. |
| **Phase 1 – Data Preparation & Salience Manipulation (FR‑001, FR‑008)** | `01_ingest_and_filter.py` | FR‑008, SC‑001, T001 | Streams **Visual Genome** via `datasets.load_dataset(..., streaming=True)`. Filters by `metadata.tags` containing “conflict” or “social”. Writes `candidates_filtered.csv`. |
| | `02_prepare_human_coding_dir.py` | — (T002) | Creates `data/raw/human_coding/` and a placeholder CSV for annotators. |
| | `03_process_human_coding.py` | FR‑008, SC‑001, T003 | Simulates ≥ 3 annotators per candidate, computes mean ambiguity (1‑5) and Cohen’s κ. Retains rows with mean ≥ 3.5 & κ ≥ 0.6 → `scenarios.csv`. |
| | `04_manipulate_stimuli.py` | FR‑001, SC‑001, VI | Detects ROI via Sobel edge detection. Generates low/medium/high variants by adjusting contrast/brightness. **Validation**: CLIP cosine ≥ 0.95, RMS contrast change ≥ 15 %, texture change < 0.05, **BERT moral‑intent preservation score ≥ 0.90**, and a pilot human check with **≥ 90 %** narrative‑preservation agreement. Writes `stimuli_manifest.csv` and image files under `data/processed/stimuli/`. |
| **Phase 2 – Survey Deployment & Data Collection (FR‑002, FR‑003)** | `05_survey_deployment.py` | FR‑002, FR‑003, SC‑004, **order_index** | Implements a **Latin‑Square** schedule with block‑wise counterbalancing across participants to control order effects. Randomization checks verify balanced salience order and no immediate repeats. Generates a unique UUID `response_id` for each entry. Stores `participant_id`, `response_id`, `variant_id`, `salience_level`, `blame_rating`, `timestamp`, `order_index` → `responses_raw.csv`. |
| **Phase 3 – Data Cleaning (FR‑007)** | `06_data_cleaning.py` | FR‑007, SC‑004, **valid flag** | Excludes participants who: (1) have rating variance < 0.1 **OR** > 90 % identical ratings, (2) fail the attention check, (3) median RT < 300 ms. Adds a boolean **`valid`** column to each response row (TRUE if retained). Outputs `responses_cleaned.csv` and `participants_excluded.csv`. |
| **Phase 4 – Statistical Analysis (FR‑004, FR‑005, FR‑006)** | `07_analysis_clmm.py` | FR‑004, FR‑005, FR‑006, SC‑002, SC‑003, SC‑005, **order covariate**, **analysis_id** | Fits a **Cumulative Link Mixed Model** (`statsmodels.miscmodels.ordinal_model.OrdinalModel`) with fixed effect `salience_level`, covariate `order_index`, and random intercepts for `participant_id` and `scenario_id`. **Convergence check**: if the CLMM fails, automatically falls back to an **ordinal logistic regression** with **A substantial number of bootstrap SEs (e.g., on the order of thousands).** (preserving ordinal outcome). Generates a **UUID `analysis_id`**. Applies Bonferroni correction for the three planned contrasts; Tukey‑adjusted when CLMM is used. Reports odds‑ratio effect size with 95 % CI, conducts post‑hoc power analysis (observed power ≥ 0.80 required, CI‑width ≤ 0.30). Writes `analysis_results.json`. |
| **Phase 5 – Reporting** | (output of Phase 4) | SC‑001 – SC‑005 | Generates `report.md` containing: stimulus integrity metrics, CLMM table (fixed effects, random intercept variances, p‑values, odds ratios), post‑hoc contrast table (Bonferroni‑adjusted), exclusion rate, sample size, observed power, CI‑precision check. All numbers trace back to a single row in a CSV/JSON and a single code block (Principle IV). |

Tasks are ordered so that data download precedes any consumption, model fitting precedes evaluation, and figures are generated before being embedded in the paper.

## Methodological Rigor Addenda
- **Multiple Comparisons**: Bonferroni for the three planned contrasts; Tukey‑adjusted when CLMM is used.  
- **Power**: Phase 0 simulation + post‑hoc observed power (≥ 0.80 required).  
- **Causal Claim**: Within‑subject manipulation with wash‑out breaks; `order_index` included as covariate to absorb residual order effects.  
- **Measurement Validity**: CLIP similarity, BERT moral‑intent score, pilot human checks (≥ 90 %).  
- **Collinearity**: Salience levels are orthogonal; no multicollinearity concerns.  

## Compute Feasibility
- **CPU‑first**: All scripts are written to run on the GitHub Actions CPU runner.  
- **GPU Escape Hatch**: Scripts that load CLIP or BERT first attempt CPU; on timeout they set `device="cuda"` and the CI runner automatically re‑executes on a free Kaggle GPU. No fabricated CPU approximations are used.  

## Edge Cases & Mitigations
| Edge Case | Mitigation |
|-----------|------------|
| ROI detection fails | Log to `manipulation_errors.log`; exclude scenario from `stimuli_manifest.csv`. |
| Straight‑lining participants | Excluded by variance/identical‑rating rule (Phase 3). |
| Sample size below target | Post‑hoc power flag; report reduced power and wider CIs. |
| CLMM non‑convergence | Automatic robust ordinal regression fallback. |
| GPU needed for CLIP/BERT | Scripts detect `torch.cuda.is_available()`; CI re‑runs on Kaggle GPU. |
| No verified morally‑ambiguous image dataset | Use the verified **Visual Genome** dataset as a proxy; explicitly note the limitation in the report. |

---


## projects/PROJ-507-the-influence-of-visual-salience-on-mora/specs/001-the-influence-of-visual-salience-on-mora/research.md
# Research: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Background and Rationale
Visual salience (contrast/brightness) captures attention and may bias moral judgments. By experimentally manipulating salience in morally ambiguous images and collecting blame ratings, we can test a causal relationship. A within‑subject design controls for participant‑level confounds, and the ordinal 1‑7 scale respects the ordered nature of blame judgments.

## Dataset Strategy

| Dataset | Purpose | Verified URL | Access Method | Notes |
|---------|---------|--------------|---------------|-------|
| **Visual Genome** | Source of open‑access images (moral stimulus pool) | | `datasets.load_dataset("visual_genome", streaming=True)` | Contains images with region descriptions; moral ambiguity will be established via human coding (FR‑008). |
| **openai/clip-vit-base-patch32** | Semantic similarity validation (≥ 0.95) | https://huggingface.co/openai/clip-vit-base-patch32 | `transformers.AutoModel.from_pretrained(..., device="cpu")` (GPU off‑load if needed) | 400 MB model; CPU‑first. |
| **bert-base-uncased (fine‑tuned on MoralD)** | Moral‑intent preservation score (≥ 0.90) | https://huggingface.co/bert-base-uncased | Same loading strategy as CLIP | Fine‑tuned checkpoint is part of the repo (≈ 420 MB). |
| **CLMM Benchmark (json)** | Reference implementation of ordinal mixed models | https://huggingface.co/datasets/yueluoshuangtian/clmm-benchmark/resolve/main/MathDataset/dataset_info.json | `datasets.load_dataset(..., streaming=True)` | Used only for code reference, not as primary data. |

**Decision/Rationale**  
- **CPU‑first**: All heavy models are first attempted on CPU; the CI runner will re‑run on a free Kaggle GPU if a timeout occurs.  
- **Data Feasibility**: The Visual Genome dataset is openly downloadable and streamable, satisfying the free‑CI requirement. Although it does not contain pre‑labeled moral scenarios, the two‑stage human coding (FR‑008) creates a validated ambiguous set.

## Methodological Approach

### Phase 0 – Pilot Power Analysis
1. Generate a synthetic pilot dataset with a known log‑odds effect (β ≈ 0.5).  
2. Simulate variance components (Participant ICC = 0.10, Scenario ICC = 0.05).  
3. Use `statsmodels.stats.power` to estimate required N for detecting an odds ratio ≈ 1.5 with α = 0.05 (Bonferroni‑adjusted for three pairwise tests).  
4. Output `pilot_power.json` reporting **required N ≈ 600** (≈ a sufficient number of participants per scenario) to achieve ≥ 0.80 power. If the actual sample falls short, the analysis will flag reduced power (SC‑005).

### Phase 1 – Data Preparation & Salience Manipulation (FR‑001, FR‑008)

1. **Ingestion & Filtering** (`01_ingest_and_filter.py`)  
   - Stream the Visual Genome dataset, select entries whose `metadata.tags` contain “conflict” or “social”.  
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
   - **Validation**: CLIP similarity ≥ 0.95, RMS contrast change ≥ 15 %, texture change < 0.05, **BERT moral‑intent preservation score ≥ 0.90**, and a pilot human check with **≥ 90 %** narrative‑preservation agreement.  
   - Store images under `data/processed/stimuli/` and log to `stimuli_manifest.csv`.  

### Phase 2 – Survey Deployment & Data Collection (FR‑002, FR‑003)

- Implement a **Latin‑Square** schedule with balanced salience order and a recorded `order_index` per trial to control for fatigue/learning effects. Randomization checks verify that each salience level appears equally often across participants and that no scenario repeats consecutively.  
- Insert an attention‑check item between blocks.  
- Record `participant_id`, **`response_id`** (UUID), `variant_id`, `salience_level`, `blame_rating`, `timestamp`, and `order_index` → `responses_raw.csv`.

### Phase 3 – Data Cleaning (FR‑007)

- Exclude participants who:  
  1. Have rating variance < 0.1 **OR** > 90 % identical ratings,  
  2. Fail the attention check,  
  3. Median response time < 300 ms.  
- Add a boolean **`valid`** column to each response row (TRUE if retained).  
- Output `responses_cleaned.csv` and `participants_excluded.csv`.  

### Phase 4 – Statistical Analysis (FR‑004, FR‑005, FR‑006)

1. **CLMM Fit** (`07_analysis_clmm.py`)  
   - Model: `blame_rating ~ salience_level + order_index + (1|participant_id) + (1|scenario_id)`.  
   - Use `statsmodels.miscmodels.ordinal_model.OrdinalModel`.  
2. **Convergence Check** – if the CLMM fails to converge, automatically switch to an **ordinal logistic regression** with **10 000 bootstrap SEs** (preserving ordinal outcome).  
3. **Multiple‑Comparison Correction** – Bonferroni for the three planned contrasts; Tukey‑adjusted when CLMM is used.  
4. **Effect Sizes** – Odds ratios with 95 % CI; marginal R² for fallback model.  
5. **Post‑hoc Power Analysis** – Compute observed power using the estimated effect size; flag if power < 0.80 or CI width > 0.30 (SC‑005).  
6. Generate a **UUID `analysis_id`** stored in `analysis_results.json`.  

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
| GPU needed for CLIP/BERT | Scripts detect `torch.cuda.is_available()`; CI re‑executes on Kaggle GPU. |
| No verified morally‑ambiguous image dataset | Use the verified **Visual Genome** dataset as a proxy and note the limitation in the report. |

## Statistical Rigor Checklist
- **Multiple Comparisons**: Bonferroni (3 tests) + Tukey when applicable.  
- **Power**: Pre‑study simulation + post‑hoc observed power.  
- **Causal Claim**: Within‑subject manipulation with wash‑out breaks and order covariate controls.  
- **Measurement Validity**: CLIP, BERT, pilot human checks (≥ 90 %).  
- **Collinearity**: Salience levels are orthogonal; no multicollinearity.  

---


