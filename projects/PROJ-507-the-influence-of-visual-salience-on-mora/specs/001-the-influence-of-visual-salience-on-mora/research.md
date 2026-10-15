# Research: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Background and Rationale
Visual salience (contrast/brightness) can bias attention and thereby alter moral judgments. A within‑subject experiment manipulating salience in morally ambiguous images allows a causal test of this hypothesis. The design respects the experimental constraints of the specification (ordinal 1‑7 blame scale, randomization, and robust statistical testing).

## Dataset Strategy

| Dataset | Purpose | Verified URL | Access Method | Notes |
|---------|---------|--------------|---------------|-------|
| **Visual Genome** (image metadata) | Source of everyday scenes with potential moral ambiguity | https://huggingface.co/datasets/visual_genome | `datasets.load_dataset("visual_genome", split="train", streaming=True)` | Provides image IDs, object annotations, and scene descriptions. Moral ambiguity will be identified via human coding (FR‑008). |
| **CLIP model** | Semantic similarity validation (≥ 0.95) | https://huggingface.co/openai/clip-vit-base-patch32 | `transformers` on‑the‑fly (CPU; GPU off‑load if needed) | Used only for similarity scores; no large pretrained weights stored locally. |
| **BERT‑base‑uncased** (fine‑tuned on MoralD abstracts) | Moral‑intent preservation score (≥ 0.90 correlation) | https://huggingface.co/bert-base-uncased | `transformers` on‑the‑fly (CPU; GPU off‑load) | No external data download beyond the model weights (≈ 420 MB). |
| **Synthetic pilot data** | Synthetic dataset for power analysis and early testing | N/A (generated programmatically) | `pandas` | Guarantees a runnable pipeline before real data are collected. |

**Decision/Rationale**  
- **CPU‑first**: All heavy models (`clip-vit-base-patch32`, `bert-base-uncased`) are loaded on CPU; if the runner exceeds a 30‑second timeout, the same code runs on a Kaggle free GPU (automatic off‑load).  
- **Data Feasibility**: Visual Genome metadata streaming keeps RAM < 2 GB.  
- **Ambiguity Identification**: Human coding (FR‑008) creates the necessary morally ambiguous subset from an otherwise neutral image pool.  

## Methodological Approach

### Phase 0 – Pilot Power Analysis
1. Run a pilot with a modest number of participants and a comparable set of scenarios.  
2. Estimate variance of blame ratings and effect size (β).  
3. Compute required N for [deferred] power using `statsmodels.stats.power` (no external G*Power binary).  
4. **Assumptions** (see Power‑Analysis Addenda): 20 scenarios, 30 participants per scenario, ICC≈0.15 (participants) and 0.10 (scenarios), residual variance from pilot.  
5. If required N > 120, the study will be flagged as under‑powered (SC‑005).

### Phase 1 – Data Preparation & Salience Manipulation (FR‑001, FR‑008)

1. **Ingestion & Filtering** (`01_ingest_and_filter.py`)  
   - Stream Visual Genome metadata, keep rows where `objects` contain socially relevant tags (e.g., “person”, “vehicle”, “conflict”).  
   - Write `candidates_filtered.csv` with checksum.  

2. **Human Coding** (`02_human_coding.py`)  
   - Simulated crowd‑source (≥ 3 raters per image).  
   - Compute mean ambiguity and Cohen’s κ. Retain scenarios meeting **mean ≥ 3.5** and **κ ≥ 0.6**.  

3. **Stimulus Manipulation** (`03_manipulate_stimuli.py`)  
   - Detect a target ROI via simple edge detection (Sobel).  
   - Apply three contrast/brightness settings (low/medium/high).  
   - Validate each variant:  
     - **CLIP cosine similarity** ≥ 0.95.  
     - **RMS contrast change** ≥ 15 % in ROI.  
     - **Texture/edge density** change < 0.05.  
     - **Moral‑intent preservation** (BERT correlation) ≥ 0.90.  
     - **Pilot Human Manipulation Check**: ≥80 % of an independent coder panel confirms the moral narrative is unchanged.  
   - Store each image under `data/processed/stimuli/` and log to `stimuli_manifest.csv`.  

### Phase 2 – Survey Deployment (FR‑002, FR‑003)

- Generate a **Latin‑Square** schedule *plus* block‑wise counterbalancing and a brief wash‑out filler between salience levels to reduce carry‑over/fatigue.  
- Deploy a Flask mock‑survey for CI verification; production deployment can use Prolific.  
- Record `participant_id`, `variant_id`, `salience_level`, `blame_rating`, and timestamps in `responses_raw.csv`.  

### Phase 3 – Data Cleaning (FR‑007)

- Exclude participants with **variance < 0.1** or **> 90 % identical ratings**.  
- Flag and remove their rows, producing `responses_cleaned.csv` and `participants_excluded.csv`.  

### Phase 4 – Statistical Analysis (FR‑004, FR‑005, FR‑006)

1. **CLMM** (`statsmodels.miscmodels.ordinal_model.OrdinalModel`) with:  
   - Fixed effect: `salience_level` (ordered).  
   - Random intercepts: `Participant`, `Scenario`.  
2. **Convergence Check** – if not converged, switch to:  
   - **Robust LMM** (bootstrapped SEs) **OR**  
   - **Wilcoxon signed‑rank** tests for each pairwise contrast (Bonferroni corrected).  
3. **Multiple‑Comparison Correction** – Bonferroni for the three pairwise contrasts; Tukey‑adjusted p‑values when using CLMM.  
4. **Effect Sizes** – Odds ratios with 95 % CI for the main salience effect; marginal R² for LMM fallback.  
5. **Post‑hoc Power Analysis** – compute observed power; flag if < 0.80 (SC‑005).  

### Phase 5 – Reporting

- Assemble a markdown report (`report.md`) with:  
  - Stimulus integrity statistics (SC‑001).  
  - CLMM table (fixed effects, random effects, p‑values, odds ratios).  
  - Post‑hoc pairwise contrast table (Bonferroni‑adjusted).  
  - Exclusion rate (SC‑004).  
  - Confidence‑interval width vs. pre‑registered threshold (SC‑005).  
- All numbers trace back to a single row in `data/processed/` and a single code block, satisfying Principle IV.

## Edge Cases & Mitigations

| Edge Case | Mitigation |
|-----------|------------|
| **Manipulation Failure** (e.g., ROI detection fails) | Log to `manipulation_errors.log`; exclude scenario from `stimuli_manifest.csv`. |
| **Straight‑lining Participants** | Automatically excluded in `05_data_cleaning.py` per variance/identical‑rating rule. |
| **Low Sample Size** | Power analysis flag; report reduced power and wider CIs. |
| **CLMM Non‑Convergence** | Automatic fallback to robust LMM or Wilcoxon (FR‑005). |
| **GPU Needed for CLIP/BERT** | Scripts detect `torch.cuda.is_available()`; CI re‑runs on Kaggle GPU if needed. |

## Statistical Rigor Checklist
- **Multiple Comparisons**: Bonferroni (3 tests) + Tukey where appropriate.  
- **Power**: Pre‑study pilot + post‑hoc observed power; flag if < 0.80.  
- **Causal Claim**: Within‑subject experimental manipulation → causal inference justified.  
- **Measurement Validity**: CLIP similarity validated against human semantic check; BERT moral‑intent classifier fine‑tuned on MoralD abstracts (external validation).  
- **Collinearity**: Not applicable (salience levels are orthogonal manipulations).  

---


## Carry‑over Mitigation
- **Latin‑Square + block‑wise counterbalancing** ensures each salience level appears in each ordinal position equally across participants.  
- **Wash‑out filler**: a neutral 30‑second image (non‑moral, low salience) is presented between salience levels of the same scenario.  
- **Breaks**: after every 10 trials, a short break screen appears to reduce fatigue.

---


## Troubleshooting
- **Memory errors**: Reduce `--max-scenarios` or sample a smaller pilot (`--num-samples`).  
- **CLIP/BERT timeout**: Set `--device cpu` to force CPU; the next CI run will automatically switch to Kaggle GPU.  
- **Convergence warnings**: Check `analysis_results.json` for `fallback_method`; the script will have already applied the robust alternative.

## Quick Reference Checklist
- **Stimulus Integrity**: `stimuli_manifest.csv` validates against `contracts/stimulus.schema.yaml`.  
- **Response Schema**: `responses_cleaned.csv` validates against `contracts/response.schema.yaml`.  
- **Analysis Output**: `analysis_results.json` validates against `contracts/analysis_schema.yaml`.  

If any validation fails, re‑run the corresponding step; the scripts emit detailed logs.
