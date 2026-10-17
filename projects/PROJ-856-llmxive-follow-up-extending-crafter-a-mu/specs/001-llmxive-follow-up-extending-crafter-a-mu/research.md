# Research: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

## Objective
Validate whether a **structured typed‑edit harness** reduces **objective latency and iteration metrics** relative to a **natural‑language chat interface** when participants fix localized errors in scientific figures. *Note:* Because the CI validation uses synthetic participants, the study cannot directly measure human cognitive load; the inferred cognitive‑load conclusions will be confirmed only in a subsequent human‑subject experiment.

## Dataset Strategy
| Need | Availability | Action |
|------|--------------|--------|
| Failed figure generations (multiple) with ground‑truth layout vectors | **CrafterBench** – *no verified source* (see constitution) | **Synthetic surrogate**: generate a set of raster images (random plots) and corresponding JSON vector layouts; inject a single localized error per image (color, axis label, missing legend). All generation code is deterministic (seed = 42) and stored under `data/synthetic/`. |
| Semantic similarity model | Open‑source ResNet‑18 weights (CPU‑compatible) from `torchvision.models.resnet18(pretrained=True)` – publicly available on PyPI. | Load model in CPU mode; no external data download beyond the model checkpoint (auto‑download via `torchvision`). |
| Human participant data | Not required for CI validation; synthetic participants will emulate realistic latency/iteration distributions. | Simulated driver creates multiple participant sessions with randomized interface and task order. |

> **Note:** The pipeline is built to accept a real CrafterBench subset if a verified URL becomes available later; the data‑curation module detects the presence of a downloaded dataset and falls back to the synthetic generator otherwise.

## Methodology
1. **Randomized Counterbalanced Within‑Subject Design**  
   - For each simulated participant, `curate_failed_figures.py` provides the same 50 tasks.  
   - Interface order is randomized (seed = 42) and counterbalanced across participants (half start with Structured, half with Chat).  
   - **Task order** is also shuffled per participant to mitigate fatigue/learning effects.  

2. **A‑Prior Power Analysis**  
   - Using a medium effect size (Cohen’s d ≈ 0.5) and α = 0.05, a two‑tailed Wilcoxon signed‑rank test requires **N ≈ 28** participants.  
   - The pipeline computes this requirement before simulation; if the planned N < required, execution aborts with a clear error.  

3. **Instrumentation**  
   - Every edit (typed command or chat utterance) triggers `interaction_logger.py` → JSON line with fields: `timestamp_ms`, `iteration`, `payload`, `mode` (`structured`/`chat`).  

4. **Success Definition**  
   - **Exact vector match**: `vector_match.py` computes equality of serialized layout JSON.  
   - **Semantic equivalence**: `semantic_similarity.py` extracts feature vectors from the output image and the ground‑truth image; cosine similarity ≥ 0.95 ⇒ pass.  
   - A trial is marked **success** if **either** condition passes. Both scores are stored in a `SemanticValidation` record for independent analysis.  

5. **Statistical Test**  
   - Paired Wilcoxon signed‑rank test (SciPy `scipy.stats.wilcoxon`) on the per‑participant paired differences for:  
     - `time_to_success` (ms)  
     - `iteration_count`  
   - No preliminary normality test (as per FR‑006).  
   - Effect size *r* and two‑sided p‑value reported.  

6. **Multiple‑Comparison Control**  
   - Two primary outcomes → apply Bonferroni correction (α = 0.025 per test).  

7. **Retention & Validity Checks**  
   - After simulation, verify that at least **25** of the 30 sessions contain at least one non‑aborted successful trial; otherwise the analysis is halted.  
   - Tasks with corrupted ground‑truth vectors are skipped with a warning; N is adjusted accordingly.  

8. **Handling Edge Cases**  
   - **Timeout (>15 min)** → task logged as `"aborted"`; excluded from `time_to_success` mean but counted with max iteration for iteration analysis.  
   - **Corrupted ground‑truth** → task skipped, warning emitted, N adjusted.  
   - **Ambiguous semantic score (0.94‑0.95)** → flagged for manual review; excluded from primary analysis.  

## Decision / Rationale
| Component | CPU‑first or GPU‑escape? | Reason |
|-----------|--------------------------|--------|
| Data curation & synthetic generation | **CPU‑first** (pure NumPy/Pillow) | Trivial memory footprint (< 200 MB). |
| Semantic similarity model | **CPU‑first** (A moderately sized ResNet model runs comfortably on modest hardware resources.) | No need for GPU; model size ≈ tens of MB. |
| Wilcoxon test & report generation | **CPU‑first** | Scipy functions are CPU‑only. |
| No GPU‑only steps identified. | – | – |

All steps are guaranteed to complete within the allocated CI window on the free tier.

## Expected Deliverables
- **`data/`**: synthetic figures, ground‑truth vectors, checksums.  
- **`data/logs/`**: raw interaction logs (JSON lines).  
- **`data/validation/`**: `SemanticValidation` JSON lines.  
- **`outputs/report.md`**: statistical summary, tables, confidence intervals, **independent** success‑rate breakdowns (vector vs. semantic), and notes on any aborted or corrupted tasks.  
- **Contract files** (`contracts/*.schema.yaml`) for log, semantic validation, and analysis validation.  

---

