# Research: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

## Objective
Determine whether a **structured typed‑edit harness** yields lower **objective latency** (`time‑to‑success`) and fewer **iteration steps** than a **natural‑language chat interface** when participants correct localized errors in scientific figures. 

**Crucial Distinction**: The project implements a pipeline that is validated using synthetic data (Software Verification) but is designed to produce research results only from real human interaction logs (Research Execution). Synthetic timestamps are used only to test the code's ability to process data; they lack construct validity for measuring human cognitive load.

## Dataset Strategy
| Need | Availability | Action |
|------|--------------|--------|
| Failed figure generations with ground‑truth layout vectors (approximately a moderate number) | **CrafterBench** – **Unverified/Missing Source** (Constitution Principle II) | **Blocking Issue**: A verified public URL for the CrafterBench subset is required to satisfy FR-001. Until a verified source is provided, the pipeline will use a deterministic synthetic surrogate (seed=42) **strictly for software verification**. Research results cannot be generated until the real dataset is acquired. |
| Pre‑trained visual similarity model | `torchvision.models.resnet18(pretrained=True)` – publicly available | Load CPU‑only ResNet‑18; model checkpoint is auto‑downloaded by `torchvision`. |
| Human participant data | Not required for CI validation; collected in field study. | `human_data_collection.py` provides a stub for ingesting logs from real participants. Synthetic participants (`simulate_participants.py`) are used for CI verification only. |

## Methodology
1. **Within‑Subjects Counterbalanced Design**  
   - Each *real* participant receives the same 50 tasks.  
   - Interface order is randomized (seed = 42) and counterbalanced.  
   - Task order is shuffled per participant.  

2. **A‑Prior Power Analysis**  
   - Using `statsmodels.stats.power.WilcoxonPower` (or Monte‑Carlo fallback) with effect size *d* ≈ 0.5, α = 0.05, the script computes a minimum **N ≈ 28**.  
   - The pipeline aborts if the planned N < required.  

3. **Instrumentation (Construct Validity)**  
   - Every edit submitted to `/edit` triggers `interaction_logger.py`.  
   - **Research Execution**: Timestamps are captured from the real wall‑clock time of human interaction, providing the valid construct for “objective latency”.  
   - **Software Verification**: Deterministic timestamps are used in CI to ensure the pipeline runs without error.  

4. **Success Definition**  
   - **Exact vector match**: `vector_match.py` checks JSON equality of the final layout vector against ground truth.  
   - **Semantic equivalence**: `semantic_similarity.py` extracts ResNet‑18 features; cosine similarity ≥ 0.95 ⇒ pass.  
   - **Primary success** requires **both** conditions to be true.  

5. **Statistical Testing**  
   - Paired Wilcoxon signed‑rank test (`scipy.stats.wilcoxon`) on per‑participant paired differences.  
   - No preliminary normality test (FR-006).  
   - Two primary outcomes → Bonferroni correction (α = 0.025 per test).  
   - Effect size *r* = Z / √N, 95% CI for median difference via bootstrap (1,000 resamples).  

6. **Retention & Validity Checks**  
   - `retention_check.py` verifies that ≥ 25 of 30 sessions contain at least one non‑aborted successful trial.  
   - Tasks with corrupted ground‑truth vectors are skipped; N is adjusted.  

7. **Edge‑Case Handling**  
   - **Timeout (>15 min)** → task logged as `"aborted"`; excluded from `time_to_success` but counted in iterations.  
   - **Ambiguous semantic score (0.94-0.95)** → flagged for manual review; excluded from primary analysis.  

## Decision / Rationale
| Component | CPU‑first or GPU‑escape? | Reason |
|-----------|--------------------------|--------|
| Synthetic data generation | **CPU‑first** (NumPy + Matplotlib) | Minimal memory/CPU load. |
| Semantic similarity model | **CPU‑first** (ResNet‑18) | No GPU required; model size ≈ on the order of tens of megabytes. |
| Statistical analysis | **CPU‑first** (SciPy) | Pure CPU libraries. |

## Expected Deliverables
- `data/figures/` and `data/ground_truth/` (Real CrafterBench subset, or synthetic set for verification).  
- `data/logs/` (Raw interaction logs, JSONL, schema‑validated).  
- `data/validation/` (SemanticValidation records, requiring both checks).  
- `outputs/analysis_results.jsonl` (Two `AnalysisResult` objects).  
- `outputs/report.md` (Full statistical summary).  
- Contract schemas in `contracts/`.  
- End‑to‑end pipeline executable via `python -m src.run_pipeline --config config.yaml`.  
