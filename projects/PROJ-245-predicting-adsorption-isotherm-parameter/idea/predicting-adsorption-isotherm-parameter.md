---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Adsorption Isotherm Parameters from Molecular Features

**Field**: chemistry

## Research question

Which molecular descriptors of adsorbates and physicochemical properties of adsorbents most strongly determine key adsorption isotherm parameters (Henry's constant and Langmuir capacity), and how well do these relationships generalize to adsorbent materials unseen during model training?

## Motivation

Determining adsorption isotherm parameters experimentally is resource-intensive, creating a bottleneck in the design of gas storage and separation materials. There is a lack of systematic, quantitative evidence about the *relative* importance of adsorbate descriptors versus adsorbent properties in determining these thermodynamic parameters across a broad dataset. This project addresses that gap with an interpretable regression study whose statistical validation is fully specified, enabling faster, physics-informed computational screening.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv with "adsorption isotherm parameters prediction," "machine learning Henry's constant," "molecular descriptors adsorption," and "Langmuir parameter estimation," plus broader searches on type I isotherm fitting and adsorption on defective surfaces. The search returned few results; most literature addresses fitting isotherm equations to measured data or single-material experimental studies, not predictive mapping from descriptors to parameters.

### What is known

- [Simple isotherm equations to fit type I adsorption data (2009)](https://arxiv.org/abs/0911.2012) — Establishes analytical fitting frameworks for type I isotherm data on microporous adsorbents, providing the baseline mathematical route for parameter extraction, but not predictive modeling from descriptors.
- [Estimating the coefficients of variation of Freundlich parameters with weighted least squares analysis (2017)](https://arxiv.org/abs/1710.10023) — Establishes rigorous statistical practice (weighted least squares and uncertainty estimation) for extracting Freundlich parameters, informing how parameter uncertainty should be handled when parameters are used as regression targets.
- [Dose-dependent isotherm of Kr adsorption on heterogeneous bundles of closed single-walled carbon nanotubes (2021)](https://arxiv.org/abs/2111.06657) — Provides high-resolution experimental isotherms for a specific nanomaterial, illustrating surface heterogeneity effects but not generalizable parameter prediction.

### What is NOT known

No published work has systematically quantified the relative importance of specific molecular descriptors (e.g., polarizability, kinetic diameter) versus adsorbent properties (e.g., pore volume, surface area) in determining Henry's constants or Langmuir capacities across a broad multi-material dataset, with uncertainty-quantified feature importance that accounts for both material-level clustering and descriptor multicollinearity.

### Why this gap matters

Filling this gap would let researchers prioritize adsorbent candidates for synthesis based on computed descriptors, accelerating materials discovery, and would constrain which physical interactions dominate adsorption strength — useful for rational surface design in gas separation.

### How this project addresses the gap

The methodology below builds a curated descriptor–parameter dataset, trains group-held-out regression models, and quantifies feature importance with a fully specified, pairing-aware permutation protocol and group-based handling of correlated descriptors, directly producing the previously unavailable relative-importance evidence.

## Expected results

We expect a small subset of descriptors (e.g., adsorbate polarizability, kinetic diameter, and adsorbent accessible surface area) to dominate predictions. The primary informative outcome is the held-out R² and its uncertainty: if the model substantially beats a physics-informed baseline (surface-area-scaled capacity; polarizability-based Henry's constant proxy) on adsorbents unseen in training, descriptor-based screening is viable; if it does not, the negative result constrains claims of descriptor-driven predictability and is itself publishable as a benchmark finding. Feature-importance rankings with confidence intervals either align with or diverge from established physicochemical intuition, and the direction of that finding is informative either way.

## Methodology sketch

- **Data acquisition**: Download adsorption isotherm data from the NIST Adsorption Database (https://adsorption.nist.gov/) and the CoRE MOF / Zenodo gas-uptake compilations (e.g., DOI: 10.5281/zenodo.3933373). All URLs/DOIs recorded in a manifest file for reproducibility.
- **Parameter extraction with uncertainty**: Fit Langmuir and Henry-law models to raw isotherm curves by weighted least squares (following the statistical practice of arXiv:1710.10023), recording each parameter with its standard error; parameters with relative SE > 50% are excluded. Targets are analyzed as log₁₀(parameter) to handle the orders-of-magnitude skew of Henry's constants.
- **Type I filtering with a guaranteed non-empty fallback**: Classify isotherm shape algorithmically rather than relying on a schema column: fit both Langmuir and BET models and retain isotherms whose Langmuir fit has AIC within 10 of the best fit and whose uptake is monotone and concave in pressure (automated shape classification). If fewer than 200 isotherms pass, relax to all monotone concave isotherms; if still < 200, fall back to Henry's-constant-only analysis (Henry's constant is defined at the low-pressure limit for all isotherm types). The pipeline aborts only if the fallback also yields < 100 usable entries, in which case the run reports the data-availability limitation as a finding.
- **Descriptor calculation**: Adsorbate descriptors from RDKit and published tables: molecular weight, topological polar surface area, estimated polarizability (atomic-increment method), H-bond donors/acceptors, van der Waals volume, plus **kinetic diameter and Lennard-Jones ε/kB from the standard UFF/TraPPE tables** (explicitly included as first-class features). Adsorbent descriptors from dataset metadata/cif: BET surface area, pore volume, density, maximum pore diameter, functional-group indicators. Collinear descriptor groups are pre-defined by domain knowledge (e.g., {polarizability, vdW volume, MW}, {surface area, pore volume}) and reported as groups in addition to individual features.
- **Data split (leakage-safe, sparse-data-aware)**: Primary split is by adsorbent material (group split, 80/20), stratified so each split has comparable adsorbate-composition distributions; report the adsorbate distribution of both splits and the KL divergence between them. If > 30% of materials have only one adsorbate (sparse case), use leave-one-adsorbent-out cross-validation as the primary generalization metric and report both. No (adsorbent, adsorbate) pair appears in both train and test under any scheme.
- **Baselines and models**: Two baselines: (a) null model predicting the training-set median of log-target; (b) a physics-informed baseline (Langmuir capacity ∝ surface area; Henry's constant ∝ polarizability × surface area). Train ridge regression, Random Forest, and Gradient Boosting (scikit-learn) with 5-fold group CV hyperparameter tuning on the training set.
- **Performance evaluation**: R², RMSE, MAE on log-scale targets for the held-out set, with 95% bootstrap confidence intervals (1000 resamples). The improvement over each baseline is tested with a one-sided paired bootstrap test on held-out residuals (p < 0.05). Runtime target: end-to-end ≤ 4 hours on a GitHub Actions 2-core, 7 GB RAM runner (the execution environment is fixed and stated in the run manifest).
- **Feature importance — single, well-defined protocol**: Use (i) SHAP values computed with a representative background sample of 100 training points, and (ii) a **pairing-aware permutation test**: the adsorbate–adsorbent *pairing* is permuted — adsorbate descriptor vectors are randomly reassigned across different adsorbents within the training set, destroying the physical pairing while preserving each descriptor's marginal distribution and the material cluster structure. 1000 permutations, Benjamini–Hochberg FDR correction at α = 0.05. Because descriptors are correlated, importance is additionally computed at the pre-defined group level (permuting whole collinear groups together) and group-level results are the primary reported p-values; individual-feature p-values are reported as secondary. This replaces any within-cluster shuffling scheme.
- **Reduced-feature check**: Train a model on only the top-3 descriptors, where "top-3" is fixed as the three highest mean-|SHAP| features of the best model from the evaluation step; report its held-out R² against the null and physics baselines with the same paired bootstrap test.
- **Independent literature comparison**: Compare identified dominant descriptors against an externally fixed, version-controlled reference list derived from published experimental adsorption studies and the isotherm-fitting literature (the three papers above plus standard texts), stored as a committed input file with citations. The comparison is reported as a qualitative discussion of convergence/divergence (with an explicit table of top-5 model features vs. listed features), NOT as a pass/fail validation, to avoid circular confirmation.
- **Edge-case handling (specified, not ad hoc)**: entries with missing pore volume are flagged and excluded (not imputed) with counts reported; isotherms whose fit residuals show systematic structure are flagged as outliers in a machine-readable report; if held-out R² < 0.5, a fixed diagnostic checklist is emitted automatically (adsorbate distribution shift, target skew, sample size, residual-vs-feature plots, per-cluster error breakdown).
- **Reproducibility**: All steps run in a GitHub Actions job (2 cores, 7 GB RAM, ≤ 6 h); the repository contains requirements.txt, the data manifest with URLs/DOIs, fixed random seeds, and scripts producing all figures and tables.

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-10-21T06:29:37Z
**Outcome**: exhausted
**Original term**: Predicting Adsorption Isotherm Parameters from Molecular Features chemistry
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Adsorption Isotherm Parameters from Molecular Features chemistry | 0 |
| 1 | machine learning prediction of adsorption isotherms | 5 |
| 2 | quantitative structure-property relationships adsorption | 0 |
| 3 | molecular descriptor based adsorption modeling | 0 |
| 4 | neural network gas adsorption prediction | 0 |
| 5 | predicting Langmuir isotherm parameters | 0 |
| 6 | Freundlich isotherm parameter estimation from structure | 0 |
| 7 | adsorption equilibrium prediction from molecular structure | 0 |
| 8 | graph neural networks for adsorption properties | 0 |
| 9 | gas uptake prediction metal-organic frameworks | 0 |
| 10 | high-throughput screening adsorption capacity prediction | 0 |
| 11 | computational prediction of adsorption coefficients | 0 |
| 12 | QSAR modeling of organic pollutant adsorption | 0 |
| 13 | molecular simulation derived isotherm fitting | 0 |
| 14 | surrogate models for adsorption equilibrium data | 0 |
| 15 | deep learning porous materials gas storage prediction | 0 |
| 16 | cheminformatics approaches to adsorption phenomena | 0 |
| 17 | machine learning Henry's constant prediction | 0 |
| 18 | predicting adsorption affinity from chemical features | 0 |
| 19 | data-driven isotherm parameter regression | 0 |
| 20 | transfer learning adsorption property prediction | 0 |

### Verified citations

1. **Dose-dependent isotherm of Kr adsorption on heterogeneous bundles of closed single-walled carbon nanotubes** (2021). Svetlana Yu Tsareva, Edward Mcrae, Fabrice Valsaque, Xavier Devaux. arXiv. [2111.06657](https://arxiv.org/abs/2111.06657). PDF-sampled: No.
2. **Adsorption from Binary Liquid Solutions into Mesoporous Silica: A Capacitance Isotherm on 5CB Nematogen/Methanol Mixtures** (2021). Andriy V. Kityk, Gennady Y. Gor, Patrick Huber. arXiv. [2102.06908](https://arxiv.org/abs/2102.06908). PDF-sampled: No.
3. **Estimating the coefficients of variation of Freundlich parameters with weighted least squares analysis** (2017). Jos J. T. I. Boesten. arXiv. [1710.10023](https://arxiv.org/abs/1710.10023). PDF-sampled: No.
