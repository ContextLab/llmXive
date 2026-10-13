# Implementation Plan: Visual Detail and False Memory Susceptibility

**Branch**: `001-visual-detail-false-memory` | **Date**: 2026-10-13 | **Spec**: `specs/001-the-impact-of-visual-detail-on-false-mem/spec.md`  
**Input**: Feature specification from `specs/001-the-impact-of-visual-detail-on-false-mem/spec.md`

## Summary
The project will implement a **Repeated‑Measures (Within‑Subjects) design** to test how visual detail manipulation (enhanced vs. reduced vs. baseline) influences false‑memory susceptibility. Each participant will view the **same baseline image** under three detail conditions (baseline, enhanced, reduced) presented in a **Latin‑square counterbalanced** order. After each view, a brief arithmetic distractor task is run, followed by a recognition questionnaire containing **20 true items and Several lure items per condition**. The primary outcome is the **false‑memory rate** (proportion of “Yes” responses to lure items) per condition. This pipeline consists of four tightly coupled phases that map directly to every functional requirement (FR‑001 – FR‑008) and success criterion (SC‑001 – SC‑005).

| Phase | Covered FRs | Covered SCs | Core Tasks |
|-------|--------------|-------------|------------|
| **0 – Data Acquisition & Power Analysis** | FR‑001, FR‑008 | SC‑004, **SC‑002** (Power analysis) | Download (or load pre‑bundled) Visual Genome images, compute baseline complexity scores, write per‑image metadata files, run `code/analysis/power.py` to confirm ≥ 50 complete sessions needed. |
| **1 – Stimulus Manipulation** | FR‑002, FR‑008 | – | Generate enhanced and reduced versions **of each baseline image** via PIL compositing, log errors to `data/logs/manipulation_errors.log`, produce `metadata.yaml` files. |
| **2 – Participant Testing Interface** | FR‑003, FR‑004, **FR‑004 (contract validation)** | SC‑001, **SC‑002** | Serve each baseline image for **10 ± 0.5 s**, run a **2‑min arithmetic distractor**, present a **balanced set of 20 true and 20 lure items per condition** (total 40 per condition), capture timestamped responses, validate each response against `contracts/response.schema.yaml`, and record Latin‑square counterbalanced condition order as a covariate. |
| **3 – Statistical Analysis & Visualization** | FR‑005, FR‑006, **FR‑007**, FR‑007 | SC‑001, SC‑003, SC‑005, **SC‑002** | Compute per‑condition false‑memory rates, fit a **Generalized Linear Mixed‑Effects Model (binomial logit)** with participant random intercepts, apply Bonferroni correction for the three pairwise contrasts, and generate CI plots. |

All phases are scripted, deterministic, and fully automatable on a GitHub Actions free‑tier runner (a modest number of CPU cores, ≈ 7 GB RAM, ≈ 14 GB disk). No GPU is required.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `datasets==2.19.0`, `Pillow==10.2.0`, `pandas==2.2.2`, `scipy==1.13.0`, `matplotlib==3.8.4`, `statsmodels==0.14.2`, `pytest==8.2.2`
- **Storage**: Local filesystem under `data/` (stimuli, responses, analysis)
- **Testing**: `pytest` with unit tests for image manipulation, integration tests for end‑to‑end flow
- **Target Platform**: Linux (GitHub Actions runner)
- **Performance Goals**: Entire pipeline < 6 h; image manipulation ≤ 5 s/image; analysis ≤ 10 min for 60 participants
- **Constraints**: CPU‑only, ≤ 7 GB RAM, ≤ 14 GB disk, reproducible random seeds, no external API calls at runtime
- **Scale/Scope**: Minimum 30 baseline images (required for validation); target ≥ 50 complete participant sessions for statistical power

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|--------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/config.py`; `requirements.txt` version‑locked; pre‑bundled image subset guarantees identical CI runs. |
| **II. Verified Accuracy** | PASS | All citations will be validated by the Reference‑Validator; no fabricated URLs are used. |
| **III. Data Hygiene** | PASS | Checksums recorded for every generated file; transformations create new files; no PII is committed. |
| **IV. Single Source of Truth** | PASS | Figures and statistics are generated directly from `data/` via scripts; no manual transcription. |
| **V. Versioning Discipline** | PASS | Content‑hashes stored in `state/projects/PROJ-317-…yaml`; any change updates `updated_at`. |
| **VI. Human Subjects Ethics** | PASS (conditional) | `data/ethics/` contains `informed_consent.md`; IRB approval is a manual gate before real data collection; CI uses mock participants, so no IRB needed for validation. |
| **VII. Stimulus Standardization** | PASS | All stimulus images and accompanying `metadata.yaml` files are stored under `data/stimuli/`; script version is archived and referenced in any analysis notebook to ensure reproducibility. |

## Project Structure

### Documentation (this feature)
```text
specs/001-the-impact-of-visual-detail-on-false-mem/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── response.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

### Source Code (repository root)
```text
projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/
├── code/
│   ├── __init__.py
│   ├── config.py                # seeds, paths, constants
│   ├── stimuli/
│   │   ├── generator.py         # enhanced & reduced compositing (T015)
│   │   └── metadata.py          # writes `metadata.yaml` (T017)
│   ├── participants/
│   │   ├── interface.py         # web‑free UI simulation (T027)
│   │   └── response.py          # dataclass + validation (uses response.schema.yaml)
│   ├── analysis/
│   │   ├── power.py             # a priori power calc (SC‑002)
│   │   ├── glmm.py              # GLMM (binomial) analysis (replaces ANOVA)
│   │   └── viz.py               # CI plot generation (FR‑007)
│   └── utils/
│       ├── data_loader.py       # loads pre‑bundled subset or streams full Visual Genome
│       └── ethics.py            # consent handling, anonymization (VI)
├── data/
│   ├── stimuli/
│   │   ├── raw_subset/          # Several verified images (CI)
│   │   └── generated/           # enhanced / reduced + metadata
│   ├── responses/
│   ├── analysis/
│   └── ethics/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt
```

## Mapping of Functional Requirements & Success Criteria
| ID | Requirement / Criterion | Plan Element (Phase / Task) |
|----|--------------------------|-----------------------------|
| FR‑001 | System MUST download a representative Visual Genome sample spanning ≥3 quantile bins | Phase 0 – `data_loader.py` (sampling by `complexity_score`) |
| FR‑002 | Create enhanced & reduced versions per image | Phase 1 – `generator.py` |
| FR‑003 | Display baseline image for 10 ± 0.5 s before distractor | Phase 2 – `interface.py` timing logic |
| FR‑004 | Balanced true & lure recognition questions (20 each per condition) | Phase 2 – `interface.py` question generator |
| FR‑005 | Execute repeated‑measures analysis (now GLMM binomial) | Phase 3 – `glmm.py` |
| FR‑006 | Apply multiple‑comparison correction when >1 test | Phase 3 – `glmm.py` (Bonferroni) |
| FR‑007 | Generate visualization showing mean false memory rates with confidence intervals | Phase 3 – `viz.py` |
| FR‑008 | Store stimulus metadata per image | Phase 0/1 – `metadata.py` |
| SC‑001 | Measure false‑memory rate per condition | Phase 3 – compute rates from `responses/` |
| SC‑002 | Power analysis ≥ 50 complete sessions to detect effects at α = 0.05 | Phase 0 – `power.py` (gate before real data) |
| SC‑003 | Runtime within GitHub Actions limits | Entire pipeline – CPU‑first, time estimates recorded |
| SC‑004 | Dataset‑variable fit against Visual Genome metadata | Phase 0 – validation step in `data_loader.py` |
| SC‑005 | Multiple‑comparison correction measured against #tests | Phase 3 – explicit logging of correction method |

## Task Outline (high‑level, 12 tasks)
1. **T000 – Design Confirmation** – Update design to *Repeated‑Measures (Within‑Subjects)* and replace all “Between‑Subjects” references. *(this plan fulfills the requirement)*
2. **T001 – Data Loader** – Implement `data_loader.py` to stream Visual Genome (or use pre‑bundled subset) and compute `complexity_score`.
3. **T002 – Complexity Binning** – Verify ≥3 quantile bins (Q1‑Q3) with spread ≥0.3.
4. **T003 – Stimulus Generator** – Add objects for enhanced condition; blur/remove for reduced condition; log errors to `data/logs/manipulation_errors.log`.
5. **T004 – Metadata Writer** – Write `metadata.yaml` for each stimulus (enhanced & reduced).
6. **T005 – Participant Interface** – Serve each baseline image for 10 ± 0.5 s, run 2‑min distractor, present a **balanced set of 20 true and 20 lure items per condition**, capture timestamps, validate against `contracts/response.schema.yaml`, and record Latin‑square counterbalanced condition order as a covariate.
7. **T006 – Response Validator** – Enforce schema (`contracts/response.schema.yaml`).
8. **T007 – Power Analysis** – Compute required N; abort real data collection if N < 50; include sensitivity analysis for effect sizes f = 0.20, 0.25, 0.30.
9. **T008 – GLMM (Binomial) Analysis** – Use `statsmodels` to fit a mixed‑effects logistic model with participant random intercepts; check assumptions; report partial η² and Cohen’s d for pairwise contrasts.
10. **T009 – Multiple‑Comparison Correction** – Apply Bonferroni to the three pairwise contrasts.
11. **T010 – Visualization** – Plot mean false‑memory rates with 95 % CIs per condition.
12. **T011 – Logging & Checksums** – Generate SHA‑256 checksums for all outputs; store in `state/...yaml`.

Each task will produce unit tests under `tests/` and will be gated by the relevant success criteria.

--- 

## projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/specs/001-the-impact-of-visual-detail-on-false-mem/research.md===
# Research: Visual Detail and False Memory Susceptibility

## Summary
This study examines whether **visual detail** (enhanced vs. reduced vs. baseline) modulates **false‑memory susceptibility** using a **Repeated‑Measures (Within‑Subjects) design**. Participants view all three stimulus conditions for the **same underlying scene** in a **Latin‑square counterbalanced** order, complete a brief arithmetic distractor, and answer a recognition questionnaire containing **20 true items and 20 lure items per condition**. The primary outcome is the **false‑memory rate** (proportion of “Yes” responses to lure items) per condition.

## Theoretical Framework
- **Misinformation Effect** (Loftus et al.) demonstrates that post‑event information can alter memory. Here we test a *pre‑event* manipulation: visual detail.
- **Constructive Memory** (Bartlett) predicts that gaps are filled with plausible details; richer visual scenes may either **(a)** increase cognitive load → more lures accepted, or **(b)** provide more distinctive cues → fewer lures. The direction is exploratory.
- **Hypothesis**: Visual detail will **significantly affect** false‑memory rates across conditions.

## Dataset Strategy
The verified datasets block contains only a math parquet file, which is **not applicable**. Therefore:

| Dataset | Source | Availability | Variable Fit |
|---------|--------|--------------|--------------|
| **Visual Genome (Pre‑bundled subset)** | `data/stimuli/raw_subset/` (30 curated images) | **Verified** by content hash, shipped with repo | Provides scene images, object annotations, and can be used to compute `complexity_score`. |
| **Visual Genome (Full)** | `datasets.load_dataset("visual_genome")` | **Pending verification** – not listed in verified block. The pipeline includes a switch (`--source visual_genome`) for the final study once verification is obtained. | Same variables as above; streaming mode will be used to stay within memory limits. |

*Data‑Variable Fit*: The subset includes `image_id`, object lists, and resolution metadata; we compute a derived `complexity_score` (edge density + object count) to satisfy FR‑001. The outcome variable (false‑memory rate) is derived from participant responses, satisfying SC‑001.

**Data Availability Plan**  
- CI runs use the pre‑bundled subset (no external download).  
- For the full study, we will stream Visual Genome (`streaming=True`) and sample a limited subset of images to stay within the allocated RAM budget.  
- All image files are stored under `data/stimuli/`; checksums recorded in `state/...yaml`.

## Statistical Methodology
- **Design**: Repeated‑Measures (Within‑Subjects) with *condition* (enhanced, reduced, baseline) as the within‑subject factor. Condition order is **Latin‑square counterbalanced** across participants and recorded as a covariate.
- **Model**: **Generalized Linear Mixed‑Effects Model (GLMM)** with a binomial (logit) link to model the binary lure responses. Implemented via `statsmodels` (`statsmodels.genmod.bayes_mixed_glm.BinomialBayesMixedGLM` or equivalent). Participant IDs are included as random intercepts; condition order is added as a fixed‑effect covariate to control for fatigue/learning.
- **Assumption Checks**:  
  - **Overdispersion**: Examine Pearson residuals.  
  - **Random‑effects adequacy**: Compare models with vs. without random intercepts via likelihood ratio test.  
- **Multiple‑Comparison**: Bonferroni correction for the three pairwise contrasts (enhanced vs baseline, reduced vs baseline, enhanced vs reduced).
- **Power Analysis** (SC‑002):  
  - **Effect size justification**: Prior visual‑memory work (Brady et al., 2022) reported a medium effect (f ≈ 0.25) for detail‑related memory differences; we adopt this as a baseline.  
  - **Sensitivity analysis**: `code/analysis/power.py` computes required N for effect sizes f = 0.20, 0.25, 0.30 (see Table 1). For f = 0.25, α = 0.05, power = 0.80 → **N ≈ 50** participants. The script will abort real data collection if the projected N falls below 50.  
- **Effect Size Reporting**: Report odds ratios and marginal R² for the GLMM, and Cohen’s d for pairwise log‑odds contrasts.  
- **Measurement Validity**: Recognition items follow the paradigm of Loftus & Palmer (1974); lures are generated via a “Semantic Absence” algorithm that selects objects present in the same scene category but absent from the target image.  

All statistical steps are performed with **CPU‑only** libraries (`statsmodels`, `scipy`, `matplotlib`).

## Compute Feasibility
- **CPU‑First**: All image compositing (PIL), data loading (datasets streaming), and statistical analysis run on the GitHub Actions free tier.  
- **Memory**: Streaming ensures < 5 GB RAM even with full Visual Genome.  
- **Disk**: Pre‑bundled subset ≈ a moderate size on the order of tens of megabytes; full streamed images processed on‑the‑fly, final outputs < 200 MB.  
- **Runtime**: Estimated < 6 h total; analysis < 10 min for 60 participants.  

## Ethics & Compliance
- **IRB**: No real participants are recruited in CI; a manual IRB approval checkpoint (`data/ethics/irb_approval.txt`) must be satisfied before any `--mode real` run.  
- **Consent**: `data/ethics/informed_consent.md` contains a GDPR‑compliant consent script; participants must click “I Agree” before the first stimulus.  
- **Anonymization**: Participant IDs are generated as pseudonyms (`P-001`, …) and stored separately from any IP logs.  
- **Data Security**: All files under `data/` are checksummed; no PII is ever written to the repository.  

--- 

## projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/specs/001-the-impact-of-visual-detail-on-false-mem/data-model.md===
# Data Model: Visual Detail and False Memory Susceptibility

## Entities

### Stimulus (Image)
| Field | Type | Description |
|-------|------|-------------|
| `image_id` | `string` (UUID) | Unique identifier for the baseline image. |
| `baseline_path` | `string` | Relative path to the original image file. |
| `enhanced_path` | `string` | Path to the enhanced‑detail version. |
| `reduced_path` | `string` | Path to the reduced‑detail version. |
| `complexity_score` | `number` (0 – 1) | Derived metric (edge density + object count). |
| `manipulation_params` | `object` | JSON with `objects_added`, `objects_removed`, `blur_radius`, etc. |
| `created_at` | `string` (ISO‑8601) | Timestamp of generation. |
| `script_version` | `string` | Git commit hash of the generator script. |
| `checksum` | `string` (SHA‑256) | File‑level checksum for reproducibility. |

*Note*: The `enhanced_path` and `reduced_path` **share the same `image_id`** as the baseline; participants will see all three versions of the *same underlying scene* across conditions, preserving within‑subject comparability.

### Participant
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | `string` (pattern `^P-\d{3}$`) | Pseudonymous identifier. |
| `condition_order` | `array[string]` | Latin‑square randomized sequence of the three stimulus conditions. |
| `consent_verified` | `boolean` | True if consent was recorded. |
| `completion_timestamp` | `string` (ISO‑8601) | End‑of‑session time. |
| `status` | `string` (`complete`, `partial`, `dropped`) | Session outcome flag. |

### Response
| Field | Type | Description |
|-------|------|-------------|
| `response_id` | `string` (UUID) | Unique response identifier. |
| `participant_id` | `string` | FK → Participant. |
| `question_id` | `string` | Identifier for the recognition item (e.g., Q_001). |
| `condition` | `string` (`enhanced`, `reduced`, `baseline`) | Stimulus condition for this question. |
| `is_false_detail` | `boolean` | True if the item is a lure. |
| `lure_source_query` | `string` | Query used to generate the lure (e.g., “objects in kitchen not in image”). |
| `response_value` | `boolean` | Participant answered “Yes”. |
| `response_timestamp` | `string` (ISO‑8601) | When the answer was recorded. |
| `latency_ms` | `integer` | Time taken to answer, in milliseconds. |
| `semantic_plausibility` | `number` (0 – 1) | WordNet‑based plausibility score for the lure (0 = implausible, 1 = highly plausible). |
| `trial_type` | `string` (`true`, `lure`) | Indicates whether the question referred to a true detail or a false/lure detail (ensures balanced 20/20 per condition). |

## Data Flow
1. **Acquisition** – `data_loader.py` streams Visual Genome (or loads pre‑bundled subset) → `Stimulus` records stored in `data/stimuli/`.  
2. **Manipulation** – `generator.py` creates enhanced/reduced images, writes `metadata.yaml` per stimulus.  
3. **Collection** – `interface.py` runs the participant session, writes `Response` rows to `data/responses/{participant_id}.jsonl`.  
4. **Analysis** – `glmm.py` aggregates responses per condition, fits a binomial GLMM, outputs `data/analysis/glmm_results.json` and `results.png`.  

## Constraints
- **No PII** in any file under `data/responses/`.  
- **Uniqueness**: `image_id` and `response_id` must be globally unique.  
- **Integrity**: Every `response` must reference an existing `participant_id` and a valid `question_id` derived from the associated stimulus.  
- **Versioning**: All generated files include a SHA‑256 checksum recorded in the project state YAML.  

--- 

## projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/specs/001-the-impact-of-visual-detail-on-false-mem/quickstart.md===
# Quickstart: Visual Detail and False Memory Susceptibility

## Prerequisites
- Python 3.11 or newer
- `git`
- Internet connection (only for optional full Visual Genome download)

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-317-the-impact-of-false-mem

# Set up a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Running the CI Validation Pipeline (uses pre‑bundled subset)
```bash
# 1. Load the pre‑bundled images and compute complexity scores
python code/utils/data_loader.py --source prebundled --count <desired_number> --seed 42

# 2. Generate enhanced and reduced stimuli (writes metadata files)
python code/stimuli/generator.py --mode all --seed 42

# 3. Simulate multiple participant sessions (mock mode, no IRB needed)
#    Each session presents **20 true items and 20 lure items per condition**.
python code/participants/interface.py --mode mock --n-sessions 60 --seed 123

# 4. Power analysis (will pass because N = 60 ≥ 50)
python code/analysis/power.py

# 5. Run GLMM analysis and produce the plot
python code/analysis/glmm.py
python code/analysis/viz.py --output data/analysis/false_memory_rates.png
```

## Running the Full Study (requires verified Visual Genome)
1. **Verify Visual Genome** – Add the dataset to the verified list or obtain an explicit verification token.  
2. **Download & Stream**  
```bash
python code/utils/data_loader.py --source visual_genome --limit 5000 --stream
```
3. **Collect Real Data** (after IRB approval)  
```bash
python code/participants/interface.py --mode real --n-sessions 60
```
4. **Analyze** – same commands as step 5 above.

## Verification Checklist
- `data/stimuli/generated/` contains `*_enhanced.jpg`, `*_reduced.jpg`, and matching `metadata.yaml` files.  
- `data/responses/` holds one JSONL file per participant; each line conforms to `contracts/response.schema.yaml`.  
- `data/analysis/false_memory_rates.png` displays mean false‑memory rates with 95 % confidence intervals for the three conditions.  
- SHA‑256 checksums for all outputs are recorded in `state/projects/PROJ-317-…yaml`.  

--- 

## projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/specs/001-the-impact-of-visual-detail-on-false-mem/contracts/response.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "Participant Response Schema"
description: "Schema for individual response records collected during the experiment (FR-004)."
type: "object"
required:
  - "response_id"
  - "participant_id"
  - "question_id"
  - "condition"
  - "is_false_detail"
  - "lure_source_query"
  - "response_value"
  - "response_timestamp"
properties:
  response_id:
    type: "string"
    description: "Unique UUID for the response."
  participant_id:
    type: "string"
    pattern: "^P-\\d{3}$"
    description: "Pseudonymous participant identifier."
  question_id:
    type: "string"
    description: "Identifier for the recognition question (e.g., Q_001)."
  condition:
    type: "string"
    enum: ["enhanced", "reduced", "baseline"]
    description: "Stimulus condition to which this response belongs."
  is_false_detail:
    type: "boolean"
    description: "True if the question refers to a lure (false detail)."
  lure_source_query:
    type: "string"
    description: "Query used to generate the lure (e.g., 'objects in kitchen not in image')."
  response_value:
    type: "boolean"
    description: "Participant answered 'Yes, I saw this'."
  response_timestamp:
    type: "string"
    format: "date-time"
    description: "ISO‑8601 timestamp of the response."
  latency_ms:
    type: "integer"
    minimum: 0
    description: "Time taken to answer, in milliseconds."
  semantic_plausibility:
    type: "number"
    minimum: 0.0
    maximum: 1.0
    description: "WordNet‑based plausibility score for the lure (0 = implausible, 1 = highly plausible)."
additionalProperties: false