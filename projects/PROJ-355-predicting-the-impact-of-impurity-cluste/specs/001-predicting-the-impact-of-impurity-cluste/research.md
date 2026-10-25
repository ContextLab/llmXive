# Research: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Executive Summary
We evaluate whether impurity‑clustering descriptors computed **on the bulk lattice (outside any grain‑boundary interface)** predict segregation energies **as recorded in published atomistic‑simulation datasets (EAM potentials)**. Bulk alloy records are sourced from the open OQMD dataset (Materials Project omitted due to lack of an unauthenticated open source on the free runner). Grain‑boundary supercells are built, impurities are inserted at the interface, and three **pre‑insertion bulk‑lattice** clustering descriptors (RDF peak, pair‑correlation, Voronoi count) are computed. Linear Regression (with robust SE p‑values) and RandomForest are trained under 5‑fold cross‑validation (or LOOCV if N < 5). Model selection follows a quantitative Ramsey RESET test (α = 0.05). VIF diagnostics (threshold ≥ 10, flagged at VIF = 10 per 2005.02245) are performed before any dimensionality reduction. A **Bonferroni** multiple‑comparison correction is applied to all coefficient tests. Power analysis (f² = 0.15, α = 0.05, target ≥ 0.80) follows Cohen’s medium‑effect‑size convention (Cohen, 1992) and includes a sensitivity note. All findings are **associational within the EAM‑potential physics**; no causal claims about experimental segregation are made.

## Dataset Strategy

| Required Variable | Source | Verified URL / Loader | Fit Check |
|-------------------|--------|----------------------|-----------|
| Bulk alloy compositions, spacegroup, `volume_per_atom` | OQMD | https://huggingface.co/datasets/jablonkagroup/oqmd/resolve/main/completion_0/test-00000-of-00001.parquet | ✅ Present; used to reconstruct bulk structures. |
| Segregation‑energy labels | GENERATED (EAM from literature) | N/A (generated in‑house) | ✅ Generated from published EAM potentials; provenance recorded. |
| Structural covariates (misorientation angle, boundary plane, strain, atomic radius, electronegativity) | Derived from bulk/GB geometry & standard elemental tables | N/A (computed) | ✅ Computed from the same bulk/GB records; no external download required. |

**Dataset‑variable fit verdict**: All predictor and target variables required by the functional requirements are obtainable from the OQMD records (after reconstruction) and from the in‑house EAM extraction. No external gated dataset is needed.

## Methodology & Statistical Rigor

- **Model choice (FR‑004a/b, FR‑010)**: A Ramsey RESET test (α = 0.05) determines whether the linear specification is adequate. If the test rejects linearity, RandomForest is used; otherwise Linear Regression (OLS) with robust standard errors is the primary model.  
- **Multiple comparisons (FR‑005/SC‑003)**: **Bonferroni** correction is applied whenever >1 coefficient is tested. Adjusted p‑values and the count of predictors whose significance (α = 0.05) changes are saved in `results/hypothesis_report.json`.  
- **Power analysis (FR‑008)**: `statsmodels.stats.power.FTestPower` with effect size f² = 0.15 (medium per Cohen, 1992), α = 0.05, **7 predictors** (3 descriptors + 4 structural covariates). Required N and achieved N are reported; any shortfall is logged honestly. A brief sensitivity note records that if the observed effect size differs markedly, the power analysis will be re‑evaluated.  
- **Significance of R² (SC‑001)**: Permutation testing for the held‑out test set (≥1 000 permutations, seeded) – per‑system R² for ≥3 alloy systems.  
- **Collinearity (FR‑007/FR‑012/SC‑004)**: VIF computed on the three raw descriptors before any PCA; VIF ≥ 10 (including exactly 10 per 2005.02245) triggers the JSON collinearity report. No predictors are removed; relationships are described qualitatively.  
- **Causal framing**: The study is observational/computational; all statements are explicitly associational.  
- **Uncertainty (SC‑002)**: Linear model prediction intervals are obtained from `statsmodels` (95 % CI); RandomForest intervals are derived via bootstrap quantiles (implemented in `train_model.py`).  
- **Permutation test for coefficients (FR‑014)**: For each regression coefficient, ≥1 000 label permutations generate an empirical p‑value, reported alongside the analytic p‑value.  

## Computational Feasibility

- **CPU‑only**: EAM relaxation of modest GB supercells (≤ 200 atoms) runs in seconds‑minutes; a full set of ≥200 configurations completes well within the 6 hour runner limit.  
- **Memory/Disk**: OQMD dataset is streamed via `datasets` (arrow format) and only a sampled subset is held in memory. All intermediate files are < 7 GB total.  
- **Libraries**: All dependencies have CPU wheels; no GPU needed.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use **Bonferroni** correction | Deterministic, satisfies FR‑005, avoids nondeterminism. |
| Omit Materials Project download | No open, unauthenticated MP endpoint is available on the free runner; the requirement is formally **waived** (Constitution VI). |
| Generate segregation energies with **validated EAM potentials** | No open literature dataset of segregation energies is directly downloadable; generating from published EAM potentials satisfies FR‑003 while preserving provenance. |
| Record `[DATA_UNAVAILABLE]` for any permanent download failure | Aligns with FR‑001 retry policy and provides transparent logging. |
| Ensure `.gitignore` and `README.md` contents (see `quickstart.md`) | Satisfies T001b/T001c verification requirements. |
| Validate `download_mp.py` exits cleanly with a waiver note | Satisfies T013 while acknowledging Materials‑Project omission. |
| Perform VIF before any dimensionality reduction | Directly satisfies FR‑007/FR‑012; flagged VIF ≥ 10 reported as required. |
| Clarify scientific validity of descriptor timing | Descriptors are computed on the bulk lattice only, addressing the reviewer’s concern. |
| Add quantitative linearity test (Ramsey RESET) | Addresses reviewer concern about subjective visual assessment. |
| Add structural covariates (misorientation angle, boundary plane, lattice strain, atomic radius, electronegativity) | Controls for known GB geometry effects (methodology‑c28c62e6). |
| Scope Limitation (Associational Claim) | All reported relationships reflect how the **EAM‑derived physics** links bulk clustering descriptors to segregation energies. No inference is made about real experimental segregation behavior. |

## Expected Outputs
- `data/processed/training_set.csv` – schema‑validated regression dataset (no `cluster_size` column).  
- `results/metrics.json` – CV metrics, per‑system R², power analysis, collinearity report, linearity assessment, preprocessing counts, and provenance metadata.  
- `results/hypothesis_report.json` – raw & Bonferroni‑adjusted p‑values, significance‑change count, free‑text summary.  
- `results/cluster_size_vs_segregation.png` – per‑alloy‑system figure (uses post‑insertion `cluster_size` **only for illustration**).  
- `.gitignore` and `README.md` (contents shown in `quickstart.md`).  

---===
