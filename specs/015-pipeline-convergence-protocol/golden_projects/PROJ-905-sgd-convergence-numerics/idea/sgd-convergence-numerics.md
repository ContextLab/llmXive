# Idea — Numerical convergence rate of stochastic gradient descent on smooth strongly-convex objectives (mathematics)

Research question: For smooth strongly-convex objectives, does the asymptotic O(1/T) convergence rate of SGD with decaying step size η_t = c/t hold under finite-sample averaging at T ∈ {10², 10³, 10⁴, 10⁵}?

Hypothesis: The empirical convergence rate matches the theoretical 1/T asymptote within constants of 2x; the empirical multiplicative constant depends sub-linearly on the condition number κ in the small-κ regime.

Methods: Implement SGD on a battery of synthetic strongly-convex quadratics with varying κ ∈ {1, 10, 100}; measure ||x_t - x*|| over 1000 sample paths; fit power-law convergence laws; report empirical constants vs. theoretical bounds.

Feasibility: theoretical / simulation project; no external data required. Implementable with free open-source libraries on a single CPU machine.
