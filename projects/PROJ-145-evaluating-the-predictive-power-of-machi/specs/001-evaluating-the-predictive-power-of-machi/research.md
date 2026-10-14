# Research: Evaluating the Predictive Power of Machine Learning for Identifying Novel High‑Entropy Alloy Compositions

## Executive Summary
The study investigates whether simple compositional descriptors (atomic radius, electronegativity, VEC, melting point) enable accurate prediction of formation energy for high‑entropy alloys (HEAs) and whether model‑derived uncertainty metrics reliably flag compositions outside the training manifold. Because no **verified open dataset** containing the required thermodynamic columns is available (see Data‑Availability Gap), the pipeline proceeds with a placeholder CSV bundled with the repository. All conclusions are therefore conditional on the placeholder data; a formal scope revision is recommended to replace it with a truly open HEA dataset.

### Methodological Highlights
* **Candidate Generation** – iterative random sampling from a curated “Top 30 HEA elements” list, filtered against a *Local Proxy Index* built from the placeholder data.  
* **Descriptor Computation** – weighted means & variances via `pymatgen`; variances clamped to 1e‑6.  
* **Modeling** – Random Forest & Gradient Boosting regressors trained with **5‑fold cross‑validation** (the cross‑fold count is fixed to 5 per the verified fact from 2604.10702).  
* **Uncertainty Calibration** – ensemble variance + convex‑hull distance; Spearman rank correlation (FR‑007).  
* **Statistical Rigor** – Mann‑Whitney U test for error‑distribution shift (FR‑006); multiple‑comparison correction is unnecessary because only two independent tests are performed.  
* **DFT Validation** – optional; if runtime exceeds 1 h per candidate, the report contains the required “unvalidated assumption” statement per Principle VI.

## Dataset Strategy
| Role | Source (Verified?) | URL | Format | Variables Needed |
|---|---|---|---|---|
| **Training / Hold‑out** | Placeholder CSV (bundled) | *none* (internal file) | CSV | `composition_id`, `elements`, `formation_energy`, `mixing_enthalpy` |
| **True Novel Index** | Same placeholder (used to build Local Proxy Index) | *none* | CSV | composition hash for existence check |
| **Reference for VEC** | **NO verified source** | – | – | – |
| **Other descriptors** | `pymatgen` internal tables (version‑pinned) | – | – | atomic radius, electronegativity, VEC, melting point |

*Variable Fit*: The placeholder CSV includes all columns required by FR‑001 and FR‑003. No external API is called, satisfying the CI runner constraints.

*Gap Statement*: Because the original specification called for static Parquet files from Materials Project / AFLOW (which lack a verified URL), we cannot guarantee that the placeholder data faithfully represents the full HEA chemical space. This limitation is explicitly noted in the final report.

## Methodological Rationale
1. **CPU‑First Design** – Random Forest / Gradient Boosting are trivially CPU‑tractable; no GPU is required.  
2. **Cross‑Validation** – 5‑fold CV (as per verified fact) provides robust interpolation performance estimates.  
3. **Uncertainty Metrics** – Ensemble variance is a native by‑product of tree ensembles; convex‑hull distance offers an orthogonal geometric proxy.  
4. **Statistical Tests** –  
   * *Mann‑Whitney U* (FR‑006) compares error distributions without assuming normality.  
   * *Spearman* (FR‑007) quantifies monotonic relationship between variance and hull distance; performed only if ≥ 10 novel samples exist.  
5. **Descriptor Traceability** – All descriptor calculations use `pymatgen` version pinned in `requirements.txt`, satisfying Principle VII.  

## Risks & Mitigations (re‑iterated)
* **Missing verified HEA data** – Scope revision request; placeholder used only for demonstration.  
* **Rate‑limit / API reliance** – Not applicable (local index only).  
* **Numerical instability** – Variance clamping to 1e‑6.  
* **Insufficient novel samples** – If `<10`, Spearman test is omitted and noted.  

---
