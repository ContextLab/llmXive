# Research: llmXive follow-up: extending "Leveraging Verifier-Based Reinforcement Learning in Image Editing"

## Overview
This document details the experimental design, data acquisition, model execution, and statistical analysis that will produce the evidence required by the functional (FR‑*) and success‑criteria (SC‑*) specifications.

## 1. Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Raw prompts & images | InstructPix2Pix (3 public shards) | `datasets.load_dataset("parquet", data_files=URL, streaming=False)` | URLs are verified in the “Verified datasets” block. |
| Synthetic feasibility scores | Deterministic heuristic (Section 2) | Generated locally after download | Used **only** for conflict generation; **never** for evaluation (FR‑010). |
| Human feasibility validation | Crowdsourced annotation of **all 1000 prompts** | `src/data/human_annotation.py` writes `data/human_validation.csv` | Provides the primary ground‑truth for alignment evaluation (FR‑001, FR‑009). |
| Conflict generation | Rule‑based augmentation of neutral prompts | `src/data/conflict_generator.py` creates conflicting prompts | Guarantees a balanced set of genuine contradictions. |

All downloads are performed programmatically on the CI runner; no manual steps are required.

## 2. Synthetic Feasibility Scoring (FR‑001 – generation only)
1. **Neutral prompts** → synthetic score `1.0`.  
2. **Conflicting prompts** → parse into atomic clauses; compute the proportion of mutually compatible clauses using an antonym‑lookup dictionary (WordNet). Result ∈ [0, 1] reflects “partial compliance”.  
3. Store in `data/curated_prompts.csv` as `synthetic_score`.  

**Human Validation**: A separate annotation step (Section 1) collects `human_score`. If Pearson r between synthetic and human scores < 0.6, we flag the heuristic and **exclude synthetic scores from any downstream evaluation** (fulfilling FR‑010).

## 3. Baseline Verifier Evaluation (FR‑003)
- Load the distilled Edit‑R1 1B model from Hugging Face (`"llmxive/edit-r1-1b-distilled"`).  
- Run inference on each `prompt_text` **without** graph context, using `torch.device("cuda")` if available (GPU escape hatch) or CPU otherwise.  
- Record verifier alignment probability as `verifier_score`.  
- Output `data/baseline_scores.csv` with columns: `prompt_id`, `verifier_score`, `human_score`, `alignment_delta = verifier_score - human_score`.  

*Alignment delta is always computed against the independent **human_score** (synthetic scores are ignored).*

## 4. Symbolic Constraint‑Graph Parser (FR‑002, Principle VI)
- **Tokenization & POS** via spaCy (`en_core_web_sm`).  
- **Node extraction**: noun‑phrase chunks representing actionable principles.  
- **Temporal edges**: detect cue words (“first”, “then”, “after”) → `temporal-precedes`.  
- **Contradiction edges**: use WordNet antonym pairs to flag `contradiction`.  
- **Graph abstraction constraint**: node `label` fields contain only the extracted **principle phrase** (no full paraphrased clause); edges carry only the relation type. This guarantees that the JSON graph supplies *pure structural* information to the verifier.  
- Serialize each graph to JSON (`graph_<prompt_id>.json`).  
- **Runtime budget**: ≤ 30 min on 2‑core CPU (validated by profiling).  
- **GPU usage**: None; the parser runs strictly on CPU.  

**Failure policy**: Prompts for which graph construction fails are logged, a warning is emitted, and a `null` graph (`{}`) is used for that sample; the pipeline continues without halting.

## 5. Graph‑Augmented Verifier Evaluation (FR‑004)
- Embed each graph JSON into the verifier’s prompt template under a `Context:` section.  
- **Control Conditions**:  
  1. **Random filler** – a JSON object of similar size containing unrelated key‑value pairs.  
  2. **Empty graph** – `{}`.  
- Run inference (GPU escape hatch if needed) and store results in `data/augmented_scores.csv` (same schema as baseline, with an additional `condition` column indicating `graph_augmented`, `control_filler`, or `control_empty`).  

## 6. Statistical Comparison (FR‑005, FR‑006, FR‑007)
1. **Primary paired test** – Conflicting subset (`baseline_scores` vs. `augmented_scores`).  
   - Normality check (Shapiro‑Wilk).  
   - If normal → paired **t‑test**; else → **Wilcoxon signed‑rank**.  
   - Report: mean alignment‑score difference (SC‑001), Cohen’s d (or rank‑biserial) (SC‑008), 95 % CI, p‑value (SC‑004).  
2. **Neutral‑subset paired test** – Ensure graph augmentation does **not** degrade performance on neutral prompts (addresses SC‑006).  
3. **Control comparison** – Baseline vs. random filler (same test) to confirm improvements are not due to added context length.  
4. **Robustness check** – Generate a hold‑out set of re‑phrased conflicting prompts via back‑translation; repeat full pipeline and paired test.  
   - Verify that the effect‑size drop is **non‑significant (p ≥ 0.05)** (SC‑005).  
5. **Multiple‑comparison correction** – Apply **Benjamini‑Hochberg FDR** (α = 0.05) across the three hypothesis tests (primary, neutral, robustness). Adjusted p‑values are reported (SC‑004).  

6. **Correlation analysis** – Compute Pearson r between verifier scores (baseline & augmented) and human scores; require **r ≥ 0.5** (SC‑007).  

All calculations use `scipy.stats` and `statsmodels.stats.multitest`.

## 7. Power Analysis (Methodology)
Using G*Power (paired t‑test, α = 0.05, effect size d = 0.5), **N = 500** conflicting prompts yields power ≈ 0.86. If observed variance exceeds the assumption, we will increase to **N = 600** (still within the 1000‑prompt budget). This satisfies the implicit power expectation for SC‑001 and SC‑008.

## 8. Runtime & Memory Auditing (FR‑008, SC‑002, SC‑003, SC‑009)
- `psutil` logs peak RAM for each stage; assert ≤ 7 GB.  
- Wall‑clock timers log duration of parser, baseline inference, augmented inference, and analysis; total ≤ 6 h.  
- **Baseline verifier runtime** is recorded separately and must be **≤ 2 h** on the CPU‑only runner (SC‑009).  

## 9. Decision / Rationale (CPU vs GPU)
The 1B Edit‑R1 model in float32 exceeds the 7 GB RAM limit on CPU, so inference scripts request a CUDA device. If `torch.cuda.is_available()` is false on the free runner, the platform automatically re‑runs the same command on a free Kaggle GPU (GPU escape hatch). The symbolic parser remains CPU‑only, satisfying Principle VI.

## 10. Deliverables
- `data/curated_prompts.csv` (prompt text + synthetic & **human** feasibility scores).  
- `data/constraint_graphs/*.json` (one graph per prompt, abstraction‑only).  
- `data/baseline_scores.csv`.  
- `data/augmented_scores.csv` (including control runs).  
- `analysis/report.json` (p‑values, effect sizes, CIs, runtime, memory, baseline runtime, correlation).  
- `analysis/report.csv` (human‑readable summary for the paper).  

All files conform to the schema in `contracts/evaluation_report.schema.yaml`.

## 11. Ethical & Reproducibility Notes
- Human annotation data stored under `data/human_validation.csv` with SHA‑256 checksums recorded in the project state file.  
- All randomness seeded (`numpy.random.seed(42)`, `torch.manual_seed(42)`).  
- Synthetic conflict generator is deterministic given the seed, ensuring reproducibility.

## 12. Independence Assurance
Evaluation relies exclusively on **human‑annotated feasibility scores** as ground‑truth, eliminating any circularity with the rule‑based antonym detection used for graph construction.

## 13. Verification
```bash
pytest tests/contract/test_evaluation_report.py
```
All contract tests must pass before CI marks the job successful.

## 14. GPU Escape Hatch Note
If the runner reports `torch.cuda.is_available() == False`, the verifier scripts automatically switch to the Kaggle GPU escape hatch (the platform will re‑run the same command on a free GPU). No code changes are required; just ensure the `torch` and `transformers` versions support `device="cuda"`.

---

