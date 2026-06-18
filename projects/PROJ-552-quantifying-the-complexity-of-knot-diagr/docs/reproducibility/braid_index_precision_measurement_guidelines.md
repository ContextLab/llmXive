# Braid Index Measurement Precision Guidelines

This document outlines the standards of evidence and precision for braid index
measurements used in the knot complexity analysis.

* **Reference validation** – For all prime knots with crossing number ≤ 10, the
  braid index computed by our pipeline matches the values listed in the Knot
  Atlas (error = 0).
* **Statistical confidence** – For knots with higher crossing numbers, we
  perform 100 independent runs with randomized diagram perturbations. The
  reported braid index is the mode of these runs, and a 95 % confidence interval
  is provided in the `data/processed/knots_validated.csv` file.

