# Research: llmXive Follow-up: Dynamic Socio-Cognitive State Injection

## 1. Research Question
Does the explicit injection of dynamically inferred socio‑cognitive state signals into an LLM mediator’s context significantly increase consensus gap closure in high‑emotion, culturally diverse conflict scenarios compared to static prompting?

## 2. Dataset Strategy

### Verified Datasets
| Dataset | Source URL | Variables Needed | Fit Verification |
|---------|------------|------------------|------------------|
| **SoCRATES Evaluation Suite** | `https://huggingface.co/datasets/SoCRATES/socrates-eval` | `conflict_type`, `ideal_resolution`, `dialogue_prompts`, plus generated `emotional_reactivity` & `cultural_identity` metadata | **Verified** – the suite provides prompts and ideal resolutions. Trajectories with the required metadata are **synthesized** by running the prompts with seeded attribute values (see Section 3.1). |

### Variable Mapping
- `emotional_reactivity` – generated numeric score (0‑1) used for oversampling (FR‑001).  
- `cultural_identity` – list of tags used for oversampling (FR‑001).  
- `dialogue_history` – raw text fed to the state classifier (FR‑002).  
- `ideal_resolution` – ground‑truth summary for the consensus‑gap evaluator (FR‑005).  

### Availability & Feasibility
- **Download**: `datasets.load_dataset("SoCRATES/socrates-eval", streaming=True)` (streaming avoids RAM overload).  
- **Synthesis**: `src/data/generate_trajectories.py` creates **120 trajectories**, guaranteeing ≥40 % high‑difficulty cases (T015).  
- **Storage**: Raw prompts → `data/raw/socrates_prompts.parquet`; generated trajectories → `data/processed/filtered_trajectories.jsonl` (checksummed).  

## 3. Methodology

### 3.1 Data Generation (FR‑001)
1. Load SoCRATES prompts.  
2. For each seed, set `emotional_reactivity` ∈ [0.6, 1.0] **or** assign at least one `cultural_identity` tag from a high‑diversity list.  
3. Run the SoCRATES pipeline to obtain a dialogue history.  
4. Store the trajectory with metadata.  
5. After generation, compute oversampling statistics; abort if high‑difficulty proportion < 40 % (T015).  

### 3.2 Train/Test Split (addressing scientific_soundness‑b2402598)
- **Task T018** randomly partitions the 120 generated trajectories into a **classifier‑training set** (≈ 72 trajectories) and an **experiment set** (≈ 48 trajectories).  
- The classifier is trained only on the training split; the experiment set is used exclusively for mediation runs, eliminating any data‑leakage between predictor and outcome.

### 3.3 State Classifier (FR‑002)
- **Features**: TF‑IDF of the last *N* turns (default N = 3).  
- **Labels**: Derived from `conflict_type` or a rule‑based mapping to `escalating`, `cultural‑friction`, `neutral`.  
- **Model**: Scikit‑learn `LogisticRegression(solver='lbfgs')`.  
- **Training**: [deferred] train / [deferred] hold‑out split **within** the classifier‑training set (random seed 42).
- **Confidence Threshold**: 0.7 (configurable). Below threshold → `neutral‑monitoring`.  
- **Feature Independence Audit** (T020b): Verify that none of the TF‑IDF tokens encode the numeric `emotional_reactivity` or `cultural_identity` values.  

### 3.4 Experiment Execution (FR‑003, FR‑004)
- **LLMs**: quantized GGUF models (e.g., `llama-3-8b`, `mistral-7b`, etc.) loaded via `transformers` with `device="cpu"` and `load_in_8bit=True`.  
- **Conditions**:  
  - *Static*: Base system prompt + optional generic instructions.  
  - *Adapter*: Base prompt + dynamic instruction generated from the classifier’s `state_label` and `injection_instruction`.  
- **Loop** (implemented in `runner.py` – T027):  
  1. For each trajectory → **randomly shuffle** the order of the two conditions (Adapter, Static) to avoid order effects.  
  2. Run classifier.  
  3. If `confidence ≥ threshold` → inject corresponding instruction; else inject `"monitor the conversation neutrally"` (neutral‑monitoring).  
  4. Call the LLM; capture output, inference time, and status.  
  5. Log all fields per `experiment_log.schema.yaml`.  
  6. On timeout or crash → exponential back‑off retry (max 3 attempts); if still failing, log `status="skipped"` and exclude from analysis, with a count reported in `scope_adjustments.json`.  

### 3.5 Evaluation (FR‑005)
- **Metric**: `consensus_gap_score = 1 - cosine_similarity( embed(LLM_output), embed(ideal_resolution) )`.  
- **Embedding Model**: `sentence‑transformers/all‑MiniLM‑L6‑v2` (CPU‑friendly).  
- **Independence**: The evaluator uses only semantic embeddings; it never accesses classifier outputs or state labels. Audited in T033b.  

### 3.6 Statistical Analysis (FR‑006, FR‑007)
1. **Paired Difference**: For each trajectory & model, compute `Δ = gap_adapter – gap_static`.  
2. **Normality**: Shapiro‑Wilk on the set of Δs (per model). Record p‑value.  
3. **Test Selection**:  
   - If `p_normality > 0.05` → paired t‑test on **logit‑transformed** gap scores (logit avoids boundary compression).  
   - Else → Wilcoxon signed‑rank test.  
4. **Multiple‑Comparison**: Apply Holm‑Bonferroni across the 8 models.  
5. **Primary Report**: Includes `mean_gap_adapter`, `mean_gap_static`, `diff_mean`, `test_type`, `p_value`, `corrected_p_value`, `effect_size`, `is_significant`.  
6. **Neutral‑Monitoring Inclusion**: All adapter runs, including neutral‑monitoring, are **included** in the primary paired test (per Constitution VII). A **post‑hoc sensitivity analysis** (T050) repeats the test on the subset where `confidence ≥ threshold` to check robustness.  

### 3.7 Throughput & Feasibility (SC‑003)
- **Task T051** measures average inference time and trajectories per hour per model; expected on the order of tens of seconds per call → on the order of a few hours total wall‑clock on the CI runner, satisfying the compute budget.

## 4. Compute Feasibility & Rationale
| Method | Platform | Rationale |
|--------|----------|-----------|
| Logistic Regression | CPU | Trains in < 30 s on 72 samples; negligible RAM. |
| 8‑bit GGUF LLMs | CPU (no CUDA) | Quantized models ≈ 2 GB; fit within 7 GB RAM limit. |
| MiniLM sentence‑transformer | CPU | < 200 MB; inference < 10 ms per sentence. |
| Streaming dataset load | CPU | Avoids > 7 GB RAM usage for SoCRATES prompts. |

All steps are **CPU‑first**; no GPU escape hatch is required.

## 5. Assumptions & Limitations
- **Synthetic Trajectories** faithfully emulate real conflict dialogue; any domain‑shift is acknowledged.  
- **8‑bit Quantization** retains sufficient mediation quality; if a model fails to load, it is excluded from the study (recorded in `scope_adjustments.json`).  
- **Neutral‑Monitoring** may dilute effect size; sensitivity analysis (T050) quantifies this.  
- **Power** is based on a medium effect size (Cohen's d = 0.5) with required minimum N = 25 per paired test (source: 2511.14546). Our experiment set (≈ 48 trajectories per model) exceeds this threshold, ensuring ≥ 0.80 power for medium effects.  

---

