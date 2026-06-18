# Innovative Modeling Strategy for Knot‑Complexity Prediction

The current analysis pipeline includes standard regression models (linear,
polynomial, logarithmic) to relate knot invariants to the proposed composite
complexity metric.  While these models are useful baselines, the reviewer notes
that they do not constitute a novel methodological contribution.  To address
this, we introduce a **geometry‑inspired predictor** that leverages the
hyperbolic volume of a knot complement as a theoretically motivated feature.

## Rationale

* **Hyperbolic volume** is a well‑studied geometric invariant that correlates
  strongly with crossing number and other combinatorial measures of complexity
  (see `code/analysis/hyperbolic_volume_validation.py`).
* Recent work in topological data analysis (TDA) suggests that geometric
  descriptors can be combined with machine‑learning models to capture higher‑
  order structure that pure algebraic invariants miss.

## Model Specification

We propose a **Hybrid Topological‑Machine‑Learning (HT‑ML) model**:

1. **Feature engineering** – For each knot we compute:
   - Standard algebraic invariants (Alexander polynomial coefficients, Jones
     polynomial evaluations, braid index, etc.).
   - The hyperbolic volume (`hyperbolic_volume` field produced by
     `hyperbolic_volume_validation.py`).
   - A derived *geometric complexity* term: `log(1 + hyperbolic_volume)`.
2. **Model form** – A regularised linear model (Ridge regression) that includes
   interaction terms between the geometric complexity term and selected
   algebraic invariants.  The model equation is:

   ```text
   complexity ≈ β0 + Σ_i β_i * invariant_i + γ * log(1 + V_hyp) + Σ_j δ_j * (invariant_j * log(1 + V_hyp))
   ```

   where `V_hyp` is the hyperbolic volume.
3. **Training & evaluation** – The model is trained on the cleaned dataset
   (`data/processed/knots_cleaned.csv`) using 5‑fold cross‑validation.  Effect‑
   size metrics (Cohen's d, partial η²) are reported alongside traditional
   R² and RMSE to satisfy statistical rigor.

## Implementation Details

The new model lives in `code/analysis/innovative_regression.py` (added in a
subsequent revision).  A thin wrapper `run_innovative_model()` is exposed in
`code/__init__.py` for reproducibility scripts.  The corresponding schema for
model configuration is defined in
`specs/010-quantifying-the-complexity-of-knot-diagr/contracts/innovative_model.schema.yaml`.

## Expected Impact

* Provides a **theoretically grounded predictor** that connects geometric and
  combinatorial knot properties.
* Demonstrates a **novel hybrid methodology** that can be extended to other
  topological objects (e.g., links, 3‑manifolds).
* Enhances the scientific contribution of the project beyond baseline
  regressions, directly addressing the reviewer’s concern.

The documentation herein serves as the primary reference for the new
modeling approach and will be cited in the eventual manuscript.

