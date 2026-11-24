# Research: llmXive follow‑up – Graph‑augmented Verifier Evaluation

## 1. Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Raw prompts & images | InstructPix2Pix (three verified parquet shards) | `datasets.load_dataset("parquet", data_files=[URL1, URL2, URL3], streaming=False)` | URLs are listed in the contract block; each file’s SHA‑256 is recorded in `data/raw/provenance.json`. |
| Human feasibility scores | Crowdsourced annotation of **1 000** prompts (500 conflicting, 500 neutral) | `src/data/human_annotation.py` writes `data/results/human_validation.csv` | Provides the primary ground‑truth for alignment (FR‑009). |
| Conflict verification | Manual/heuristic verification of conflict status (via `src/data/conflict_verify.py`) | Produces `conflict_verified` column in `curated_prompts.csv`; ensures an equal number of conflicting and neutral prompts. | Guarantees that the “conflicting” subset truly contains contradictions. |
| Synthetic feasibility scores | Deterministic heuristic (Section 2) | Generated locally in `src/data/curate.py` (column `synthetic_score`) | **Never** used for evaluation (FR‑010). |

All downloads and processing are performed programmatically on the CI runner; no manual steps are required.

## 2. Synthetic Feasibility Scoring (generation only)
1. **Neutral prompts** → synthetic score `1.0`.  
2. **Conflicting prompts** → parse into atomic clauses; compute the proportion of mutually compatible clauses using a WordNet‑based antonym dictionary. Result ∈ [0, 1] reflects “partial compliance”.  
3. Store in the `synthetic_score` column of `curated_prompts.csv`.  

**Human Validation**: a separate annotation step (Section 1) collects `human_score`. If Pearson r between synthetic and human scores < 0.6, we flag the heuristic and **exclude synthetic scores from any downstream evaluation** (fulfilling FR‑010).

## 3. Baseline Verifier Evaluation (FR‑003)
- Load the distilled Edit‑R1 1B model from Hugging Face (`"llmxive/edit-r1-1b-distilled"`).  
- **CPU‑only 8‑bit quantized inference** keeps RAM < 7 GB and avoids any GPU dependence.  
- Run inference on each `prompt_text` **without** graph context, recording verifier alignment probability as `verifier_score`.  
- Output `data/results/baseline_scores.csv` with columns: `prompt_id`, `verifier_score`, `human_score` (for the 1 000 human‑scored prompts), `alignment_abs = |verifier_score - human_score|`.  

*Alignment absolute difference is always computed against the independent **human_score** (synthetic scores are ignored).*

**Runtime target**: **≤ 2 hours** for the full 1 000 human‑scored prompts (≈ 0.3 s per prompt). If runtime exceeds 2 h, the pipeline aborts and reports the limitation (SC‑009).

## 4. Symbolic Constraint‑Graph Parser (FR‑002, Principle VI)
- **Tokenization & POS** via spaCy (`en_core_web_sm`).  
- **Node extraction**: noun‑phrase chunks representing actionable principles.  
- **Temporal edges**: detect cue words (“first”, “then”, “after”) → `temporal-precedes`.  
- **Contradiction edges**: two complementary heuristics  
  1. WordNet antonym dictionary.  
  2. Cue‑word patterns (“but”, “however”, “contradict”, “while”).  
- Serialize each graph to JSON (`graph_<prompt_id>.json`).  
- **Runtime budget**: ≤ 30 min on 2‑core CPU (validated by profiling).  
- **GPU usage**: None; the parser runs strictly on CPU.  

**Failure policy**: Prompts for which graph construction fails are logged, a warning is emitted, and a `null` graph (`{}`) is used for that sample; the pipeline continues without halting.

## 5. Randomization & Counterbalancing (supports reproducibility)
For each prompt we randomly permute the order of the four evaluation conditions:

1. Baseline (raw prompt)  
2. Graph‑augmented  
3. Control‑filler (random JSON of similar size)  
4. Control‑empty (`{}`)

Permutation generated with a fixed seed (`numpy.random.seed(12345)`) ensures reproducibility while eliminating systematic order effects (addresses SC‑002).

## 6. Graph‑Augmented Verifier Evaluation (FR‑004)
- Embed each graph JSON into the verifier’s prompt template under a `Context:` section.  
- **Control Conditions**:  
  1. **Random filler** – a JSON object of similar size containing unrelated key‑value pairs.  
  2. **Empty graph** – `{}`.  
- Run inference (**CPU‑only 8‑bit quantized**) and store results in `data/results/augmented_scores.csv` (same schema as baseline, plus a `condition` column indicating `graph_augmented`, `control_filler`, or `control_empty`).  

## 7. Statistical Comparison (FR‑005, FR‑006, FR‑007, FR‑008)
1. **Primary paired test** – Conflicting subset (500 prompts with human scores) comparing baseline vs. graph‑augmented.  
   - Normality check (Shapiro‑Wilk).  
   - If normal → paired **t‑test**; else → **Wilcoxon signed‑rank**.  
   - Report: mean `alignment_abs` difference, Cohen’s d (or rank‑biserial), 95 % CI, p‑value.  
2. **Neutral‑subset paired test** – Verify that graph augmentation does not degrade performance on neutral prompts (500 human‑scored neutral prompts).  
3. **Control comparison** – Baseline vs. random filler (same test) to confirm improvements are not due to added context length.  
4. **Robustness check** – Apply the full pipeline to a hold‑out set of re‑phrased conflicting prompts generated via deterministic back‑translation; repeat the paired test.  
   - Verify that the effect‑size drop is **non‑significant (p ≥ 0.05)** (SC‑005).  
5. **Multiple‑comparison correction** – Apply **Benjamini‑Hochberg FDR** (α = 0.05) across the three hypothesis tests (primary, neutral, robustness). Adjusted p‑values are reported (SC‑004).  
6. **Correlation analysis** – Compute Pearson r between verifier scores (baseline & augmented) and human scores; require **r ≥ 0.5** (SC‑007).  

All calculations use `scipy.stats` and `statsmodels.stats.multitest`.

## 8. Power Analysis (Methodology)
Using G*Power (paired t‑test, α = 0.05, effect size d = 0.5), **N = 500** conflicting prompts yields power ≈ 0.85, and the combined neutral set raises overall power to **≈ 0.88**. Because we now evaluate the full 1 000 human‑annotated prompts, the study meets the conventional ≥ 0.80 threshold. The report will note the achieved power and, if the observed effect size is smaller (d < 0.3), recommend additional data collection.

## 9. Runtime & Memory Auditing (FR‑008, SC‑002, SC‑003, SC‑009)
- `psutil` logs peak RAM for each stage; assert ≤ 7 GB.  
- Wall‑clock timers log duration of parser, baseline inference, augmented inference, and analysis; total ≤ 6 h.  
- **Baseline verifier runtime** recorded separately and must be **≤ 2 h**; otherwise the pipeline aborts and the limitation is reported (SC‑009).  

## 10. Decision / Rationale (CPU vs GPU)
The 1B Edit‑R1 model in float32 exceeds the 7 GB RAM limit on pure CPU, so inference scripts request **CPU‑only 8‑bit quantization**, which reduces RAM usage to a level that fits within the free‑tier constraints without any GPU fallback.

## 11. Deliverables
- `data/raw/*.parquet` (original InstructPix2Pix shards)  
- `data/raw/provenance.json` (checksums and source metadata)  
- `data/results/curated_prompts.csv` (prompt text + synthetic scores + conflict label)  
- `data/results/human_validation.csv` (human ratings for 1 000 prompts)  
- `data/results/graphs/*.json` (constraint graphs)  
- `data/results/baseline_scores.csv` (baseline verifier scores for the 1 000 human‑scored prompts)  
- `data/results/augmented_scores.csv` (graph‑augmented + control conditions)  
- `analysis/report.json` (full statistical summary, runtime, memory, correlation, correction method)  
- `analysis/report.csv` (human‑readable summary for the paper)  

All files conform to the schemas defined in `contracts/evaluation_report.schema.yaml`.

## 12. Ethical & Reproducibility Notes
- Human annotation data are stored under `data/results/human_validation.csv` with SHA‑256 checksums recorded in the project state file.  
- All randomness seeded (`numpy.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`).  
- Synthetic conflict generation is **not** used for evaluation; only the real conflict set is evaluated (fulfilling FR‑010).  

## 13. Verification
```bash
pytest tests/contract/test_evaluation_report.py
```
All contract tests must pass before CI marks the job successful.

---

