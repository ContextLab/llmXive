# Research: Neuro‑Symbolic Learning Networks

## Research Question
*Within the ASSISTments domain, does a neuro‑symbolic explanation (neural narrative + symbolic trace) improve student reasoning accuracy, response time, and self‑reported comprehension compared to neural‑only and symbolic‑only explanations?*

## Background & Motivation
Neural language models generate fluent natural‑language explanations, yet they may lack logical rigor. Symbolic solvers provide precise traceability but can be opaque to novices. A hybrid neuro‑symbolic explanation could combine the pedagogical strengths of both, potentially boosting learning outcomes. Prior work on explanation formats in intelligent tutoring systems (e.g., Koedinger et al.) emphasizes the need for mixed‑methods evaluation (accuracy, speed, confidence). This study directly tests that hypothesis in a controlled educational setting.

## Verified Datasets
| Dataset | Role | Verified URL |
|---|---|---|
| **ASSISTments** | Source of math/logic problems (raw) | https://huggingface.co/datasets/OloriBern/assistments-dataset/resolve/main/skill_builder_data_corrected.csv |
| **Khan Academy** | Source of additional math/logic problems (raw) | *No verified open download URL is available.* |
| **Human Pilot Data** | Calibration of BKT simulator (≥ 50 participants) | *Collected locally; stored at `data/pilot/real_pilot_data.csv`* |
| **Real Student Data** | Primary inferential evidence (≥ 200 participants) | *Collected locally; stored at `data/processed/real_student_data.csv`* |

*Note*: Because no verified open Khan Academy dataset exists, the pipeline **must abort** if the Khan download cannot be completed. This limitation is recorded for a future spec amendment; the current pipeline proceeds only when both datasets are available.

## Dataset Strategy
| Step | Action | Rationale |
|---|---|---|
| **Ingestion** | `download_assistments.py` fetches the CSV from the verified HuggingFace URL with a 300 s timeout (FR‑001, FR‑007). | Guarantees reproducibility and satisfies ASSISTments requirement. |
| **Khan Download** | `download_khan.py` attempts to download the Khan Academy dataset. If the download fails (no verified URL or timeout), the CI job aborts with exit 1 and a clear error message (FR‑001, FR‑007, SC‑008). | Enforces the requirement that **both** datasets be present; flags the missing open source. |
| **Unification** | `unify_datasets.py` merges the two sources, **enforces ≥ 30 % representation from each source** when both are present (FR‑012, FR‑021). | Controls source bias. |
| **Schema Validation** | `validate_schema.py` checks `unified_problems.csv` against `problem.schema.yaml`. | Enforces data hygiene (III). |
| **Human Pilot** | Manual collection of ≥ 50 participants across three explanation conditions; stored as `real_pilot_data.csv`.<br>Run `simulation/pilot_calibrator.py` to fit BKT parameters, compute RMSE, TOST (FR‑010). If calibration fails, abort (prevents circular simulation). | Provides calibration data (FR‑010). |
| **Real‑Student Data** | Manual collection of ≥ 200 participants; stored as `real_student_data.csv`.<br>Run `analysis/merge_data.py` to concatenate simulated + real, add `data_source` column (FR‑011). | Supplies primary evidence (FR‑011). |

## Methodological Rigor & Statistical Plan
- **Design**: Between‑subjects; each student experiences only one explanation condition per problem. Random assignment enforced by the simulator and by study recruitment scripts.  
- **Mixed‑Effects Model** (FR‑006):  
  - Fixed effects: `condition`, `prior_knowledge_score`, `difficulty`.  
  - Random intercepts: `problem_id`, `student_id`.  
  - Implemented with `statsmodels.MixedLM` (Python) or `lme4` (R via `rpy2`).  
- **Exploratory Diagnostics**: Run the same mixed‑effects model on the **combined** simulated + real dataset **solely for diagnostics** (effect‑size CI widths, `data_source` effect) – results are reported but **not used for primary causal claims** (FR‑020).  
- **Primary Inference**: Run the mixed‑effects model **only on the real‑student subset**; this satisfies FR‑006, FR‑011, and the constitution’s Educational Evaluation Rigor principle.  
- **Multiple‑Comparison**: Holm‑Bonferroni correction applied to the three pairwise condition contrasts (SC‑003).  
- **Effect Sizes**: Cohen’s d with 95 % confidence intervals for each contrast (SC‑003).  
- **Power**: No formal power analysis is claimed; with ≥ 200 real participants the study may be under‑powered for small effects. This limitation is **explicitly acknowledged** (methodology‑3bceee5f).  
- **Causal Claims**: Results from simulated data are labeled *exploratory* (FR‑020). Primary inferential claims are drawn solely from the real‑student dataset.  
- **Measurement Validity**: ASSISTments problems have established validity in prior tutoring research (cited in the literature review).  
- **Collinearity**: Variance Inflation Factor (VIF) computed for `difficulty` and `rt_seconds`; VIF > 5 triggers a diagnostic note.  

## Prior Knowledge Score
- **Simulated students**: The calibrated BKT model provides an estimated mastery probability at the start of each problem; this probability is recorded as `prior_knowledge_score`.  
- **Real students**: A short pre‑test administered before the main task yields a numeric `prior_knowledge_score` stored in `real_student_data.csv`.  

## Compute Feasibility
- **CPU‑First**: TinyLlama‑1.1B‑Chat quantized to 4‑bit runs on ≤ 2 CPU cores, ≤ 2 GB RAM per inference.  
- **GPU Escape Hatch**: If CPU OOM occurs, the same script re‑executes on a free Kaggle GPU (`device="cuda"`). No fabricated CPU surrogate is used.  
- **Streaming**: Large CSVs processed with `datasets.load_dataset(..., streaming=True)` to keep RAM under 7 GB.  
- **Runtime**: End‑to‑end ≤ 5 h on the free CI runner; GPU off‑load adds ≤ 2 h, still within the 6 h job limit.  

## Decision / Rationale Summary
- **Dataset Choice**: ASSISTments is the only fully verified open dataset; Khan Academy lacks a verified URL, so the pipeline aborts if it cannot be obtained, satisfying FR‑001 while flagging a scope limitation.  
- **Model Size**: 1 B‑parameter quantized LLM satisfies CPU constraints; larger models would force a GPU‑only solution, which is avoided.  
- **Simulation**: BKT calibrated on a human pilot ensures realistic exploratory behavior while keeping primary inference human‑based.  
- **Analysis**: Mixed‑effects regression aligns with constitution principle VI and captures hierarchical data structure.  
- **Scope‑Reduction**: If Khan download fails, the job aborts with a clear error; this enforces the requirement that **both** datasets be present.  

---


