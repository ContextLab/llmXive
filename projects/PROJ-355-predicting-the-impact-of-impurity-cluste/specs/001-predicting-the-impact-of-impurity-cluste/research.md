# Research: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Executive Summary

We test whether impurity‑clustering descriptors computed in the interface region of grain‑boundary supercells predict segregation energies **within the EAM‑potential internal physics**. Real bulk‑alloy records are loaded from OQMD via the verified `datasets` loader; GB supercells are constructed with impurities at the interface; three clustering descriptors (RDF peak, pair‑correlation, Voronoi neighbor count) are computed **after EAM relaxation**; segregation‑energy labels are generated with validated EAM potentials for three alloy systems. Both Linear Regression (with coefficient p‑values) and RandomForest (FR‑004b) are trained under 5‑fold CV (LOOCV if N < 5); the primary model is selected by the FR‑010 linearity assessment. VIF diagnostics (threshold 10, per 2005.02245) run before any dimensionality reduction; multiple‑comparison correction (Bonferroni/FDR) is applied to coefficient p‑values; a power analysis (f² = 0.15, α = 0.05, power ≥ 0.80) is reported. FR‑011 validation against a DFT benchmark **cannot be performed** because no verified open benchmark exists; the harness will emit a `[DATA_UNAVAILABLE]` limitation record. All findings are therefore **associational** and do not imply causal physical mechanisms.

## Dataset Strategy

| Required Variable | Source | Verified URL / Loader | Fit Check |
|-------------------|--------|----------------------|-----------|
| Bulk alloy compositions, spacegroups, `volume_per_atom` | OQMD via `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")` — verified: a large set of records with fields name, formula, spacegroup, volume_per_atom, … | https://huggingface.co/datasets/jablonkagroup/oqmd/resolve/main/completion_0/test-00000-of-00001.parquet | ✅ Composition, spacegroup, and volume data present; ✅ Used to reconstruct bulk structures (see Methodology). |
| Alternative OQMD access points (same data, verified) | OQMD CSV / parquet | https://huggingface.co/datasets/kjappelbaum/chemnlp-oqmd/resolve/main/targets.csv ; https://huggingface.co/datasets/materials-toolkits/oqmd/resolve/main/all_index.parquet | ✅ Verified reachable |
| Segregation‑energy labels | GENERATED in‑house via EAM simulation (`simulate_energy.py`) | N/A (generated; sanctioned by FR‑011 "EAM‑derived segregation‑energy labels") | ⚠️ No verified open literature segregation‑energy database exists; generation path is explicit and provenance‑recorded |
| DFT benchmark for FR‑011 validation | **NO verified source found** | — | ❌ No verified open DFT benchmark is available; the validation harness will report `[DATA_UNAVAILABLE]` unless a verified source is added. No URL is fabricated. |

**Dataset‑variable fit verdict**: The verified OQMD loader supplies composition, spacegroup, and volume information (sufficient for prototype reconstruction). Segregation‑energy labels are generated via EAM; the lack of an external benchmark is explicitly noted (see above). The FR‑011 requirement is therefore **conditionally unmet** and reported as a limitation.

**Synthetic Structure Note**: The OQMD `raw_data` records do **not** contain atomic coordinates or explicit lattice parameters. To obtain structures usable for GB construction we **synthetically reconstruct** bulk crystals using `pymatgen.Structure.from_spacegroup`, deriving lattice constants from the provided `volume_per_atom`. This reconstruction is fully documented in `data/metadata.yaml` and cited to the originating OQMD record ID. While this satisfies the need for bulk configurations, it is a **deviation** from the spec’s literal “download bulk configuration files” wording; the limitation is recorded here.

## Methodology & Statistical Rigor

- **Model choice (FR‑004a/b, FR‑010)**: exploratory scatter plots and residual analysis decide the primary model. Linear Regression (statsmodels OLS with robust/HCE standard errors) provides coefficient p‑values; RandomForest provides a non‑linear comparator. Both run 5‑fold CV (LOOCV if N < 5) with a pinned split and GroupKFold grouping.
- **Multiple comparisons (FR‑005/SC‑003)**: Bonferroni when ≤20 coefficient tests, Benjamini‑Hochberg FDR otherwise; adjusted p‑values and the count of predictors whose α = 0.05 significance status changes are reported in `results/hypothesis_report.json`.
- **Power (FR‑008)**: `statsmodels.stats.power.FTestPower`‑style multiple‑regression power analysis with f² = 0.15 (medium, Cohen 1992), α = 0.05, **7 predictors** (3 descriptors + 4 covariates), target power ≥ 0.80; required minimum N computed at run time `[deferred]`; achieved N compared against it, with any shortfall logged honestly.
- **Significance of R² (SC‑001)**: permutation testing (pinned seed, ≥1000 permutations) on the held‑out test set; per‑system R² for ≥3 alloy systems.
- **Collinearity (FR‑007/FR‑012/SC‑004)**: VIF computed on the three raw descriptors BEFORE any PCA/dimensionality reduction; threshold VIF = 10 (source: 2005.02245, https://arxiv.org/abs/2005.02245); flagged groups reported descriptively with a one‑sentence summary — no independent‑effects claims for definitionally related predictors.
- **Causal framing**: the study is observational/computational; all claims are associational. No causal or moderation effect is claimed.
- **Measurement validity (FR‑011)**: EAM labels are validated against a DFT benchmark **only if** a verified benchmark becomes available; otherwise the limitation is recorded. No synthetic DFT stand‑in.
- **Uncertainty (SC‑002)**: [deferred] prediction intervals on held‑out predictions (linear model: statsmodels CIs; RandomForest: bootstrap quantiles `[deferred]`).

## Computational Feasibility

- **CPU‑only**: EAM relaxation of small GB supercells runs in seconds–minutes per cell on a modest number of cores.; ≥200 configurations fit comfortably in ≤6 h. No GPU and no GPU escape hatch is needed.
- **Memory/disk**: OQMD loaded via `datasets` (memory‑mapped/arrow); a fixed‑seed sample of records is persisted, well under typical RAM limits for standard hardware. / A multi‑gigabyte disk..
- **Libraries**: `datasets`, `pymatgen`, `ase`, `scikit-learn`, `statsmodels`, `numpy`, `pandas`, `matplotlib` — all CPU wheels.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Load OQMD via verified `datasets` recipe | Prior plan cited guessed parquet endpoints; the verified loader (`jablonkagroup/oqmd`, name `raw_data`) was executed and returned [deferred] real records |
| Reconstruct bulk structures from formula + `volume_per_atom` | Verified OQMD records lack atomic coordinates; we now derive lattice constants from `volume_per_atom` and use pymatgen prototypes – a documented, checksummed derivation |
| Generate segregation energies via EAM | FR‑011 explicitly references "EAM‑derived segregation‑energy labels"; no verified open literature segregation database exists |
| Implement FR‑011 harness with `[DATA_UNAVAILABLE]` path | No verified DFT benchmark URL exists; the harness will report `[DATA_UNAVAILABLE]` and a structured limitation record |
| Train BOTH Linear Regression and RandomForest | FR‑004a and FR‑004b are separate requirements; prior plan’s Ridge‑only choice covered neither |
| Power analysis at f² = 0.15 | FR‑008 specifies f² = 0.15 (prior plan’s 0.2 was un‑spec’d) |
| Drop the λ sensitivity sweep | FR‑006 was REMOVED from the spec; keeping it would add an un‑spec’d constraint |
| Add FR‑009 plot and FR‑010 linearity assessment | Both are spec requirements absent from the prior plan |
| VIF before any dimensionality reduction, no predictor removal | FR‑007/FR‑012; flagged relationships reported descriptively |
| Explicitly note that results are associational within the EAM model | Addresses methodology‑7d4ddb28 and scientific‑soundness‑68851c51 concerns |
| Update `.gitignore`/`README.md` with content‑verified tests | T001b/T001c now satisfied by ensuring these files contain the required patterns/sections (verified by integration tests) |
| Record Materials Project omission as a deviation | Constitution VI requires both sources; deviation is justified and documented |