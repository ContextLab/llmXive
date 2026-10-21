# Research: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

## Objective
Evaluate whether a **structured typed‑edit harness** reduces **objective latency** (`time‑to‑success`) and **iteration count** relative to a **natural‑language chat interface** when participants correct localized errors in scientific figures, while also capturing **subjective cognitive load** (NASA‑TLX) and controlling for participant expertise.

## Dataset Strategy
| Need | Availability | Action |
|------|--------------|--------|
| Failed figure generations with ground‑truth layout vectors (approximately a moderate number of items) | **CrafterBench** – verified via HuggingFace: `https://huggingface.co/datasets/crafterbench` | Download the subset for the real study. For CI verification, generate a deterministic synthetic surrogate (`--verify-only`). |
| Pre‑trained visual similarity model | `torchvision.models.resnet18(pretrained=True)` – publicly available via PyPI | Load CPU‑only ResNet‑18; model weights auto‑downloaded on first run. |
| Human participant logs | Not needed for CI; collected in the field study. | `human_data_collection.py` ingests real logs; synthetic logs (`simulate_participants.py`) are used for pipeline verification only. |
| NASA‑TLX questionnaire | Publicly available (paper‑based or digital). | Integrated into the UI; scores (0‑100) stored per task. |
| Participant expertise questionnaire | Self‑report (0‑5 Likert). | Collected at session start; stored as `expertise_level` in `ParticipantSession`. |

## Methodology
1. **Within‑Subjects Counterbalanced Design**  
   - Each **real** participant completes the same 50 tasks.  
   - Interface order is randomized (seed = 42) **and fully counterbalanced** across participants.  
   - A **2‑minute wash‑out interval** separates the two interface blocks to mitigate carry‑over learning.  
   - **Task order** is shuffled per participant (seed = 42 + participant ID) to further reduce practice effects.  

2. **A‑Prior Power Analysis**  
   - `power_analysis.py` computes the minimum N for a paired Wilcoxon test with **α = 0.025** (Bonferroni‑adjusted) and effect size *d* ≈ 0.5.  
   - Required N is set to a sufficiently large value; the pipeline aborts if the planned N < required, ensuring adequate power.  

3. **Instrumentation (Construct Validity)**  
   - Every edit triggers `interaction_logger.py`, which writes a JSONL line with millisecond timestamps, iteration number, payload, **and NASA‑TLX score** (`subjective_load`).  
   - For **real** participants, timestamps reflect actual wall‑clock time → valid measure of cognitive load.  
   - For **synthetic** verification, deterministic timestamps are generated (seeded) to ensure reproducibility.  

4. **Success Definition**  
   - **Exact vector match** (`vector_match.py`): JSON equality of the final layout vector vs. ground‑truth.  
   - **Semantic equivalence** (`semantic_similarity.py`): ResNet‑18 feature cosine similarity **≥ 0.90** (pilot data shows this balances false‑positives/negatives).  
   - **Overall success** = both conditions true (`overall_success`).  

5. **Statistical Testing**  
   - Paired Wilcoxon signed‑rank test (`scipy.stats.wilcoxon`) on per‑participant differences for `time_to_success`, `iteration_count`, **and** `subjective_load`.  
   - No preliminary normality test (per FR‑006).  
   - **Bonferroni correction** for the three metrics (α = 0.025 each).  
   - Effect size *r* = Z / √N; 95 % CI for the median difference via bootstrap (1 000 resamples).  
   - **Exploratory covariate analysis**: Linear mixed‑effects model includes `expertise_level` as a fixed effect to control for prior experience.  

6. **Retention & Validity Checks**  
   - `retention_check.py` ensures **≥ 25** of 30 sessions have at least one successful correction.  
   - Tasks with corrupted ground‑truth vectors are skipped; N is adjusted accordingly.  
   - **Aborted tasks** (timeout > 15 min) are **excluded from all three primary analyses** (latency, iteration count, and NASA‑TLX) to avoid asymmetric bias.  

7. **Edge‑Case Handling**  
   - **Timeout** → logged as `"aborted"`; excluded from all analyses.  
   - **Corrupted ground‑truth** → task skipped, warning logged, N adjusted.  
   - **Semantic score 0.94–0.95** → flagged for manual review; excluded from primary analysis.  

## Decision / Rationale
| Component | CPU‑first or GPU‑escape? | Reason |
|-----------|--------------------------|--------|
| Synthetic data generation | **CPU‑first** (NumPy, Pandas) | Minimal resource usage. |
| ResNet‑18 semantic similarity | **CPU‑first** (torch CPU backend) | Model ≈ tens of MB; runs comfortably on 2‑core runner. |
| Statistical analysis | **CPU‑first** (SciPy, Statsmodels) | Pure CPU libraries. |
| Full pipeline (CI verification) | **CPU‑first** | Entire pipeline stays within a reasonable runtime and memory budget. |
| Real‑world similarity model (if larger model chosen later) | **GPU‑escape** (Kaggle) – not required now. |

## Expected Deliverables
- `data/figures/` and `data/ground_truth/` (real CrafterBench subset **or** synthetic surrogate).  
- `data/logs/` (raw interaction logs, JSONL, schema‑validated, including `subjective_load`).  
- `data/validation/` (SemanticValidation records).  
- `outputs/analysis_results.jsonl` (three `AnalysisResult` objects: time_to_success_ms, iteration_count, subjective_load).  
- `outputs/report.md` (statistical summary, tables, confidence intervals, **average NASA‑TLX scores**, success‑rate breakdown).  
- Contract schemas in `contracts/`.  
- End‑to‑end pipeline executable via:  
  ```bash
  python -m src.run_pipeline --config config.yaml
  ```

---


