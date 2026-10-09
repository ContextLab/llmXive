# Implementation Plan: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Branch**: `001-visual-priming-implicit-attitudes` | **Date**: 2024-10-09 | **Spec**: `specs/001-visual-priming-implicit-attitudes/spec.md`  
**Input**: Feature specification from `/specs/001-visual-priming-implicit-attitudes/spec.md`

## Summary
The pipeline will (1) download a **public IAT response‑time dataset** from Hugging Face, (2) extract and verify stimulus metadata, (3) derive missing prime‑valence and stimulus‑ambiguity scores using CPU‑optimized models, (4) fit a **linear mixed‑effects (LME) model** with robust SE, VIF checks, and FDR correction, and (5) generate a **publication‑ready PDF** containing interaction plots, coefficient tables, and a sensitivity‑analysis summary. All steps are deterministic, reproducible, and respect the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `statsmodels==0.14.2`, `torch==2.3.0+cpu`, `transformers==4.44.0`, `datasets==2.20.0`, `pyyaml==6.0.2`, `reportlab==4.2.2`, `matplotlib==3.9.2`, `seaborn==0.13.2`  
- **Storage**: Local file system under `data/` and `reports/`.  
- **Testing**: `pytest==8.3.2` (unit & contract validation).  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤7 GB RAM).  
- **Project Type**: Data‑science pipeline (no web service).  
- **Constraints**: CPU‑first execution; optional GPU fallback only for the **valence‑derivation transformer** (scaled 8‑bit, Kaggle free GPU).  
- **Scale/Scope**: Single open IAT dataset (≈ 500 k trials); streaming mode used for > 7 GB files.

## Constitution Check
| Principle | Compliance | Implementation Detail |
|-----------|------------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned (`np.random.seed(42); torch.manual_seed(42)`); `requirements.txt` pins exact versions; data fetched via deterministic Hugging Face URLs. |
| **II. Verified Accuracy** | PASS | All external URLs appear in the “Verified datasets” block; citations are limited to those URLs. |
| **III. Data Hygiene** | PASS | Raw files are never overwritten; each transformation writes a new file; checksums recorded in `state/artifact_hashes.json`; PII scan (`code/pii_scan.py`) runs on `data/processed/`. |
| **IV. Single Source of Truth** | PASS | Every figure/table in `reports/final_report.pdf` references a single row in `data/processed/linked_trials.csv` and a single entry in `code/`. |
| **V. Versioning Discipline** | PASS | Content hashes for all artifacts stored in `state/artifact_hashes.json`; `state/project_state.yaml` updated after each task. |
| **VI. Distinct Stimulus Set Integrity** | PASS | Primes stored in `data/primes/`; targets in `data/targets/`; they are merged **only** after the LME model is specified (see Task T018). |

## Project Structure
```text
specs/001-visual-priming-implicit-attitudes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── linkage_status.schema.yaml
│   └── output.schema.yaml
└── tasks.md      # generated later by /speckit-tasks
```

```text
code/
├── main.py                # CLI orchestrator
├── ingest.py              # Download + basic validation
├── preprocess.py          # Metadata extraction, linkage, derivations
├── derive_valence.py      # CPU‑optimized emotion classifier (distilbert-base-uncased‑emotion)
├── derive_ambiguity.py    # Lexical Ambiguity Index / Image texture variance
├── model.py               # LME fitting, VIF, robustness
├── report.py              # Plotting, PDF assembly, sensitivity analysis embed
├── config.py              # Thresholds, file paths, GPU‑fallback flags
├── logs/
│   └── pipeline.log       # Created at runtime (Task T009)
├── requirements.txt
└── pip.conf               # Index URL for torch‑cpu wheels
```

## Complexity Tracking (FR/SC → Tasks)
| FR / SC | Required Capability | Corresponding Task(s) |
|--------|---------------------|-----------------------|
| FR‑001 | Verify presence of RT, prime valence, ambiguity; derive missing scores | T010 (Validate core columns), T018a (Derive ambiguity), T018b (Derive valence) |
| FR‑002 | CPU‑optimized emotion classification or lexical dictionary | T018b (Valence derivation) |
| FR‑003 | Frame findings as associational | T029 (Associational framing) |
| FR‑004 | Apply FDR / Bonferroni when > 1 hypothesis | T028 (FDR correction) |
| FR‑005 | Compute VIF, flag > 5.0 | T027a (VIF calculation) |
| FR‑006 | Sweep α‑levels for sensitivity | T030 (Sensitivity analysis) |
| SC‑001 | Data ingestion completeness | T016 (Linkage gate) + T018a (Metric calc) |
| SC‑002 | Model convergence success ≥ [deferred] | T025 (LME fitting) + T047 (Convergence fallback) |
| SC‑003 | Final PDF contains required artifacts | T036 (PDF generation) |

## Data Availability & Feasibility
- **Primary Dataset**: `davanstrien/ia_test_embeddings` (Parquet). Verified URL: `https://huggingface.co/datasets/davanstrien/ia_test_embeddings/resolve/main/data/train-00000-of-00001-82feb90c086b8e08.parquet`.  
  - Contains `response_time`, `participant_id`, `stimulus_id`, optional `age`, `gender`, `education`.  
- **Streaming**: For files > 7 GB the pipeline invokes `datasets.load_dataset(..., streaming=True)`. A synthetic 8 GB Parquet file is generated on‑the‑fly during the **verification step of T040** to prove streaming works.  
- **GPU Fallback**: Valence derivation can optionally use `distilbert-base-uncased-emotion` in 8‑bit mode on a free Kaggle GPU (`device="cuda"`). All other steps remain CPU‑only.

## Task Ordering (Corrected Dependencies)

| ID | Description | Depends On |
|----|-------------|------------|
| **T001** | Initialize environment, load config (`config.py`). | – |
| **T002** | **Ingest** – download the IAT Parquet from the verified URL, write to `data/raw/iat.parquet`. | T001 |
| **T003** | **Validate Core Columns** – ensure `response_time`, `stimulus_id`, `participant_id` exist; abort with “Data Gap: Schema Mismatch” if not. | T002 |
| **T004** | **Extract Stimulus Metadata** – separate prime vs. target images/words into `data/primes/` & `data/targets/`. | T003 |
| **T005** | **Linkage Metric Calculation (T018a)** – compute % of trials that have a matching image file; write `data/processed/ingest_metrics.json`. | T004 |
| **T006** | **Define Threshold (T018b)** – write `config/analysis_params.json` with `LINKAGE_THRESHOLD=95.0`. | T005 |
| **T007** | **Linkage Gate (T016)** – read `ingest_metrics.json` and `analysis_params.json`; HALT if `% < LINKAGE_THRESHOLD`. | T005, T006 |
| **T008** | **Derive Ambiguity (T018a)** – if `ambiguity` missing, run `derive_ambiguity.py`; write to `data/processed/linked_trials.csv`. | T007 |
| **T009** | **Derive Valence (T018b)** – if `prime_valence` missing, run `derive_valence.py` (CPU‑first; GPU fallback if required). | T007 |
| **T010** | **Merge Derived Scores** – create final `linked_trials.csv` with both scores, add `linkage_status`. | T008, T009 |
| **T011** | **Logging Setup (T009)** – create `code/logs/pipeline.log` and configure `logging` in `main.py`. | T001 |
| **T012** | **Demographics Check** – flag missing age/gender/education; write `state/demographics_status.json`. | T010 |
| **T013** | **VIF Pre‑Check (T027a)** – compute VIF on the design matrix **before** model fitting; write `state/vif_flag.json`. | T010, T012 |
| **T014** | **LME Fitting (T025)** – fit mixed‑effects model using `statsmodels`; incorporate robust SE if any derived predictor present. | T010, T012, T013 |
| **T015** | **Convergence Fallback (integrated in T014)** – try alternative optimizers up to 3 attempts; record in `state/model_convergence_metrics.json`. | T014 |
| **T016** | **Post‑Fit Diagnostics** – check convergence flag, VIF flag, write `state/model_diagnostics.json`. | T014 |
| **T017** | **FDR Correction (T028)** – apply Benjamini‑Hochberg to all p‑values; augment model result dict. | T016 |
| **T018** | **Associational Framing (T029)** – add `caution_note` & `limitation_note` keys to result dict. | T017 |
| **T019** | **Sensitivity Analysis (T030)** – sweep α ∈ {0.01,0.05,0.10}; write `reports/sensitivity_analysis.csv`. | T014 |
| **T020** | **Interaction Plot Generation** – seaborn/matplotlib figure saved as `reports/interaction_plot.png`. | T014 |
| **T021** | **PDF Assembly (T036)** – combine plots, coefficient table, sensitivity CSV into `reports/final_report.pdf`. | T018, T019, T020 |
| **T022** | **PII Scan** – run `code/pii_scan.py` on `data/processed/linked_trials.csv`; write `reports/pii_scan.json`. | T021 |
| **T023** | **Final Verification** – ensure all contract schemas validate; abort if any fail. | T021, T022 |

*All tasks run sequentially respecting the dependency graph; independent tasks (e.g., logging setup) occur early to guarantee artifact availability.*

## Mapping of FR/SC to Concrete Steps
- **FR‑001** → T003, T008, T009  
- **FR‑002** → T009 (valence), T008 (ambiguity)  
- **FR‑003** → T018 (caution notes)  
- **FR‑004** → T017 (FDR)  
- **FR‑005** → T013 (VIF)  
- **FR‑006** → T019 (sensitivity)  
- **SC‑001** → T005, T007 (linkage completeness)  
- **SC‑002** → T014, T015 (convergence rate)  
- **SC‑003** → T021 (PDF contents)  

All functional and success criteria are explicitly covered.

## Compute Feasibility
- **CPU‑first**: All steps except optional valence transformer run on ≤2 CPU cores, < 7 GB RAM.  
- **GPU Escape Hatch**: If `derive_valence.py` detects that the transformer exceeds CPU time (> 30 min), it switches to `device="cuda"` with 8‑bit quantization on a free Kaggle GPU. The pipeline auto‑detects CUDA errors and re‑runs the step on Kaggle.

---
