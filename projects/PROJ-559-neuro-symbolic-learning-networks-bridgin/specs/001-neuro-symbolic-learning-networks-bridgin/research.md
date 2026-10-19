# Research: Neuro‑Symbolic Learning Networks

## Research Question
*Within the ASSISTments domain, does a neuro‑symbolic explanation (neural narrative + symbolic trace) improve student reasoning accuracy, response time, and self‑reported comprehension compared to neural‑only and symbolic‑only explanations?*

## Background & Motivation
Educational AI often trades off fluency (LLM) for logical rigor (symbolic solvers). Bridging them may yield explanations that are both understandable and correct, potentially enhancing learning outcomes (cognitive System 1 vs. System 2). Prior work (e.g., BKT modeling) suggests that explanation format can affect knowledge acquisition speed and confidence.

## Verified Datasets
| Dataset | Role | Verified URL |
|---|---|---|
| **ASSISTments** | Source of math/logic problems (raw and unified) | https://huggingface.co/datasets/OloriBern/assistments-dataset/resolve/main/skill_builder_data_corrected.csv |
| **Human Pilot Data** | Calibration of BKT simulator (≥ 50 participants) | *Collected via approved survey platform; stored locally as `data/pilot/real_pilot_data.csv`* |
| **Real Student Data** | Primary inferential evidence (≥ 200 participants) | *Collected via approved survey platform; stored as `data/processed/real_student_data.csv`* |

*Note*: The spec mentions Khan Academy, but no verified direct‑download URL exists in the provided block. The pipeline therefore treats Khan as optional; if unavailable the Scope Reduction Protocol limits claims to ASSISTments (see research.md).

## Dataset Strategy
| Step | Action | Rationale |
|---|---|---|
| **Ingestion** | `download_assistments.py` pulls the CSV from the verified HuggingFace URL with a 300 s timeout. | Guarantees reproducible source (FR‑001, FR‑007). |
| **Optional Khan** | `download_khan.py` attempts download; on timeout logs error and proceeds without aborting (FR‑007, SC‑008). | Satisfies “attempt” requirement while preserving pipeline robustness. |
| **Unification** | `unify_datasets.py` merges available sources, stratifies by `dataset_source`, and ensures ≥ 30 % of problems from each source (FR‑021). If Khan missing, proportion check is relaxed and limitation noted. | Controls source bias (FR‑012). |
| **Schema Validation** | `validate_schema.py` validates against `problem.schema.yaml`. | Enforces data hygiene (III). |
| **Human Pilot** | Manual collection; stored as CSV with checksum. | Provides calibration data (FR‑010). |
| **Real Student** | Manual collection; stored as CSV with checksum. | Supplies primary evidence (FR‑011). |

## Methodological Rigor & Statistical Plan
- **Design**: Between‑subjects; each student receives exactly one explanation condition per problem (enforced by unique `(student_id, problem_id)` constraint).  
- **Mixed‑Effects Model** (FR‑006):  
  - Fixed effects: `explanation_condition`, `prior_knowledge_score`, `problem_difficulty`, `data_source`.  
  - Random intercepts: `problem_id`, `student_id`.  
  - Estimated via `statsmodels` (`MixedLM`) or `lme4` via `rpy2`.  
- **Multiple‑Comparison Correction**: Holm‑Bonferroni applied to the three pairwise condition contrasts (SC‑003).  
- **Effect Sizes**: Cohen’s d with 95 % CI for each contrast (SC‑003).  
- **Power**: Target ≥ 0.80 for effect size ≥ 0.1; sample‑size calculation deferred (`[deferred]`).  
- **Causal Inference**: Claims are **associational** for simulated data; primary causal language reserved for real‑student analysis (FR‑020).  
- **Measurement Validity**: ASSISTments problems have established validity in prior educational research (cited in literature).  
- **Collinearity**: VIF computed for `problem_difficulty` and `response_time`; if VIF > 5, report and interpret cautiously.  

## Compute Feasibility
- **CPU‑First**: TinyLlama‑1.1B‑Chat quantized to 4‑bit runs comfortably on 2 CPU cores (< 2 GB RAM).  
- **GPU Escape Hatch**: If CPU inference fails, the same script will re‑run on a Kaggle free GPU (`device="cuda"`). No fabricated CPU surrogate is used.  
- **Memory Management**: Large CSVs streamed (`datasets.load_dataset(..., streaming=True)`) to stay within 7 GB RAM.  
- **Runtime**: Estimated ≤ 5 h total on free‑tier runner; GPU offload adds ≤ 2 h extra if needed.

## Decision / Rationale Summary
- **Dataset choice**: ASSISTments is the only fully verified source; Khan is optional and handled gracefully.  
- **Model size**: 1 B‑parameter quantized LLM meets CPU constraints; larger models would require GPU, handled by offload.  
- **Simulation**: BKT calibrated on real pilot data ensures plausible behavior without circularity.  
- **Analysis**: Mixed‑effects respects hierarchical data and aligns with constitution principle VI.  
- **Scope Reduction**: Guarantees scientific honesty if Khan data is unavailable (SC‑001, SC‑009).  

---
