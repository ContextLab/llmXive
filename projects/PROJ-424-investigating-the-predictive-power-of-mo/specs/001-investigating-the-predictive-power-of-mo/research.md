# Research: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Summary

Quantify how accurately atomistic OPLS‑AA MD simulations predict experimental self‑diffusion coefficients of water, ethanol, and acetone at 1 ns, 5 ns, and 10 ns, producing timescale‑accuracy curves (MAE vs. duration) with 95 % bootstrap confidence bands, descriptive trend analysis, and a **descriptive paired‑comparison** (no formal p‑value) that reports a granularity limitation for the low‑seed regime.

## Dataset Strategy

| Dataset | Source / Path | Access Method | Validation |
|---|---|---|---|
| Experimental benchmarks | `data/raw/nist_refs.json` (committed, manually curated) | `json.load()` via `code/data/loader.py` | Schema‑validated; checksummed under `data/` (Constitution III). |
| MD trajectories | `data/raw/simulations/{solvent}_{duration}ns_seed{seed}.xtc` (generated in‑house) | `mdtraj.load()` | MSD linear fit R² ≥ 0.95 **and** log‑log slope ≈ 1 gate (Constitution VI, FR‑003). |

**Data availability note**: the "# Verified datasets" block contains no dataset relevant to solvent self‑diffusion coefficients (the listed NIST URLs cover an AI‑risk framework CSV, conversational data, and LLM‑leaderboard details). Per the spec's assumption (§4), experimental values are therefore manually curated into `nist_refs.json` — no external dataset URL is cited or fabricated. No synthetic fallbacks are used (spec §7).

## Methodological Approach

### 1. Simulation Protocol
- **Engine/force field**: OpenMM (CPU platform, 2 threads) with OPLS‑AA parameters.
- **System**: On the order of a few hundred molecules per solvent (approximately a few thousand atoms)., identical box size across all durations to avoid a size/timescale confound.
- **Ensemble**: NPT, T = 300 K (matched to reference data temperature in `nist_refs.json`), P = 1 bar, Langevin dynamics (friction = 1 ps⁻¹), Monte Carlo barostat.
- **Durations**: 1 ns, 5 ns, 10 ns. **Seeds**: 3 per condition for 1 ns and 5 ns, 1 seed for 10 ns (total number of trajectories), seeded constants in `code/`.
- **Protocol per run**: energy minimization → 0.1 ns equilibration → production with positions saved every 1–5 ps.

### 2. Diffusion Coefficient Extraction (FR‑002, FR‑003)
- MSD computed with `mdtraj` over the production trajectory (all molecules, unwrapped coordinates).
- Discard the first **0.1** of trajectory time (ballistic/sub‑diffusive regime); fit MSD(t) with ordinary least squares over the remaining window.
- **Convergence diagnostics**: (a) linear‑fit **R² ≥ 0.95**; (b) log‑log MSD vs. time slope must be **≈ 1 ± 0.05**. Both criteria must be met; failures flagged `convergence_failed`.
- Apply the **Yeh‑Hummer finite‑size correction** to the raw diffusion coefficient:
  \[
  D_{\text{corr}} = D_{\text{raw}} + \frac{k_{\mathrm{B}}T\,\xi}{6\pi\eta L}
  \]
  where \(L\) is the cubic box length, \(\eta\) the viscosity (taken from literature), and \(\xi≈2.837297\). This corrected value is used for all downstream error metrics (addresses methodology‑93d1bb0a).
- *D* = corrected slope / 6 (Einstein relation).

### 3. Accuracy & Uncertainty (FR‑004, FR‑008)
- Per‑seed absolute error \(|D_{\text{sim}} - D_{\text{exp}}|\); MAE per solvent × duration.
- **Bootstrap: a sufficiently large number of iterations** (resampling per‑seed errors with replacement, seeded RNG). 2.5th/97.5th percentiles form the 95 % CI (SC‑003). No automatic iteration reduction; any pipeline wall‑clock exceeding 5.5 h is logged and reported as a performance issue (FR‑004).
- **Descriptive paired‑comparison** (replaces the originally specified paired‑bootstrap test): for each solvent we compare the MAE at 1 ns vs. 10 ns using the same seed set. Because N = 3 (or 1 for 10 ns), the test cannot yield a conventional p‑value; instead we report a `granularity_note` indicating the minimal achievable two‑sided p‑value (relatively low) and present the observed mean difference with its bootstrap‑derived CI. This satisfies SC‑005 in a descriptively honest way (methodology‑37736ec4, scientific_soundness‑d99c1a89).

### 4. Sensitivity Analysis (US2)
- Vary the MSD start‑fraction (0.1, 0.2, 0.3) while keeping all other parameters fixed.
- For each combination compute the diffusion coefficient and its variance across seeds; report `variance_pct`. The analysis is stored in `data/processed/sensitivity_report.json` and validated against `contracts/sensitivity_report.schema.yaml`. This directly addresses US2’s methodological‑rigor requirement.

### 5. Timescale‑Accuracy Curves & Trend Analysis (FR‑008)
- Per solvent: MAE vs. duration (1, 5, 10 ns) with 95 % bootstrap confidence bands (SC‑001).
- Descriptive trend analysis: monotonicity of MAE with duration, CI overlap between consecutive durations, and the granularity‑aware paired comparison result (SC‑004, SC‑005).

## Decision Rationale

| Decision | Reasoning |
|---|---|
| **CPU‑first, OpenMM** | Small OPLS‑AA boxes run on the 2‑core CI runner; the spec states no GPU is required. No GPU escape hatch needed. |
| **Seed matrix (m × m × 2 + 1)** | Keeps total wall‑clock within the 6 h budget while providing multiple seeds for the short durations where variance is highest. Power limitation with N = 3 (or 1) is explicitly acknowledged and CIs are reported rather than relying solely on a p‑value. |
| **Bootstrap with exactly 1000 iterations** | Mandated by FR‑004; cost is negligible (vectorized numpy over ≤21 error values). The iteration count is justified by the functional requirement, not by external citation (plan‑consistency‑3c3e4fc1). |
| **Finite‑size correction** | Addresses the systematic under‑estimation of *D* in small boxes (methodology‑93d1bb0a, scientific_soundness‑cb3468b9). |
| **Sensitivity analysis** | Provides robustness validation for the 0.1 start‑fraction choice (methodology‑d8b3c3f8), fulfilling US2. |
| **Descriptive paired‑comparison with granularity note** | Prevents reporting a misleading p‑value given the tiny seed count (methodology‑37736ec4, scientific_soundness‑d99c1a89). |
| **Fallback for zero accepted seeds** | Guarantees that the pipeline never crashes; null MAE/CI entries are recorded with an explanatory note (methodology‑73d790a2). |
| **Additional convergence diagnostic (log‑log slope)** | Strengthens the R² gate, acknowledging its limited discriminating power (scientific_soundness‑0d39462a). |

## Limitations & Power Considerations (methodology‑9348a9bc)

- With only 3 seeds (1 seed for 10 ns), bootstrap confidence intervals are highly degenerate; the 95 % CI may span a narrow range that reflects sampling noise rather than true uncertainty. All interpretations explicitly note this limitation.
- The descriptive paired‑comparison cannot achieve a conventional significance threshold; the `granularity_note` clarifies the minimal achievable p‑value is relatively low (i.e., on the order of a modest magnitude). and advises cautious interpretation.

---

