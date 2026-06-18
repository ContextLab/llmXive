# Innovative Modeling Strategy

The project now includes a **geometry‑inspired regression model** that leverages
the hyperbolic volume of a knot complement as a predictor for crossing number
and braid length.  This model goes beyond standard linear, polynomial, and
logarithmic fits by incorporating a topologically meaningful invariant.

Implementation details can be found in `code/analysis/regression.py` where the
function `geometry_inspired_regression` fits a regression using the hyperbolic
volume together with traditional features.  Effect‑size metrics (Cohen's d,
partial η²) are reported alongside standard R² and RMSE values.

The approach demonstrates a **topological‑machine‑learning hybrid**: the
geometric invariant is treated as a learned feature within a scikit‑learn
pipeline, enabling the model to capture non‑linear relationships rooted in knot
theory.

