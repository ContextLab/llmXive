# Research Strategy: Dataset Construction, Symbolic Planner, and Statistical Analysis

## 1. Overview
This document details the synthetic data generation pipeline, the symbolic planning approach, and the statistical framework required to evaluate whether a symbolic‑guided Bidirectional Evolutionary Search (BES) can match or exceed a neural‑verifier baseline on logic/arithmetic puzzles.

## 2. Dataset Construction

### 2.1 Generation Approach
- **Synthetic Curation**: Puzzles are generated algorithmically, guaranteeing deterministic verification scripts and eliminating the need for external gated datasets.  
- **Puzzle Types**  
  1. **Sudoku Variants** – grid size `N×N` (e.g., 4×4, 9×9). Complexity score = `N`.  
  2. **Constrained Pathfinding** – rectangular grid with obstacles; complexity score = number of nodes `N`.  
- **Scaling**: The generator accepts a list of `N` values (e.g., `10 20 50 100 200 500`). For each `N` it creates `M(N)` puzzles (default `M=20` for pilot, `M=80` for full run) to ensure sufficient power for the McNemar test.  
- **Determinism**: A global seed (default `42`) is stored in each puzzle’s JSON header (`generation_seed`). The same seed reproduces identical puzzles.  

### 2.2 Output Format
`generator.py` writes a **single JSON object**:

```json
{
  "puzzles": [
    { "puzzle_id": "...", "puzzle_type": "...", "constraints": "...", ... },
    ...
  ]
}
```

This matches the expectations of `tests/unit/test_generator.py`.

### 2.3 Verification Scripts
Each puzzle receives an immutable Python file `verifier_<puzzle_id>.py` exposing:

```python
def verify(solution: str) -> tuple[bool, str]:
    """
    Returns (is_valid, error_code). error_code is one of:
    "valid", "PARSE_FAILURE", "CONTRADICTION_DETECTED", "INVALID_PATH"
    """
```

The verifier parses the solution (≤ 100 ms) and checks every formal constraint, returning a specific error code on failure.

## 3. Symbolic Planner

### 3.1 Parser (`parser.py`)
Translates the formal constraint string into an abstract syntax tree (AST). Parsing errors raise `ParseFailure`.

### 3.2 Planner (`planner.py`)
Walks the AST to produce an ordered list of sub‑goals (e.g., “fill row 1”, “place number 5 in column 3”).  
- If constraints are contradictory, raises `ContradictionDetected`.  
- On success returns `List[Dict]` of sub‑goals; on failure the BES controller **logs the puzzle as a symbolic failure**, excludes it from the symbolic‑guided run, and increments `excluded_instances`.  
- The **planner feasibility rate** is computed as `1 - excluded_instances / total_instances` and reported separately (see Section 5.2).

## 4. Evolutionary Search (BES)

### 4.1 Forward Step (CPU LLM)
- Uses `transformers` with a small pretrained model (`gpt2`) on the CPU.  
- Input: current population + planner‑generated sub‑goals.  
- Output: candidate solution strings formatted for the deterministic verifier.

### 4.2 Backward Step (Symbolic)
- Calls `SymbolicPlanner.decompose(puzzle.constraints)`.  
- If an exception occurs, the puzzle is **logged as a symbolic failure** and omitted from the paired statistical analyses (see Section 5.2). Excluded instances are still counted in `excluded_instances` for reporting but do **not** contribute to success‑rate or cost comparisons.

## 5. Statistical Analysis Plan

All analysis lives in `code/analysis/stats.py`.

### 5.1 Primary Metrics
- **Success Rate** = `valid_solutions / (total_instances - excluded_instances)`.  
  *Only puzzles where the symbolic planner succeeded are included; this yields a conditional success rate.*  
- **Planner Feasibility Rate** = `1 - excluded_instances / total_instances`.  
- **Mean Wall‑Clock Time** per instance (seconds) – computed on the same matched set.  
- **Energy Estimate** (Joules) derived from CPU power draw (`≈ 50 W` × wall‑clock seconds).

### 5.2 Hypothesis Tests
| Test | Null Hypothesis | Alternative | α (significance) |
|------|----------------|------------|------------------|
| **Paired McNemar’s test** (binary outcomes on matched instances) | `p_symbolic = p_neural` | `p_symbolic ≠ p_neural` (two‑tailed) | **0.0497** (source: Two‑proportion Z‑test, https://en.wikipedia.org/wiki/Two-proportion_Z-test) |
| **TOST Equivalence (success rate)** | `|p_symbolic - p_neural| ≥ Δ` | `|p_symbolic - p_neural| < Δ` (Δ = 0.05) | 0.0497 |
| **Paired t‑test (CPU‑seconds)** | `μ_symbolic = μ_neural` | `μ_symbolic < μ_neural` (one‑tailed) | 0.0497 |

Implementation uses:
- `statsmodels.stats.contingency_tables.mcnemar` for McNemar.  
- `statsmodels.stats.proportion.proportions_ztest` for the TOST equivalence.  
- `scipy.stats.ttest_rel` for the paired t‑test.

### 5.3 Power Analysis
- **Effect size assumptions**:  
  - Success‑rate: Cohen’s h = 0.20 (small). Required matched sample size ≈ 200 per condition for 80 % power at α = 0.0497.  
 - CPU‑time: Cohen’s d = 0.50 (medium). Required matched sample size ≈ 64 for [deferred] power.
- **Pre‑analysis check**: `pre_analysis_power_check(effect_size_h=0.20, effect_size_d=0.50, alpha=0.0497, power=0.80)` computes required N. If the generated dataset does not meet these minima, the experiment aborts with a clear “insufficient power” message.  
- **Impact of exclusions**: Because exclusions reduce the matched sample, the effective N is recomputed after data collection; a **post‑hoc power report** is generated and included in `summary.json`.

### 5.4 Scalability Regression
- Log‑log linear regression on `complexity_score` vs. `mean_time`.  
- Acceptable fit: `R² ≥ 0.85`. The slope is interpreted as the empirical complexity class (e.g., O(n), O(n²)).

## 6. Reproducibility Measures
- **Seeds**: All RNGs (`numpy`, `random`, `torch`) are seeded via `code/utils/seed.py`. Seed stored in `data/processed/metadata.json`.  
- **Manifests**: `MANIFEST.md` lists SHA‑256 hashes for every file in `data/raw/` and `code/`.  
- **Environment**: `requirements.txt` pins exact library versions; CI installs from this file each run.

## 7. References
- Specification: `spec.md`  
- Alpha level for two‑proportion Z‑test & McNemar: **0.0497** (source: Two‑proportion Z‑test, https://en.wikipedia.org/wiki/Two-proportion_Z-test)  

---

