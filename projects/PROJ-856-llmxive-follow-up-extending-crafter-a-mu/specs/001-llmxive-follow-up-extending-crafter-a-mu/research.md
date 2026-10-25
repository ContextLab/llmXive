# Research: llmXive follow‑up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

## Objective
Evaluate whether a **structured typed‑edit harness** reduces **objective latency** (`time‑to‑success`), **iteration count**, and **subjective cognitive load** (NASA‑TLX) relative to a **natural‑language chat interface** when participants correct localized errors in scientific figures, while controlling for participant expertise.

## Dataset Strategy
| Need | Availability | Action |
|------|--------------|--------|
| Failed figure generations with ground‑truth layout vectors (≈ a moderate number of items) | **CrafterBench** – *NO verified open‑source URL* (see verified datasets block). | `curate_failed_figures.py` will **abort** if a download is attempted without a verified URL, making the missing dataset explicit. When an open source becomes available, the same script will ingest it without modification. |
| Pre‑trained visual similarity model | CLIP ViT‑B (available via `torchvision` / `transformers`) – CPU‑only weights auto‑downloaded from HuggingFace. | Load on CPU; weights cached locally. |
| Human participant logs | Not needed for CI; will be collected in the field study. | `human_data_collection.py` (stub) will ingest real logs when available. |
| NASA‑TLX questionnaire | Publicly described in NASA‑TLX literature. | Integrated into UI; scores (0‑100) stored per task. |
| Participant expertise questionnaire | Self‑report (0‑5 Likert). | Collected at session start; stored as `expertise_level` in `ParticipantSession`. |

## Methodology
1. **Within‑Subjects Counterbalanced Design**  
   - Each real participant completes the same set of tasks.  
   - Interface order is **randomized** (seed = 42 + participant ID) **and fully counterbalanced**: half of participants receive the Structured harness first, half receive Chat first, guaranteeing equal numbers for each first‑interface condition.  
   - A **5‑minute wash‑out interval** separates the two interface blocks (FR‑010).  
   - Task order is shuffled per participant (seed = 42 + participant ID).  

2. **A‑Prior Power Analysis**  
   - `power_analysis.py` computes the minimum N for a **mixed‑effects model** with expertise as a covariate, using **α = 0.025** (Bonferroni‑adjusted) and effect size ≈ moderate (i.e., a medium effect).  
   - Required N ≈ 40 participants; pipeline aborts if the planned N < required, ensuring target power = 0.80 (FR‑009).  

3. **Instrumentation (Construct Validity)**  
   - Every edit triggers `interaction_logger.py`, writing a JSONL line with millisecond timestamps, iteration number, payload, **and NASA‑TLX score** (`subjective_load`).  
   - For **real** participants, timestamps reflect actual wall‑clock time.  
   - For **synthetic** CI verification, deterministic timestamps are generated (seeded) to guarantee reproducibility.  

4. **Success Definition**  
   - **Primary success** = **exact vector match** (`vector_match.py`).  
   - **Secondary validation** = CLIP ViT‑B/32 cosine similarity **≥ 0.95** (`semantic_similarity.py`).  
   - `overall_success` mirrors the vector‑match result only; `semantic_pass` is recorded separately and does **not** affect inclusion in the primary analysis.  

5. **Statistical Testing**  
   - Paired Wilcoxon signed‑rank test (`scipy.stats.wilcoxon`) on per‑participant differences for `time_to_success_ms`, `iteration_count`, `subjective_load`, and **semantic_success_rate**.  
   - **Bonferroni correction for four metrics** (α = 0.025 per test).  
   - Effect size *r* = Z / √N; 95 % CI for the median difference via bootstrap (1 000 resamples).  
   - **Exploratory covariate analysis**: Linear mixed‑effects model includes `expertise_level` as a fixed effect (FR‑012).  

6. **Retention & Validity Checks**  
   - `retention_check.py` ensures **≥ 28** of the recruited **≥ 32** participants have completed both interface blocks with at least one primary‑success trial each (SC‑004).  
   - If the criterion is not met, the pipeline aborts and flags a redesign.  

7. **Edge‑Case Handling**  
   - **Timeout** (> 15 min) → logged as `"aborted"`; **aborted tasks are excluded** from latency and iteration analyses (FR‑011).  
   - **Corrupted ground‑truth** → task skipped; N adjusted accordingly.  
   - **Semantic score 0.94–0.95** → flagged for manual review; does **not** affect primary success status.  

## Decision / Rationale
| Component | CPU‑first or GPU‑escape? | Reason |
|-----------|--------------------------|--------|
| Synthetic data generation | **CPU‑first** (NumPy, Pandas) | Minimal resource usage; suitable for CI verification. |
| CLIP ViT‑B/32 semantic similarity | **CPU‑first** (torch CPU backend) | Model size (~300 MB) fits comfortably on the runner. |
| Statistical analysis | **CPU‑first** (SciPy, Statsmodels) | Pure CPU libraries. |
| Full pipeline (CI verification) | **CPU‑first** | Entire pipeline stays within runtime and memory budget. |
| Real‑world similarity model (if larger later) | **GPU‑escape** (Kaggle) – not required now. | Placeholder for future scaling. |

## Expected Deliverables
- `data/figures/` and `data/ground_truth/` (synthetic surrogate now; real subset can replace when a verified open source is supplied).  
- `data/logs/` (raw interaction logs, JSONL, schema‑validated, including `subjective_load`).  
- `data/validation/` (SemanticValidation records).  
- `outputs/analysis_results.jsonl` (four `AnalysisResult` objects, each containing the required `test_used` field).  
- `outputs/report.md` (statistical summary, tables, confidence intervals, **average NASA‑TLX scores**, and a breakdown of success‑rate (vector vs. semantic)).  
- Contract schemas in `contracts/`.  
- End‑to‑end pipeline executable via:  
  ```bash
  python -m src.run_pipeline --config config.yaml
  ```

---


