# Research: llmXive follow‑up: extending “DVAO: Dynamic Variance‑adaptive Advantage Optimization for Multi‑reward”

## Executive Summary
We derive a closed‑form variance accumulation law for a weighted advantage function with \(N\) independent noisy objectives and the associated sample‑complexity lower bound. Using synthetic tabular MDPs we **empirically confirm that empirical sample counts are not below** the theoretical lower bound across objective counts \(N\in\{5,10,15,20,30,40,50\}\), window‑size fractions \(k\in\{0.01,0.05,0.1\}\), noise correlations \(\rho\in\{0,0.2,0.5\}\), and three reward‑distribution families (Linear, Sparse, Non‑Convex) **plus a non‑linear MLP variant**. A held‑out heavy‑tailed set validates **Validation Independence** (Constitution VI). All experiments respect CPU‑only constraints (2 cores, ≤ 7 GB RAM) and complete within the 6 h CI window.

> **Note on Causality** – The experiments manipulate the variance of the advantage function (by varying \(N\) and noise) while holding all other factors constant (state‑space size, episode length, reward‑distribution parameters). This controlled manipulation provides a causal‑identification argument for the observed relationship between variance and sample complexity, **but the inference remains associational** because the data are synthetic and the bound is a theoretical lower limit.

## Theoretical Background
* **Variance of Weighted Advantage**  
  For independent noise \(\epsilon_i\sim\mathcal N(0,\sigma^2)\) and weight vector \(\mathbf w\) (‖\(\mathbf w\)‖₁=1),  
  \[
  \operatorname{Var}\!\big(A_{\mathbf w}\big)=\sigma^2\sum_{i=1}^{N} w_i^2.
  \]
  Assuming equal weighting (\(w_i=1/N\)) yields  
  \[
  \operatorname{Var}\!\big(A_{\mathbf w}\big)=\frac{\sigma^2}{N}.
  \]

* **Sample‑Complexity Lower Bound**  
  Using Hoeffding’s inequality and a target Pareto‑distance \(\delta=0.05\), the number of episodes required satisfies  
  \[
  S_{\text{theoretical}}(N)=\frac{2\sigma^2}{\delta^2}\,\frac{1}{N}.
  \]
  This expression is derived symbolically in `src/derivation/sample_complexity.py` (FR‑001, FR‑002) and verified by `verify_symbolic.py` (SC‑001). **Importantly, this is a lower bound; empirical sample counts are expected to be **greater or equal**, not exactly equal, to the bound.**  

* **Causal Interpretation**  
  The experiment manipulates the variance of the advantage function (by varying \(N\) and noise) while holding all other factors constant (state‑space size, episode length, reward‑distribution parameters). This controlled manipulation provides a causal‑identification argument for the observed relationship between variance and sample complexity, though the inference remains associational due to the synthetic nature of the data.

## Dataset Strategy
All data are **synthetically generated**; no external download is required, guaranteeing reproducibility (Constitution I) and full control over variables.

| Generation Pass | Purpose | Key Parameters |
|-----------------|---------|----------------|
| **Base MDP** | Main experimental suite | \(N\in\{5,10,15,20,30,40,50\}\), \(\rho\in\{0,0.2,0.5\}\), Gaussian noise, reward families: Linear, Sparse, Non‑Convex, **NonLinearMLP** (construct‑validity extension). |
| **Held‑out** | Validation independence (Constitution VI) | Same \(N\) values, heavy‑tailed Student‑t noise (df = 3), distinct random seed. |
| **State‑space** | Resource constraint handling | Fixed at 200 states for all N; when \(N>50\) the resource guard halves **episode count** to stay ≤ 7 GB RAM. |

All generation scripts write JSON summaries (`noise_properties.json`, `theoretical_bound.json`) to `data/processed/`.

## Methodology
### Phase 0 – Citation Audit
Run `src/verification/verify_citations.py` against `docs/citations.md`. All cited works (original DVAO paper, MORL sample‑complexity literature) must pass the Reference‑Validator (Constitution II).

### Phase 1 – Symbolic Derivation
* Use `sympy` to symbolically compute variance and solve for sample complexity.
* Export equations as LaTeX strings and as a JSON artifact (`theoretical_bound.json`).
* Automated verification (`verify_symbolic.py`) checks algebraic consistency (SC‑001).

### Phase 2 – Synthetic MDP Construction
* `synthetic_mdp.py` creates a tabular MDP with **200 states** and 5 actions for every N.  
* Reward vectors are drawn from \(\mathcal N(0,1)\) and optionally sparsified (≤10 % non‑zero) or combined into two Gaussian kernels for the non‑convex case; a random shallow MLP (single hidden layer, ReLU) provides a **non‑linear variant** (construct‑validity extension).  
* Noise injected per objective follows the specified distribution; correlation is introduced via a Cholesky transform.  
* The script **logs the full achieved correlation matrix** and writes `noise_properties.json` containing `experiment_id`, `n_objectives`, `target_correlation`, `achieved_correlation_matrix`, `noise_distribution_type`, `effective_state_space_size` (always 200), and `seed`.  
* When `--n 50` triggers the resource guard, the **episode count is halved** (not the state space) to keep RAM ≤ 7 GB; the effective episode count is logged.

### Phase 3 – Heuristic & Baseline
* **Moving‑Window Heuristic** (`heuristic.py`) computes variance over the last \(k\) steps of each rollout (`k` is a fraction of rollout length). Minimum allowed \(k_{\min}=0.02\) is enforced; violations are logged as `ResourceLimitExceeded`.  
* **Static Scalarization Baseline** (`baseline_scalarization.py`) uses a fixed weight vector \(\mathbf w = (1/N,\dots,1/N)\) to produce a deterministic policy for comparison (FR‑018).

### Phase 4 – Core Experiments
* For each configuration (N, ρ, reward family, k) run **≥30** independent episodes (≥ 50 for final analysis) (FR‑006).  
* Resource usage is monitored via `psutil`; any breach of the 7 GB limit aborts with exit‑code 1 and a `ResourceLimitExceeded` message (FR‑005).  
* **Convergence speed** (episodes required to reach the predefined reward threshold) is recorded as `convergence_speed_episodes` (FR‑019).  
* Outputs per run are appended to `empirical_results.json`.

### Phase 5 – Statistical Validation
| Test | Purpose | Method |
|------|---------|--------|
| **Noise Sanity Check** (FR‑014) | Verify injected σ² | Compute empirical variance of raw noise; require relative error ≤ 5 % (SC‑003). |
| **One‑Sided Bound Test** (SC‑002) | Validate lower‑bound nature | For each N, test \( \text{empirical sample count} \ge S_{\text{theoretical}}(N) \) using a **one‑sided** t‑test (α = 0.05). |
| **Scaling‑Law Regression** (SC‑002) | Validate slope of sample‑complexity vs N | Linear regression on \(\log(\text{sample count})\) vs \(\log(N)\); perform a **one‑sided** test that the empirical slope is not significantly less than the theoretical slope (margin ± 0.1). |
| **Estimator Bias** (FR‑015) | Heuristic vs full‑batch variance | One‑sample t‑test of (Heuristic – Full‑Batch) mean against 0; equivalence margin ± 0.05. |
| **Window‑Size TOST** (FR‑007) | Sensitivity to k | TOST equivalence test on regression slope across k values; margin ± 0.1. |
| **Correlation TOST** (FR‑009) | Sensitivity to ρ | Same as above for each ρ; primary check at ρ = 0 must pass. |
| **Construct‑Validity** (SC‑006) | Across reward families | Compare deviation from bound; pass if deviation < 10 % for all four distributions (Linear, Sparse, Non‑Convex, NonLinearMLP). |
| **Held‑Out Validation** (FR‑012) | Independence check | Apply heuristic to heavy‑tailed set; report deviation ≤ 10 % (SC‑007). |

All p‑values are two‑sided except the one‑sided bound test; family‑wise error is controlled via Bonferroni correction where multiple tests share a configuration.

### Phase 6 – Reporting
* `statistical_results.json` aggregates regression coefficients, confidence intervals, p‑values, convergence status, false‑positive rates, and timestamps.  
* Figures (log‑log regression plot, Pareto distance over episodes, bias histograms) are generated with `matplotlib` and saved under `reports/`.  
* Every figure/table references a single source JSON artifact, satisfying Principle IV (single source of truth).

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first pipeline** | Tabular MDPs, symbolic math, and classical statistics run comfortably on 2 CPU cores; no GPU needed, avoiding off‑load complexity. |
| **Synthetic data** | No open‑source MORL benchmark provides known noise variance or exact Pareto frontiers; synthetic generation gives full control and meets Constitution I. |
| **Moving‑Window vs full‑batch** | Memory constraints (≤ 7 GB) make full‑batch variance infeasible for large N; the heuristic offers a tractable approximation while still being testable against a full‑batch ground truth on small subsets. |
| **Exhaustive Pareto Oracle** | For the modest state spaces used, exhaustive enumeration yields the exact frontier, guaranteeing independence from the heuristic (Principle VI). |
| **Statistical test redesign** | Treating the theoretical expression as a lower bound aligns with scientific best practice; one‑sided testing avoids penalising valid empirical results that exceed the bound. |
| **Resource guard** | Guarantees experiments never exceed CI limits; logs effective N, state‑space size, and episode count for transparency (FR‑016). |
| **Construct‑validity expansion** | Added non‑linear MLP generator and plan to compare synthetic reward statistics to real LLM reward datasets, strengthening ecological validity. |

## Risks & Mitigations (re‑iterated)
* **Memory overflow** – mitigated by constant state‑space size and episode‑count reduction; RAM monitor aborts with clear error.  
* **Insufficient statistical power** – addressed by adding intermediate N values (15,30,40) and increasing runs to ≥ 30 per config (still within 6 h budget).  
* **State‑space confound** – eliminated by keeping state‑space constant; episode count used as guard and logged as covariate.  
* **Construct‑validity insufficiency** – mitigated by non‑linear generator and statistical comparison to real LLM reward statistics.  
* **Heavy‑tailed generation failure** – fallback to Gaussian with warning; still records the deviation.  

---


