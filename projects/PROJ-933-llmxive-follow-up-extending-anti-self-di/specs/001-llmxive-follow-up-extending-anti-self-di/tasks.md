# Tasks: llmXive follow-up: extending "Anti‑Self‑Distillation for Reasoning RL via Pointwise Mutual Information"

**Inputs**: spec.md, plan.md, data-model, contracts, reviewer feedback.

## Phase 0 – Project setup
- [ ] T001 [P] [US1] Project setup, pinned `requirements.txt`, `config/settings.yaml` (seed 2026, hyperparameters, 5‑hour timeout), `quickstart.md`, and pre‑study power analysis in `code/analysis/statistical_test.py` producing `results/pre_study_power.json` with `power >= 0.8` (d=0.5, α=0.05). Verified previously.

## Phase 1 – Data acquisition & preprocessing
- [ ] T003 [US1] **Data download & checksum**: download BigBench Hard and Ethics via `datasets.load_dataset(..., streaming=True)`, compute SHA256 checksums for each shard, write `data/raw/checksums.json`. Abort if download fails. Verification: `checksums.json` exists and matches downloaded files.
- [ ] T003b [US1] **Filter prompts**: retain only prompts with **≥ 3** rationales, write `data/raw/filtered_bigbench.parquet` conforming to `contracts/dataset.schema.yaml`. Log skipped prompt IDs to `logs/skipped_prompts.log`. Verification: parquet validates schema; summary in `logs/data_loader_summary.json` shows 0 prompts with <3 rationales.
- [ ] T003c [US1] **Privileged‑context split**: uniformly random sample exactly one rationale per prompt as privileged context `c` (seed 2026), re‑sample up to 5 times on collision, write `data/processed/context_split.jsonl`. No quality‑score stratification. Verification: each line contains `privileged_rationale_idx` distinct from others.
- [ ] T003d [US1] **End‑to‑end smoke run**: run a single training step on first 5 prompts to ensure pipeline works. Verification: script exits 0 and produces temporary logs.
- [ ] T002 [P] [US1] Unit tests for filtering, context split, JSD stability, gradient inversion, BLEU/similarity, and Wilcoxon located in `code/tests/`. Run after T003d. Verification: `pytest -q` returns 0.

## Phase 2 – Teacher logits generation
- [ ] T004 [US2] **Inference‑only teacher pass (per‑rationale)**: for every unselected rationale listed in `data/processed/context_split.jsonl`, run frozen `distilbert-base-uncased` model, record pre‑softmax logits vector. Write each entry to canonical path `data/teacher_logits_raw.jsonl` (schema `contracts/teacher_logits.schema.yaml`). Also write manifest `data/teacher_logits_raw.jsonl.manifest` with line count and SHA256. Verification: manifest line count equals total number of unselected rationales; each entry has non‑empty `teacher_logits`.

## Phase 3 – Training
- [ ] T005 [US2] **AntiSD training loop**: run custom PyTorch loop for **500** on‑policy steps per prompt (both AntiSD and StandardSD conditions), updating only the projection head, using per‑rationale teacher logits. Log fields required by `contracts/training_output.schema.yaml` (loss, js_divergence, gradient_dot_product, generated_trajectory, deliberation_count, deliberation_tokens, training_time_seconds, peak_memory_mb) to `data/results/training_run_<run_id>.jsonl`. Additionally, write per‑token entropy values to separate file `data/results/entropy_<run_id>.jsonl`. Verification: logs validate against schema; entropy file exists.
- [ ] T021 [US2] **Full trajectory log with token‑level probabilities**: during training, capture token‑level probability distribution for each step and write combined log to `outputs/trajectory_log.jsonl`. Verification: file exists and contains probability vectors.

## Phase 4 – Trajectory generation
- [ ] T006 [US3] **Generate 50 trajectories per prompt per condition**: sample from trained heads (temperature sampling) and store under `outputs/trajectories/` with filenames `outputs/trajectories/<prompt_id>_<condition>_traj_<idx>.jsonl`. Verification: exactly 50 files per prompt per condition.

## Phase 5 – Metric computation
- [ ] T007 [US3] **Compute metrics**:
  (i) Deliberation‑token frequency (list `["let's think","consider","however","wait"]`);
  (ii) Pairwise BLEU‑4;
  (iii) MiniLM‑L6‑v2 cosine similarity against unselected rationales;
  (iv) Human‑Evaluation‑Proxy = mean ROUGE‑L F1 against held‑out rationales;
  (v) Token‑level entropy (from T005 entropy file).
  Output CSVs `data/results/deliberation_freq.csv`, `.../bleu.csv`, `.../semantic_similarity.csv`, `.../rouge_l.csv`, `.../entropy.csv`. Verification: each CSV has rows for every prompt × condition.
- [ ] T018b [US3] **Derive rater‑score artifact for contract compliance**: map each ROUGE‑L F1 score to a 1‑5 Likert integer (ceil(5 * score)) and compute median, writing `data/results/human_eval_scores.csv` matching `contracts/output.schema.yaml`. Verification: file conforms to schema.

## Phase 6 – Statistical analysis
- [ ] T008 [US3] **Wilcoxon tests & effect sizes**: perform Wilcoxon signed‑rank tests for deliberation frequency, BLEU‑4, semantic similarity, ROUGE‑L quality, and entropy (five tests). Apply Benjamini‑Hochberg FDR correction across all five. Write `results/statistical_summary.json` with p‑values, statistics, Cliff’s δ, and corrected values. Verification: JSON matches `contracts/analysis_results.schema.yaml` (no extra fields).

## Phase 7 – Final report
- [ ] T009 [US3] **Assemble final report**: create `results/final_report.json` conforming to `contracts/analysis_results.schema.yaml` (includes sample_size, power_analysis, metrics per condition, wilcoxon_results). No additional fields. Verification: JSON validates against schema.

## Phase 8 – Success‑criteria validation
- [ ] T010 [US3] **Validate all success criteria**: script `code/validation/check_sc.py` reads artifacts and checks SC‑001–SC‑007 (including teacher‑logits checksum, runtime limits, numeric SC‑005 threshold, etc.). Outputs `results/sc_validation.json`. Verification: script exits 0.
- [ ] T014 [US1] **Define numeric threshold for SC‑005**: set `config/sc_thresholds.yaml` with `min_prompts_processed: 30`. Verification: script reads this value.

## Phase 9 – Reproducibility handoff
- [ ] T011 Document a concise methods/results account in `docs/results_summary.md` linking to `results/final_report.json` and figures in `results/plots/`.
- [ ] T012 Re‑run the documented workflow from `quickstart.md` on a fresh runner, record deterministic run log `results/repro_check.json`. Verification: log shows all tasks T001–T010 passed.
