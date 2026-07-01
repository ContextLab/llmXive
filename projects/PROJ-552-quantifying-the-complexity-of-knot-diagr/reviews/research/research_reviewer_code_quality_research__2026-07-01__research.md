---
action_items:
- id: 716f740427af
  severity: writing
  text: Split code/analysis/model_fitting.py into code/analysis/model_fitting.py (fitting/metrics),
    code/analysis/residual_analysis.py (deviation logic), and code/analysis/plotting.py
    (visualization). Ensure each file is under 200 lines.
- id: bc41dab8feb2
  severity: writing
  text: Consolidate code/analysis/complexity_visualization.py, code/analysis/complexity_visualization_examples.py,
    and code/analysis/complexity_visualization_runner.py into a single code/analysis/visualization.py.
- id: abe734033c5c
  severity: writing
  text: Consolidate code/analysis/composite_metric*.py files into a single code/analysis/metrics.py.
- id: cd5b1bf2b2dc
  severity: writing
  text: Add PEP 484 type hints to all functions in the refactored analysis modules
    and verify with mypy --strict.
- id: e769634c1a06
  severity: writing
  text: Create tests/unit/test_model_fitting.py and tests/unit/test_residual_analysis.py
    to cover the split logic.
artifact_hash: 51f67afe33d622bdbc591f959097eeaa2314cfd198e275168461b1e145921cfa
artifact_path: projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/010-quantifying-the-complexity-of-knot-diagr/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-01T07:53:29.883816Z'
reviewer_kind: llm
reviewer_name: research_reviewer_code_quality_research
score: 0.0
verdict: minor_revision
---

The project demonstrates strong modularity in its data loading and validation layers (`code/download/`, `code/data/`). However, the analysis layer exhibits significant code quality issues that threaten reproducibility and maintainability, specifically regarding file size and separation of concerns.

**1. Truncation Risk and Modularity Violation**
The file `code/analysis/model_fitting.py` (14,650 bytes) is excessively large for a single module. Based on the task list (T032-T034), this file appears to conflate model fitting logic, residual analysis, goodness-of-fit metric calculation, and potentially plotting or reporting logic. This violates the "split this file" guidance in the review constraints. A single file of this size in the analysis core is prone to truncation during implementation and makes unit testing difficult.
*   **Action**: Split `code/analysis/model_fitting.py` into:
    *   `code/analysis/model_fitting.py`: Pure model fitting (Linear, Polynomial, Logarithmic) and metric calculation (R², AIC, BIC, MAE).
    *   `code/analysis/residual_analysis.py`: Logic for identifying families deviating ≥ 2 SD (T034).
    *   `code/analysis/plotting.py`: All figure generation logic (T023, T033).
    *   `code/analysis/model_reporting.py`: Logic for generating the markdown/JSON reports for these models.
    Each resulting file should be < 200 lines.

**2. Inconsistent Module Structure**
The `code/analysis/` directory contains a proliferation of single-purpose or overlapping files (e.g., `complexity_visualization.py`, `complexity_visualization_examples.py`, `complexity_visualization_runner.py`, `composite_metric.py`, `composite_metric_entropy.py`, etc.). This fragmentation suggests a lack of cohesive design. While modularity is good, this specific pattern indicates "micro-modularization" that hinders navigation.
*   **Action**: Consolidate the `complexity_visualization*` files into a single `code/analysis/visualization.py` with clear function separation. Similarly, consolidate the `composite_metric*` files into `code/analysis/metrics.py`.

**3. Missing Type Hints in Core Logic**
While T083 and T084 in `tasks.md` mandate PEP 484 type annotations, the provided code summary does not confirm their presence in the large analysis files. The `code/analysis/model_fitting.py` file, being the core of the statistical analysis, must have strict type hints for all public functions to ensure correctness and reproducibility.
*   **Action**: Run `mypy --strict code/analysis/model_fitting.py` (and the split files) and fix all errors. Ensure return types for regression results and input types for knot records are explicitly defined.

**4. Test Coverage Gaps**
The `tests/unit/` directory structure is implied but the specific test files for the refactored analysis modules (e.g., `test_model_fitting.py`, `test_residual_analysis.py`) are not clearly visible in the summary. T086 and T087 require these tests.
*   **Action**: Ensure `tests/unit/test_model_fitting.py` and `tests/unit/test_residual_analysis.py` exist and cover the split logic.

**Required Changes**
- Split `code/analysis/model_fitting.py` into `code/analysis/model_fitting.py` (fitting/metrics), `code/analysis/residual_analysis.py` (deviation logic), and `code/analysis/plotting.py` (visualization). Ensure each file is under 200 lines.
- Consolidate `code/analysis/complexity_visualization.py`, `code/analysis/complexity_visualization_examples.py`, and `code/analysis/complexity_visualization_runner.py` into a single `code/analysis/visualization.py`.
- Consolidate `code/analysis/composite_metric*.py` files into a single `code/analysis/metrics.py`.
- Add PEP 484 type hints to all functions in the refactored analysis modules and verify with `mypy --strict`.
- Create `tests/unit/test_model_fitting.py` and `tests/unit/test_residual_analysis.py` to cover the split logic.
