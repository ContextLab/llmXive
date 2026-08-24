# Research Strategy: Dataset Construction and Statistical Analysis Plan

## 1. Overview

This document defines the dataset strategy and statistical analysis plan for the llmXive follow-up project, extending "Self-Improving Language Models with Bidirectional Evolutionary Search". It explicitly details the data sources, scaling methodology, and the statistical framework (TOST, t-test, z-test) required to validate the hypothesis that symbolic-guided evolutionary search outperforms neural-verifier baselines in solving logic puzzles.

## 2. Dataset Strategy

### 2.1 Dataset Source: Synthetic Curation + Scaling Generation

The project utilizes a **Synthetic Curation** approach combined with **Scaling Generation**. We do not rely on static, pre-existing datasets (e.g., GSM8K, MATH) as they do not support the required systematic complexity scaling (N=10..500) for asymptotic analysis (SC-005).

Instead, we generate a custom dataset of logic puzzles using the `code/dataset/generator.py` module. This generator creates two primary puzzle types:
1. **Sudoku Variants**: Grid-based constraint satisfaction problems where complexity scales with grid size (N) and the number of pre-filled cells.
2. **Constrained Pathfinding**: Graph traversal problems where complexity scales with the number of nodes (N) and the density of constraints (obstacles, required waypoints).

**Provenance and Curation:**
* **Source ID**: `curated_logic_v1`
* **Generation Method**: Algorithmic generation via `PuzzleGenerator` class.
* **Verification**: Every generated instance is passed through `code/dataset/verifier.py`, a deterministic Python script that validates the existence of a unique solution and checks constraint satisfaction.
* **Fail-Loudly Principle**: If the generator fails to produce a valid puzzle within the maximum attempt limit, or if the verifier detects an internal error, the process halts immediately. No synthetic fallback or mock data is permitted.
* **Metadata**: Every puzzle file includes a JSON header with `source_id`, `generation_seed`, `timestamp`, and `generator_version` to ensure full reproducibility.

### 2.2 Scaling Method

To satisfy SC-005 (Scalability), the dataset is generated across a continuous complexity range:
* **Range**: N = 10 to N = 500.
* **Steps**: The generator accepts a list of N values (e.g., `--n 10 20 50 100 200 500`) to create distinct batches.
* **Complexity Metric**: For each puzzle, a `complexity_metric` is calculated based on the problem size (N) and constraint density. This metric is used as the X-axis in log-log regression analysis to determine the computational complexity class (e.g., O(N), O(N^2)).
* **Sample Size**: The pilot run targets N=10..50 with a small count (e.g., 10 per N) to profile runtime. The full scaling experiment targets N=10..500 with sufficient samples (N=50..100 per N) to ensure statistical power.

## 3. Statistical Analysis Plan

### 3.1 Experimental Design

We compare two experimental conditions:
1. **Experimental Group (Symbolic)**: BES loop guided by the `code/symbolic/planner.py` for sub-goal decomposition.
2. **Control Group (Neural Baseline)**: BES loop guided by a small pre-trained LLM (`distilbert-base-uncased`) as a neural verifier.

Both groups are run on the **exact same subset** of puzzles to ensure baseline equivalence (T055a).

### 3.2 Statistical Framework

The analysis adheres to a pre-registered statistical framework defined in `data/processed/pre_registration.yaml`.

#### 3.2.1 Primary Test: Two-Proportion Z-Test
* **Hypothesis**: The success rate of the Symbolic group ($p_1$) is greater than the Neural group ($p_2$).
* **Null Hypothesis ($H_0$)**: $p_1 = p_2$
* **Alternative Hypothesis ($H_1$)**: $p_1 > p_2$ (One-tailed) or $p_1 \neq p_2$ (Two-tailed, depending on pre-registration).
* **Significance Level ($\alpha$)**: 0.05
* **Implementation**: `code/analysis/stats.py::two_proportion_z_test`

#### 3.2.2 Equivalence Testing (TOST)
* **Purpose**: To verify that the Neural baseline is not *inferior* beyond a specific margin, or to test if the Symbolic approach is equivalent in speed while being superior in accuracy.
* **Method**: Two One-Sided Tests (TOST) for equivalence.
* **Implementation**: `code/analysis/stats.py::tost_equivalence_test`
* **Equivalence Margin ($\Delta$)**: Defined in pre-registration (e.g., $\Delta = 0.05$ for success rates).

#### 3.2.3 Power Analysis
* **Pre-Analysis**: Before running the full experiment, `code/analysis/stats.py::pre_analysis_power_check` calculates the required sample size to achieve a power of 0.80 given an expected effect size (Cohen's h). If the planned sample size is insufficient, a critical warning is logged (T067), but execution proceeds as per project assumptions.
* **Post-Hoc**: After the experiment, `code/analysis/stats.py::calculate_power_z_test` computes the achieved power based on the observed effect size and sample size. If power < 0.8, the final report flags the result as "Underpowered" (T049a).

#### 3.2.4 Complexity Class Derivation
* **Method**: Log-log linear regression on `complexity_metric` (X) vs. `duration` (Y).
* **Tool**: `scipy.stats.linregress`
* **Criterion**: If $R^2 < 0.85$, the complexity class is labeled 'UNKNOWN'. Otherwise, the slope determines the class (e.g., slope $\approx 1 \rightarrow O(N)$).
* **Comparison**: Slopes of Symbolic vs. Neural solvers are compared to determine which approach scales better.

## 4. Data Integrity and Reproducibility

* **Random Seeds**: All generation and sampling steps use `code/utils/seed.py` to ensure reproducibility. The seed is recorded in the metadata of every artifact.
* **Validation Gates**:
 * `data/processed/distribution_validation.json`: Verifies the dataset distribution matches the intended ratio.
 * `data/processed/validation_gate.json`: Final pass/fail status before analysis.
* **Manifest**: A `MANIFEST.md` is generated containing hashes of all input data, code, and configuration files, along with the git commit hash and Python environment version.

## 5. References

* **Project Plan**: `plan.md`
* **Specification**: `spec.md`
* **Data Model**: `data-model.md`
* **Contracts**: `contracts/dataset.schema.yaml`, `contracts/output.schema.yaml`