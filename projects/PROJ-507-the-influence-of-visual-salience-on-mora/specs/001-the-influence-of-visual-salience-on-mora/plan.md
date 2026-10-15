# Implementation Plan: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Branch**: `001-visual-salience-moral-judgments` | **Date**: 2024-10-15 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-visual-salience-moral-judgments/spec.md`

## Summary
The pipeline builds a reproducible experimental dataset, manipulates visual salience, deploys a within‑subject survey, and analyzes blame ratings with a Cumulative Link Mixed Model (CLMM). All steps are tied to the functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑005). The plan uses only **open, human‑centric visual datasets** (Visual Genome) and runs on CPU‑first GitHub Actions; any heavy embedding work (CLIP, BERT) is off‑loaded to a free Kaggle GPU when needed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pillow`, `pandas`, `numpy`, `datasets`, `torch`, `transformers`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `pyyaml`  
- **Storage**: Local file system under `data/` (raw, processed, checksums)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≈7 GB RAM) – GPU off‑load via Kaggle if `torch.cuda.is_available()` is False on the runner.  
- **Constraints**: ≤7 GB RAM, ≤14 GB disk, no permanent GPU; all random seeds pinned.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | All scripts are deterministic (seeded RNGs), external datasets fetched from canonical URLs, `requirements.txt` pins versions. |
| II. Verified Accuracy | Only URLs listed in the “Verified datasets” block are cited (none for Visual Genome; flagged for spec amendment). |
| III. Data Hygiene | Raw files checksummed (`data/checksums.txt`); every transformation writes a new file with a derivation log. |
| IV. Single Source of Truth | Every figure/table references a single row in `data/processed/` and a single code block in `code/`. |
| V. Versioning Discipline | Content hashes recorded in `state/projects/…yaml`; any change updates the timestamp. |
| VI. Stimulus‑Control Integrity | Manipulation parameters versioned in `config/manipulation.yaml`; CLIP similarity ≥ 0.95, RMS contrast ≥ 15 % enforced by `contracts/stimulus.schema.yaml`. |
| VII. Behavioral Response Validation | Survey responses link `participant_id`, `variant_id`, and `blame_rating` per `contracts/response.schema.yaml`. |

## Project Structure
```
specs/001-visual-salience-moral-judgments/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── stimulus.schema.yaml
│   └── response.schema.yaml
└── tasks.md            # created later by /speckit-tasks
```

```
projects/PROJ-507-the-influence-of-visual-salience-on-mora/
├── data/
│   ├── raw/                     # streamed downloads (e.g., Visual Genome)
│   ├── processed/               # filtered scenarios, stimuli, survey data
│   └── checksums.txt
├── code/
│   ├── 00_pilot_power_analysis.py
│   ├── 01_ingest_and_filter.py          # FR‑001, FR‑008 (now uses Visual Genome)
│   ├── 02_human_coding.py               # FR‑008
│   ├── 03_manipulate_stimuli.py         # FR‑001
│   ├── 04_survey_deployment.py          # FR‑002, FR‑003
│   ├── 05_data_cleaning.py              # FR‑007
│   ├── 06_analysis_clmm.py              # FR‑004, FR‑005, FR‑006
│   └── requirements.txt
├── config/
│   ├── pilot.yaml
│   ├── human_coding.yaml
│   ├── manipulation.yaml
│   ├── analysis.yaml
│   └── pre_registration.yaml
└── docs/
    └── constitution.md
```

## Phase & Task Mapping (covers all FRs & SCs)

| Phase | Tasks (script) | FR / SC addressed | Notes |
|-------|----------------|-------------------|-------|
| **Phase 0 – Pilot Power Analysis** | `00_pilot_power_analysis.py` | FR‑004 (sample‑size awareness), SC‑005 (precision) | **Power‑Analysis Details**: Assumes **20 scenarios** (minimum to capture diverse moral contexts) and **30 participants per scenario** (total N = 600). Expected intra‑class correlation (ICC) ≈ 0.15 for participants and ≈ 0.10 for scenarios (based on prior moral‑judgment work). Detects a **medium effect** (β ≈ 0.5) with ≥80 % power using `statsmodels.stats.power` (CPU‑only). Generates `pilot_power.json`. |
| **Phase 1 – Data Preparation & Salience Manipulation** | `01_ingest_and_filter.py` | FR‑001, FR‑008, SC‑001 | Streams **Visual Genome** via `datasets.load_dataset("visual_genome", split="train", streaming=True)`. Filters rows where `objects` contain socially relevant tags (e.g., “person”, “vehicle”, “conflict”). Writes `candidates_filtered.csv`. |
| | `02_human_coding.py` | FR‑008, SC‑001 | Simulated crowd‑source (≥3 raters per image). Calculates mean ambiguity and Cohen’s κ; retains rows with mean ≥ 3.5 & κ ≥ 0.6. |
| | `03_manipulate_stimuli.py` | FR‑001, SC‑001, VI (Stimulus‑Control) | For each retained scenario, creates low/medium/high variants by adjusting contrast/brightness in a bounding‑box ROI (detected via edge‑based mask). Validates each variant: <ul><li>**CLIP cosine similarity** ≥ 0.95.</li><li>**RMS contrast change** ≥ 15 % in ROI.</li><li>**Texture/edge density** change < 0.05.</li><li>**Moral‑intent preservation** (BERT correlation) ≥ 0.90.</li><li>**Pilot Human Manipulation Check**: ≥80 % of independent coders confirm the moral narrative is unchanged.</li></ul> Stores images under `data/processed/stimuli/` and logs to `stimuli_manifest.csv`. |
| **Phase 2 – Survey Deployment & Data Collection** | `04_survey_deployment.py` | FR‑002, FR‑003, SC‑004 | Generates a **Latin‑Square** schedule *plus* block‑wise counterbalancing and a brief wash‑out filler between salience levels to reduce carry‑over/fatigue. Deploys a Flask mock‑survey for CI testing; production can use Prolific. Records `participant_id`, `variant_id`, `salience_level`, `blame_rating`, timestamps in `responses_raw.csv`. |
| **Phase 3 – Data Cleaning** | `05_data_cleaning.py` | FR‑007, SC‑004 | Excludes participants with **variance < 0.1** or **> 90 % identical ratings**. Flags and removes their rows, producing `responses_cleaned.csv` and `participants_excluded.csv`. |
| **Phase 4 – Statistical Analysis & Reporting** | `06_analysis_clmm.py` | FR‑004, FR‑005, FR‑006, SC‑002, SC‑003, SC‑005 | Fits CLMM (`statsmodels.miscmodels.ordinal_model.OrdinalModel`) with:  <ul><li>**Fixed effect** `salience_level` (ordered).</li><li>**Random intercepts** `Participant`, `Scenario`.</li></ul> **Convergence Check** – if not converged, falls back to robust LMM (bootstrapped SEs) **or** Wilcoxon signed‑rank tests for each pairwise contrast (Bonferroni corrected). **Multiple‑Comparison Correction** – Bonferroni for the three pairwise contrasts; Tukey‑adjusted p‑values when using CLMM. **Effect Sizes** – Odds ratios with 95 % CI for the main salience effect; marginal R² for LMM fallback. **Post‑hoc Power Analysis** – computes observed power using the estimated effect size; flags if < 0.80. Writes `analysis_results.json` validated against `contracts/analysis_schema.yaml`. |
| **Phase 5 – Reporting** | `06_analysis_clmm.py` (output) | SC‑002, SC‑003 | Generates `report.md` with stimulus integrity stats (SC‑001), CLMM table, post‑hoc contrast table, exclusion rate (SC‑004), confidence‑interval width vs. pre‑registered threshold (SC‑005). All numbers trace back to a single row in `data/processed/` and a single code block, satisfying Principle IV. |

All phases are ordered so that data is downloaded before any consumption, models are fitted before evaluation, and figures are generated before being referenced in the report.

---


## Methodological Rigor Addenda

### Construct‑Validity of Salience Manipulation
In addition to automated semantic checks (CLIP, BERT), we conduct a **pilot human manipulation validation**:
1. A separate coder panel (n = 15) views each low/medium/high variant and answers “Does the moral narrative of the scene remain the same?” (Yes/No).  
2. ≥80 % “Yes” responses are required for a variant to pass.  
3. Variants failing this check are excluded from the stimulus set.

### Power‑Analysis Assumptions (Phase 0)
- **Number of scenarios**: 20 (minimum to capture diverse moral contexts).  
- **Participants per scenario**: 30 (within‑subject, each sees all three salience levels).  
- **Intra‑class correlation (ICC)**: 0.15 for participants, 0.10 for scenarios (based on prior moral‑judgment studies).  
- **Residual variance**: estimated from pilot data.  
These values feed into the `statsmodels.stats.power` calculation to ensure ≥80 % power for detecting a medium effect (β ≈ 0.5) in the CLMM.

### Carry‑over & Fatigue Mitigation (Phase 2)
- **Latin‑Square + block‑wise counterbalancing** ensures each salience level appears in each ordinal position equally across participants.  
- **Wash‑out filler**: a neutral 30‑second image (non‑moral, low salience) is presented between salience levels of the same scenario.  
- **Breaks**: after every 10 trials, a short break screen appears to reduce fatigue.

---


## Compute Feasibility
- **CPU‑first**: All scripts run on the GitHub Actions runner; heavy model embeddings (CLIP, BERT) are loaded on CPU. If a script exceeds a 30‑second timeout, the CI system automatically re‑runs the same command on a free Kaggle GPU (GPU off‑load). No fabricated CPU approximations are used.
- **Memory**: Streaming the Visual Genome metadata (~2 GB) keeps RAM < 2 GB. Image processing is done per‑batch to stay within the 7 GB limit.

---


## Edge Cases & Mitigations
| Edge Case | Mitigation |
|-----------|------------|
| **Manipulation Failure** (e.g., ROI detection fails) | Log to `manipulation_errors.log`; exclude scenario from `stimuli_manifest.csv`. |
| **Straight‑lining Participants** | Automatically excluded in `05_data_cleaning.py` per variance/identical‑rating rule. |
| **Low Sample Size** | Power analysis flag; report reduced power and wider CIs. |
| **CLMM Non‑Convergence** | Automatic fallback to robust LMM or Wilcoxon (FR‑005). |
| **GPU Needed for CLIP/BERT** | Scripts detect `torch.cuda.is_available()`; CI re‑runs on Kaggle GPU if needed. |
