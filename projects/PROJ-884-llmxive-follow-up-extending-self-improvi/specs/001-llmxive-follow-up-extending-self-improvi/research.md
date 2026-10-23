# Research Strategy: Dataset Construction, Symbolic Planner, and Statistical Analysis

## 1. Overview
This document details the data generation pipeline, symbolic planning approach, and the statistical framework required to evaluate whether a symbolic‑guided Bidirectional Evolutionary Search (BES) can match or exceed a neural‑verifier baseline on logic/arithmetic puzzles.

## 2. Dataset Construction

### 2.1 Generation Approach
- **Synthetic Curation**: Puzzles are generated algorithmically to guarantee deterministic verification scripts. No external dataset is required, satisfying the CI data‑availability constraint.
- **Puzzle Types**  
  1. **Sudoku Variants** – grid size `N×N` (e.g., 4×4, 9×9). Complexity score = `N`.  
  2. **Constrained Pathfinding** – rectangular grid with obstacles; complexity score = number of nodes `N`.
- **Scaling**: The generator accepts a list of `N` values (e.g., `10 20 50 100 200 500`). For each `N` it creates `M(N)` puzzles (default `M=20` for pilot, `M=80` for full run) to ensure sufficient power for the McNemar’s test.
- **Determinism**: A global seed (default `42`) is stored in each puzzle’s JSON header (`generation_seed`). The same seed reproduces identical puzzles.

### 2.2 Verification Scripts
Each puzzle receives a Python file `verifier_<puzzle_id>.py` exposing a function:

```python
def verify(solution: str) -> tuple[bool, str]:
    """
    Returns (is_valid, error_code). error_code is "valid" or one of:
    - "PARSE_FAILURE"
    - "CONTRADICTION_DETECTED"
    - "INVALID_PATH"
    """
```

The verifier:
- Parses the solution string (≤ 100 ms).  
- Checks every constraint defined in the puzzle’s formal language.  
- Returns a specific error code on failure.

All verifiers are stored under `data/raw/verifiers/` and are immutable (Principle III).

## 3. Symbolic Planner

### 3.1 Parser
`code/symbolic/parser.py` translates the formal constraint string into an abstract syntax tree (AST). Parsing errors raise `ParseFailure`.

### 3.2 Planner
`code/symbolic/planner.py` walks the AST to produce an ordered list of sub‑goals (e.g., “fill row 1”, “place number 5 in column 3”). If constraints are contradictory, `ContradictionDetected` is raised. The planner returns either:
- `sub_goals: list[dict]` on success, or
- raises one of the two exception types, which the BES controller catches to log exclusion (FR‑006).

## 4. Evolutionary Search (BES)

### 4.1 Forward Step (CPU LLM)
- Uses a small pretrained language model (`gpt2`) in `transformers` with `torch` CPU backend.  
- Input: current population + planner‑generated sub‑goals.  
- Output: candidate solution strings formatted for the verifier.

### 4.2 Backward Step (Symbolic)
- Calls `SymbolicPlanner.decompose(puzzle.constraints)` to obtain sub‑goals.  
- If an exception occurs, the puzzle instance is recorded as **symbolic failure** and excluded from the symbolic run (FR‑006). Excluded instances are counted as failures (success = 0) in the final success‑rate calculation to keep denominators comparable.

## 5. Statistical Analysis Plan

All analysis code lives in `code/analysis/stats.py`.

### 5.1 Primary Metrics
- **Success Rate** = `valid_solutions / total_instances`.  
  *Both symbolic and neural runs use the same `total_instances`; excluded puzzles contribute zero successes to the symbolic denominator, preserving comparability.*  
- **Mean Wall‑Clock Time** per instance (seconds).  
- **Energy Estimate** (Joules) derived from CPU power draw (`Wattage ≈ 50 W` × wall‑clock seconds).

### 5.2 Hypothesis Tests
| Test | Null Hypothesis | Alternative | α (significance) |
|------|----------------|------------|------------------|
| **Paired McNemar’s test** (binary outcomes on matched instances) | `p_symbolic = p_neural` | `p_symbolic ≠ p_neural` (two‑tailed) | **0.0497** `[ref-alpha]` |
| **TOST Equivalence (success rate)** | `|p_symbolic - p_neural| ≥ Δ` | `|p_symbolic - p_neural| < Δ` (Δ = 0.05, pre‑registered) | 0.0497 |
| **Independent t‑test (CPU‑seconds)** | `μ_symbolic = μ_neural` | `μ_symbolic < μ_neural` (one‑tailed) | 0.0497 |

Implementation uses `statsmodels.stats.contingency_tables.mcnemar` for the paired test, `statsmodels.stats.proportion.proportions_ztest` for the TOST equivalence, and `scipy.stats.ttest_ind` for the t‑test.

### 5.3 Power Analysis
- **Pre‑analysis**: `pre_analysis_power_check(effect_size=Cohen_h, alpha=0.0497, power=0.80)` computes the required number of puzzle instances per complexity level. **If the required sample size is not met, the experiment aborts** and a report flags “insufficient power”.  
- **Post‑hoc**: `calculate_power_z_test` records achieved power for transparency.

### 5.4 Scalability Regression
- Log‑log linear regression on `complexity_score` vs. `mean_time`.  
- `R² ≥ 0.85` → accept slope as empirical complexity class; otherwise label “UNKNOWN”.

## 6. Reproducibility Measures
- **Seeds**: All random generators (`numpy`, `random`, `torch`) are seeded via `code/utils/seed.py`. The seed value is stored in `data/processed/metadata.json`.  
- **Manifests**: `MANIFEST.md` lists SHA‑256 hashes for every file in `data/raw/` and `code/`.  
- **Environment**: `requirements.txt` pins exact library versions; CI installs from this file each run.

## 7. References
- Project Plan: `plan.md`  
- Specification: `spec.md`  
- Alpha value for two‑proportion Z‑test (used also for McNemar’s test): **0.0497** `[ref-alpha]` (source: *Two‑proportion Z-test*, <https://en.wikipedia.org/wiki/Two-proportion_Z-test>)  

---

