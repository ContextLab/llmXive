# Research: llmXive follow-up: extending "Leveraging Verifier-Based Reinforcement Learning in Image Editing"

## Overview
This document details the experimental design, data acquisition, model execution, and statistical analysis that will produce the evidence required by the functional (FR‑*) and success‑criteria (SC‑*) specifications.

## 1. Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Raw prompts & images | InstructPixPix (3 public shards) | `datasets.load_dataset("parquet", data_files=URL, streaming=False)` | URLs are verified in the specification’s “Verified datasets” section. |
| Synthetic feasibility scores | Deterministic heuristic (see §2) | Generated locally after download | **Used only for conflict generation**, not for any evaluation metric. |
| Human feasibility validation | Crowdsourced annotation of **all prompts** (or a representative ≥200‑prompt sample) | `src/data/human_annotation.py` (writes `data/human_validation.csv`) | Provides the **independent ground‑truth** for alignment evaluation. |
| Conflict generation | Rule‑based augmentation of neutral prompts | `src/data/conflict_generator.py` creates numerous conflicting prompts | Guarantees a balanced set of genuine contradictions. |

*All downloads are performed programmatically on the CI runner; no manual steps are required.*

## 2. Synthetic Feasibility Scoring (FR‑001 – generation only)
1. **Neutral prompts** – Assigned a feasibility score of `1.0`.  
2. **Conflicting prompts** – Parse the instruction into atomic clauses; compute the proportion of clauses that are mutually compatible using an antonym‑lookup dictionary. The resulting score ∈ [0, 1] reflects “degree of partial compliance”.  
3. Store the scores in `data/curated_prompts.csv` with columns: `prompt_id`, `instruction_type`, `prompt_text`, `synthetic_score`.  

**Human Validation**: A **separate** annotation step (Section 1) collects human feasibility scores for each prompt. These human scores become the primary `human_score` column in `curated_prompts.csv`. If the Pearson correlation between synthetic and human scores is < 0.6, we will flag the synthetic heuristic and rely exclusively on human scores for all downstream analyses.

## 3. Baseline Verifier Evaluation (FR‑003)
- Load the distilled Edit‑R1 1B model from Hugging Face (`"llmxive/edit-r1-1b-distilled"`).  
- Run inference on each `prompt_text` **without** any graph context, using `torch.device("cuda")` if available (GPU escape hatch) or CPU otherwise.  
- Record the verifier’s alignment score (model output probability of “feasible” after softmax) as `verifier_score`.  
- Output `data/baseline_scores.csv` with columns: `prompt_id`, `verifier_score`, `human_score`, `alignment_delta = verifier_score - human_score`.  
  *Note: `alignment_delta` is computed **against the independent human_score**, never against the synthetic_score.*

## 4. Symbolic Constraint‑Graph Parser (FR‑002, Principle VI)
- **Tokenization & POS tagging** via spaCy (`en_core_web_sm`).  
- **Node extraction**: noun‑phrase chunks representing actionable principles (e.g., “sky”, “blue”).  
- **Temporal edges**: detect cue words (“first”, “then”, “after”) and add `temporal-precedes` edges.  
- **Contradiction edges**: use an antonym lexicon (WordNet) to flag pairs where one node’s adjective is an antonym of another’s (e.g., “blue” vs. “dark”).  
- Serialize each graph to JSON (`graph_id`, `nodes`, `edges`).  
- **Runtime budget**: ≤ 30 min on 2‑core CPU (validated via profiling).  
- **GPU usage**: No GPU memory is allocated; the parser runs strictly on CPU.  

**Parser Failure Policy**: Prompts for which graph construction fails are logged and **excluded** from the paired statistical test; a failure‑rate summary is reported.

## 5. Graph‑Augmented Verifier Evaluation (FR‑004)
- For each prompt, embed the corresponding graph JSON into the verifier’s prompt template under a `Context:` section.  
- **Control Conditions**:  
  1. **Random filler** – a JSON object of similar size containing unrelated key‑value pairs (no graph information).  
  2. **Empty graph** – `{}` context.  
- Run inference (GPU escape hatch if needed) and store results in `data/augmented_scores.csv` (same schema as baseline).  

## 6. Statistical Comparison (FR‑005, FR‑006, FR‑007)
1. **Primary test** – Paired comparison on the **conflicting** subset (`baseline_scores` vs. `augmented_scores`).  
   - Normality check (Shapiro‑Wilk).  
   - If normal → paired **t‑test**; else → **Wilcoxon signed‑rank**.  
   - Report **mean alignment‑score difference** (SC‑001) and **Cohen’s d** (or rank‑biserial).  
   - **Alignment delta** is computed against **human_score**, not synthetic_score.  
2. **Control comparison** – Same paired test between baseline and the random‑filler condition to ensure improvements are not due to token length or context size.  
3. **Robustness check** – Generate a hold‑out set of multiple re‑phrased conflicting prompts via back‑translation **and** a baseline set of numerous re‑phrased neutral prompts. Verify that back‑translation does not significantly change prompt length or lexical diversity (t‑test on token counts). Run full pipeline on both sets and repeat paired tests.  
4. **Effect‑size consistency** – Compare Cohen’s d between primary and hold‑out tests; require that the drop in effect size is not statistically significant (p ≥ 0.05). This satisfies SC‑005.  
5. **Multiple‑comparison correction** – Apply **Benjamini‑Hochberg FDR** (α = 0.05) across the three hypothesis tests (primary, control, robustness).  

All statistical calculations use `scipy.stats` and `statsmodels.stats.multitest`.

## 7. Power Analysis (Methodology)
Using G*Power (two‑tailed paired t‑test, α = 0.05, effect size d = 0.5), a sample of **N = 500** conflicting prompts yields power ≈ 0.86. If the observed standard deviation exceeds the assumption, we will increase to **N = 600** (still within the [deferred]‑prompt budget).

## 8. Runtime & Memory Auditing (FR‑008, SC‑002, SC‑003)
- Use `psutil` to log peak RAM usage for each stage; assert ≤ 7 GB.  
- Log wall‑clock time for parser, baseline inference, augmented inference, and analysis; ensure total ≤ 6 h.  

## 9. Decision / Rationale (CPU vs GPU)
The 1B Edit‑R1 model in float32 exceeds the 7 GB RAM limit on CPU. Therefore the inference scripts request a CUDA device; if unavailable on the free runner, the platform automatically offloads the job to a free Kaggle GPU (GPU escape hatch). The parser and all other components remain CPU‑only, satisfying Principle VI.

## 10. Deliverables
- `data/curated_prompts.csv` (prompt text + synthetic & **human** feasibility scores).  
- `data/conflict_generator.log` (record of synthetic conflict creation).  
- `data/constraint_graphs/*.json` (one graph per prompt).  
- `data/baseline_scores.csv`  
- `data/augmented_scores.csv` (including control runs).  
- `analysis/report.json` (p‑values, effect sizes, confidence intervals, runtime stats).  
- `analysis/report.csv` (human‑readable summary for paper).  

These files satisfy the contract schema defined in `contracts/evaluation_report.schema.yaml`.

---


## 11. Ethical & Reproducibility Notes
- Human annotation data are stored under `data/human_validation.csv` with SHA‑256 checksums recorded in the project state file.  
- All random processes are seeded (`numpy.random.seed(42)`, `torch.manual_seed(42)`).  
- The synthetic conflict generator is deterministic given the seed, ensuring reproducibility.

## 12. Independence Assurance
By using **human‑annotated feasibility scores** as the primary ground‑truth, the evaluation is independent of the rule‑based antonym lexicon that drives both the synthetic scores and the graph parser. This eliminates circular validation and yields a genuine assessment of whether graph‑augmented prompting improves real‑world alignment.


## 13. Verification
Run the contract tests to ensure schema compliance:
```bash
pytest tests/contract/test_evaluation_report.py
```
All tests must pass before the CI job is considered successful.

---


## 14. GPU Escape Hatch Note
If the runner reports `torch.cuda.is_available() == False`, the verifier scripts automatically switch to the Kaggle GPU escape hatch (the platform will re‑run the same command on a free GPU). No code changes are required; just ensure the `torch` and `transformers` versions support `device="cuda"`.


