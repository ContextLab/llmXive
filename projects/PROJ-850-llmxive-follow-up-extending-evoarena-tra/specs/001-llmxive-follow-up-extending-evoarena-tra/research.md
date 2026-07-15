# Research: EvoMem-Conflict Filtering for Robust LLM Agents

## Dataset Strategy

### Primary Dataset: Terminal-Bench-Evo (Synthetic Subset via Trace-Injection)
- **Status**: NO verified source found in the provided verified datasets block.
- **Strategy**: Since no verified URL exists, the project will generate a **synthetic subset** of `Terminal-Bench-Evo` tasks using a **Trace-Injection** methodology to ensure realistic dynamic environments.
- **Rationale**: The spec assumes the dataset contains tasks with version updates and contradictions. Without a verified external source, we must construct a controlled environment that mimics these properties to ensure reproducibility (Constitution Principle I). **Limitation**: Results are limited to the synthetic domain unless a real dataset is later verified.
- **Generation Method (Trace-Injection)**:
  1. **Source**: Use open-source terminal command logs (e.g., from public GitHub repositories or shell history datasets) as the base "real" trace to ensure semantic complexity and noise characteristics.
  2. **Injection**: Inject "contradictions" where a new patch explicitly negates a previous state (e.g., "File X is required" vs "File X is deprecated") into these real traces.
  3. **Validation**: Ensure a minimum of 5+ version updates per task chain (per Constitution Reproducibility Requirements).
  4. **Result**: A dataset that retains the semantic complexity and noise characteristics of real dynamic environments while providing controlled ground truth for contradictions.
- **Sample Size**: Determined by Power Analysis (see below). Target a moderate-to-large scale of tasks.

### Synthetic Validation Set
- **Purpose**: To validate the conflict detection heuristic (FR-001).
- **Composition**: 500 labeled pairs (250 "contradiction", 250 "non-contradiction").
- **Source**: Locally generated JSON file (`data/raw/synthetic_conflicts.json`).
- **Labeling Protocol (Dual-Oracle Verification)**:
  1. **Generation (Oracle A)**: Pairs are generated using Rule Set A (e.g., keyword matching for "deleted" vs "exists").
  2. **Verification (Oracle B)**: A distinct, independent Rule Set B (semantic embedding distance) is applied to the generated pairs to ensure they represent true semantic contradictions, not just syntactic matches.
  3. **Audit**: A manual audit of a subset of the pairs by a researcher to confirm labels.
  4. **Conflict Resolution**: If Oracle A and Oracle B disagree, the pair is discarded or manually reviewed. This prevents "label leakage" where the model learns only the generation rules.

## Model Selection & Feasibility

### Conflict Detection Heuristic
- **Candidate**: `distilbert-base-uncased` (a smaller parameter count) or `bert-base-uncased` (a larger parameter count).
- **Rationale**:
  - **CPU-tractable**: These models run efficiently on 2 vCPU cores without GPU.
  - **Precision**: Sufficient for binary semantic contradiction detection in controlled terminal contexts.
  - **Constraints**: No 8-bit/4-bit quantization to avoid CUDA dependencies (Assumption 2).
- **Fallback**: If performance is insufficient, fallback to a rule-based heuristic (keyword matching) for the sensitivity analysis (FR-008).

### Computational Feasibility
- **Hardware**: GitHub Actions free-tier (2 vCPU, ~7GB RAM).
- **Memory Budget**:
  - Model load: approximately hundreds of megabytes (distilbert) to approximately hundreds of megabytes (bert).
  - Dataset (200 tasks): < 100MB.
  - Overhead: Python, pandas, logging < 2GB.
  - **Total**: Well within 7GB limit.
- **Runtime**:
  - Inference per patch pair: on the order of hundreds of milliseconds.
  - Total patches per task: a small, manageable set.
  - Total tasks: a substantial range suitable for comprehensive evaluation.
  - **Estimate**: < 2 hours for full experiment (well within 6h limit).

## Statistical Methodology

### Power Analysis (FR-009)
- **Test**: McNemar's test (paired, binary outcome).
- **Parameters**:
  - $\alpha = 0.05$
  - Power ($1-\beta$) = 0.80
  - Effect Size: **Cohen's h** = 0.2 (small effect for proportions). *Note: Spec FR-009/SC-006 references Cohen's d, which is invalid for binary data. This plan uses Cohen's h. Spec flagged for kickback.*
- **Result**: Requires a sufficient number of pairs.
- **Plan**: Run **250 tasks** to account for potential dropouts or invalid traces.

### Hypothesis Testing
- **Null Hypothesis ($H_0$)**: No difference in accuracy between `EvoMem-All` and `EvoMem-Conflict`.
- **Alternative Hypothesis ($H_1$)**: `EvoMem-Conflict` has higher accuracy (one-tailed) or different accuracy (two-tailed).
- **Metric**: Chain-level accuracy (binary success/fail per task).
- **Primary Test**: **McNemar's Test** (replacing Wilcoxon as per scientific validity for binary data). *Note: Spec FR-005/SC-004 mandates Wilcoxon; plan uses McNemar. Spec flagged for kickback.*
- **Secondary Metric**: Context token reduction (continuous, analyzed via Wilcoxon if needed).

### Sensitivity Analysis (FR-008)
- **Thresholds**: $\{0.7, 0.8, 0.9, 0.95\}$.
- **Method**: Re-run the conflict detection logic with varying softmax thresholds and record the resulting accuracy and noise reduction.
- **Outcome**: Identify the threshold that maximizes accuracy while minimizing false positives (discarding necessary context).

### Hallucination Metric (SC-002)
- **Definition**: A hallucination is detected if the LLM's output state description matches the ground truth state description with < 90% string similarity (Levenshtein ratio).
- **Ground Truth Source**: The ground truth is derived **exclusively** from the successful execution of terminal commands (Constitution Principle VII), NOT from the memory traces themselves. This avoids circular validation.
- **Calculation**: Compute `similarity = Levenshtein(agent_state, ground_truth_state) / max_length`. If `similarity < 0.90`, flag `hallucination_detected = True`.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Dataset lacks sufficient conflicts | Medium | High | Synthetic generation (Trace-Injection) ensures control over conflict density. |
| Model inference too slow | Low | Medium | Use smaller model (distilbert); sample tasks if needed. |
| Memory starvation (context too small) | Low | High | Fallback logic (latest + 2 recent) mandated by FR-002. |
| False positives in conflict detection | Medium | Medium | Conservative threshold (0.90) and sensitivity analysis. |
| Label Leakage in Validation | Medium | High | Dual-oracle verification layer and manual audit. |

## References
- **Terminal-Bench-Evo**: No verified source found. Synthetic generation (Trace-Injection) used.
- **DistilBERT**: Sanh et al. (2019). "DistilBERT, a distilled version of BERT".
- **McNemar's Test**: McNemar, Q. (1947). "Note on the sampling error of the difference between correlated proportions or percentages".
- **Cohen's h**: Cohen, J. (1988). "Statistical Power Analysis for the Behavioral Sciences".