# Research: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

## 1. Research Question & Hypothesis

**Question**: Can a Bidirectional Evolutionary Search (BES) framework, where the backward step is replaced by a deterministic symbolic planner, achieve comparable solution success rates to a learned neural-verifier baseline while significantly reducing computational overhead (CPU vs. GPU)?

**Hypothesis**: 
- **H1**: The symbolic-guided BES will achieve a success rate statistically equivalent (TOST p < 0.05 with pre-defined delta) to the learned neural-verifier baseline on logic/arithmetic puzzles.
- **H2**: The symbolic-guided BES will demonstrate a statistically significant reduction in computational cost (p < 0.05 for t-test) compared to the learned neural-verifier baseline, measured in wall-clock time and energy (Joules).
- **H3**: The symbolic planner will fail to decompose a small fraction of complex, non-linear constraints, which will be excluded from the symbolic-guided run (as per FR-006), without crashing the system. The rate of logical contradictions introduced by the planner will be measured as a distinct metric.

## 2. Dataset Strategy

**Dataset Source**: 
The project requires a curated dataset of logic and arithmetic puzzles (e.g., Sudoku variants, constrained pathfinding). 
- **Verified Source**: As of this planning stage, **no verified external dataset** containing the specific mix of logic puzzles with *deterministic Python verification scripts* and *formal constraint definitions* suitable for BES backward-step substitution was found in the "Verified datasets" block of the user message.
- **Strategy**: The dataset will be **synthetically curated** within the project (`data/raw/`). This aligns with FR-001, which mandates the system MUST curate such a dataset. The curation process will generate puzzle instances and corresponding Python verifier scripts programmatically to ensure [deferred] coverage of required variables (constraints, initial state, target state) and deterministic verification.
- **Scaling Generation**: To satisfy SC-005, the dataset generation will include a specific task to vary puzzle complexity (N) systematically (e.g., N=10, 20, 50, 100, 200, 500) to enable log-log regression for complexity class analysis.

**Dataset Variables**:
| Variable | Description | Source |
| :--- | :--- | :--- |
| `puzzle_id` | Unique identifier for the instance | Generated |
| `puzzle_type` | Category (e.g., "Sudoku-4x4", "Pathfinding-Grid") | Generated |
| `constraints` | Formal string representation of rules | Generated |
| `initial_state` | Starting configuration | Generated |
| `target_state` | Goal configuration | Generated |
| `verifier_script` | Path to deterministic Python script | Generated |
| `solution_path` | (Optional) Ground truth solution for validation | Generated |
| `complexity_score` | Numeric score (N) for scaling analysis | Generated |

**Dataset Fit**: 
The synthetic curation ensures that every variable required for the analysis (predictors: constraint complexity; outcome: solution validity; covariates: puzzle type) is present. This avoids the fatal flaw of relying on an external dataset that lacks necessary variables (e.g., missing formal constraint definitions).

## 3. Methodology & Statistical Rigor

### 3.1 Experimental Design
- **Conditions**: 
  1. **Symbolic-Guided BES**: Forward step = Small LLM (CPU); Backward step = Symbolic Planner.
  2. **Learned Verifier Baseline**: Forward step = Small LLM (CPU); Backward step = **Learned Verifier (DistilBERT)**. The baseline model will be **trained** on a subset of the synthetic puzzle dataset (train/val/test split) to learn the verification task, ensuring it is a true learned verifier and not a heuristic.
  - **Fallback Strategy**: If DistilBERT on CPU exceeds the 6-hour limit, the baseline will switch to **TinyBERT** or **DistilBERT with CPU-optimized quantization** (via `optimum`). This fallback is pre-registered to avoid a 'moving target'.
- **Procedure**:
  1. Generate/Curate N puzzle instances (N ≥ 500), including a scaling subset.
  2. Run BES loop for both conditions on the **full dataset**.
  3. Record success (valid solution found) and cost (time, energy) for each instance.
  4. **Stratified Analysis**:
     - **Subset A (Symbolic-Passable)**: Compare Symbolic Success vs. Neural Success.
     - **Subset B (Symbolic-Fail)**: Compare Symbolic Failure Rate (Exclusion) vs. Neural Success/Failure Rate.
  5. Measure 'Logical Contradiction Rate' for the symbolic planner (instances where planner generates contradictory sub-goals).

### 3.2 Statistical Analysis Plan
- **Success Rate Comparison (Equivalence)**: 
  - **Test**: **Two One-Sided Tests (TOST)** for equivalence.
  - **Null Hypothesis**: Success rates are different (outside the equivalence margin).
  - **Alternative**: Success rates are equivalent (within the pre-defined delta).
 - **Margin (Delta)**: Pre-registered (e.g., [deferred] difference).
  - **Correction**: If multiple puzzle types are analyzed separately, apply Bonferroni correction to maintain family-wise error rate.
- **Cost Comparison**: 
  - **Test**: Independent samples t-test (or Mann-Whitney U if non-normal).
  - **Metric**: Wall-clock time (seconds) and estimated energy (Joules, derived from CPU time and TDP).
  - **Correction**: Bonferroni if comparing multiple cost metrics.
- **Complexity Class (SC-005)**: 
  - **Method**: Log-log regression of computation time vs. complexity score (N).
  - **Output**: Slope (exponent) to determine complexity class (e.g., O(n^1), O(n^2)).
- **Power Analysis**: 
  - **Assumption**: Effect size (Cohen's h) of 0.3 (medium) for success rate difference.
  - **Alpha**: 0.05.
  - **Power**: 0.80.
  - **Required N**: ~175 per group (total ~350). We plan for N=500 to account for exclusions (FR-006).
  - **Acknowledgement**: If the actual effect size is smaller, power may be lower; this will be reported as a limitation.

### 3.3 Statistical Rigor Checklist
- **Multiple Comparisons**: Bonferroni correction applied if analyzing sub-groups (e.g., by puzzle type).
- **Sample Size**: Justified via power analysis (deferred exact N to implementation based on runtime profiling).
- **Causal Inference**: This is an observational comparison of two methods. Claims will be framed as "associational" regarding efficiency, not causal claims about "understanding" unless randomization of the method is strictly controlled (which it is, by design).
- **Measurement Validity**: Deterministic verifiers provide ground truth validity.
- **Collinearity**: If predictors (e.g., puzzle complexity) are correlated, descriptive statistics will be reported, and collinearity acknowledged.

## 4. Computational Feasibility (CPU-Only)

**Constraints**: 
- **Hardware**: GitHub Actions free-tier (2 CPU, ~7GB RAM, no GPU).
- **Time**: ≤ 6 hours per job.
- **Memory**: ≤ 6GB (safety margin).

**Mitigations**:
- **LLM Selection**: Use a small, CPU-optimized model (e.g., `distilbert-base-uncased` for embeddings, or a tiny decoder-only model like `TinyLlama` if available in CPU wheel, running in default precision). **No 8-bit/4-bit quantization** (requires CUDA).
- **Data Subset**: Process puzzles in batches. If memory is tight, stream data from disk.
- **Symbolic Planner**: Pure Python, rule-based, negligible memory/CPU overhead.
- **Verifier**: < 100ms execution per solution (as per spec).
- **Baseline**: The "Learned Verifier Baseline" will be implemented as DistilBERT trained on the synthetic data. **Fallback**: If DistilBERT is too slow, use TinyBERT or CPU-optimized quantization (via `optimum`).
- **Scaling**: The scaling dataset will be processed in smaller batches to avoid memory overflow.

**Decision**: The plan prioritizes CPU-tractability. If the full BES loop with a small LLM exceeds 6 hours, the population size or generations will be reduced (documented in `research.md` as a limitation).

## 5. Risk Management

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Symbolic Planner Failure** | High | Log exclusion (FR-006); analyze only successful cases; report exclusion rate. |
| **LLM Inference Too Slow** | High | Use smallest viable model; reduce population/generations; batch processing. |
| **Statistical Power Insufficient** | Medium | Report power analysis; interpret non-significant results cautiously; increase N if time permits. |
| **Dataset Curation Gap** | High | Synthetic generation ensures all variables are present; no reliance on external missing data. |
| **Runtime Exceeds 6h** | High | Profile early; implement early stopping; reduce complexity parameters; use fallback baseline. |
| **Baseline Infeasible** | High | Pre-registered fallback to TinyBERT or CPU-quantized model if DistilBERT fails pilot. |

## 6. Decision Rationale

- **Synthetic Dataset**: Chosen because no verified external dataset meets the specific requirement of "deterministic Python verification scripts" paired with "formal constraint definitions" for BES. This ensures FR-001 is met without fabricating URLs.
- **CPU-Only Execution**: Mandated by the target platform (GitHub Actions free-tier). GPU methods are excluded to prevent job failure.
- **TOST for Equivalence**: Standard for testing if two methods are equivalent within a margin, replacing the standard z-test which only tests for difference.
- **Bonferroni Correction**: Applied to control family-wise error rate if multiple hypothesis tests are performed (e.g., per puzzle type).
- **Pre-registered Fallback**: Ensures the experiment can complete even if the primary baseline is too slow, maintaining the 'neural' requirement.