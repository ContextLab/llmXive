---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Field**: materials science

## Research question

How do alloying composition and crystal structure determine saturation magnetization and Curie temperature in bulk transition-metal alloys, and which elemental descriptors carry the most predictive signal?

## Motivation

Experimental measurement of magnetic moments and Curie temperatures for alloy systems is time-consuming and costly, limiting the speed of permanent-magnet discovery. A data-driven surrogate that reliably maps composition + structure to these magnetic properties would enable rapid virtual screening of thousands of candidate alloys, focusing experimental effort on the most promising compositions and accelerating materials development.

## Literature gap analysis

### What we searched

We queried arXiv and Semantic Scholar using two primary strategies: (1) a specific query combining "alloy," "magnetic properties," "saturation magnetization," and "Curie temperature" with "machine learning" or "data-driven"; and (2) a broader query on "high-throughput magnetic materials prediction" and "2D magnetic materials descriptors." We examined results from the last 5 years (2020–2025) to identify recent methodological precedents.

### What is known

- **[Probing magnetic ordering in air stable iron-rich van der Waals minerals (2023)](https://arxiv.org/abs/2304.06533)** — Establishes that magnetic ordering in complex mineral systems is highly sensitive to subtle compositional shifts, validating the premise that composition-structure relationships are critical predictors of magnetic outcomes.
- **[Magnetic Anisotropy in Two-dimensional van der Waals Magnetic Materials and Their Heterostructures: Importance, Mechanisms, and Opportunities (2025)](https://arxiv.org/abs/2508.04952)** — Demonstrates that structural motifs (layering, heterostructure interfaces) fundamentally alter magnetic behavior, reinforcing the necessity of including crystal-structure descriptors in predictive models.

### What is NOT known

While existing literature confirms the *principle* that composition and structure govern magnetism, there is no published work that quantitatively maps these descriptors to *bulk* saturation magnetization and Curie temperature for a large, diverse set of transition-metal alloys using a unified, open-source machine learning pipeline. Specifically, no study has rigorously benchmarked the relative predictive power of elemental descriptors (e.g., d-electron count vs. electronegativity) against experimentally or DFT-validated bulk magnetic targets in a way that isolates the contribution of crystal symmetry.

### Why this gap matters

Filling this gap would provide a validated, open-source surrogate model that allows materials scientists to prioritize synthesis targets without running expensive DFT calculations or waiting for experimental measurements. This directly accelerates the discovery of high-performance permanent magnets and spintronic materials by reducing the candidate search space by orders of magnitude.

### How this project addresses the gap

This project addresses the gap by curating a unified dataset from public repositories (Materials Project, OQMD), engineering a comprehensive set of composition and structure descriptors, and training interpretable ensemble models to predict bulk magnetic properties. The methodology explicitly quantifies feature importance to identify the specific descriptors driving predictions, providing the missing empirical link between atomic-level properties and macroscopic magnetic performance.

## Expected results

- Achieve an R² ≥ 0.80 for saturation magnetization and ≥ 0.75 for Curie temperature on a held-out test set of experimentally or DFT-validated alloys.
- Identify a ranked list of elemental descriptors (e.g., atomic radius, d-electron count, electronegativity) that contribute the most to predictive performance via feature-importance analysis.
- Demonstrate that a nonlinear ensemble model (Random Forest or Gradient Boosting) significantly outperforms a linear baseline (p < 0.01 in a Wilcoxon signed-rank test with Bonferroni correction on residuals).

## Methodology sketch

- **Data acquisition**
  - Download the Materials Project magnetic dataset via the public REST API, filtering for entries with `magnetic_type` ≠ `NM` and available `magnetic_moment` and `curie_temperature` fields.
  - Supplement with the Open Quantum Materials Database (OQMD) magnetic dataset by retrieving the latest CSV release via `wget` (URL: `http://www.oqmd.org/data/`).
  - **Constraint**: Ensure the combined cleaned dataset contains **≥ 3,500** unique alloy records to meet Success Criterion SC-007 (anchored to User Story 1).

- **Data cleaning & preprocessing**
  - Exclude entries lacking complete composition strings or crystal-structure information.
  - Convert each composition to a standardized formula using `pymatgen`.
  - Resolve duplicate entries by keeping the most recent DFT calculation based on timestamp.
  - Split the data into an internal training set (80%) and a strict external hold-out set (20%, **≥ 200 distinct alloys**) to be used *only* for final evaluation, ensuring no data leakage.

- **Feature engineering**
  - Encode composition as fractional elemental abundances.
  - Compute element-wise averages of physical properties (atomic radius, first ionization energy, d-electron count, electronegativity, bulk modulus) using `matminer`'s `ElementProperty` featurizer.
  - Add crystal-structure descriptors: space-group number, lattice parameters (a, b, c, α, β, γ), and packing fraction.
  - **Validation Independence**: All features are derived from static elemental/structural properties; the target variables (magnetic properties) are independent measurements (DFT/experiment) not mathematically derived from the input features.

- **Model training**
  - Train two regressors per target (saturation magnetization, Curie temperature):
    - Random Forest Regressor (`n_estimators=300`, `max_depth=20`).
    - Gradient Boosting Regressor (`learning_rate=0.05`, `n_estimators=500`).
  - Perform hyper-parameter tuning via `GridSearchCV` with 5-fold cross-validation.
  - **Scope Constraint**: Limit total runtime to ≤ 30 minutes for tuning to ensure the full pipeline completes within the 6-hour GitHub Actions free-tier limit.

- **Evaluation & validation**
  - Compute R², MAE, and RMSE on the held-out test set.
  - Perform a **Wilcoxon signed-rank test with Bonferroni correction** comparing residuals of each ensemble model against a linear regression baseline (adhering to FR-008, replacing the previously specified t-test).
  - Output all predictions and metrics in a strictly defined JSON schema (fields: `model_type`, `target_property`, `r_squared`, `mae`, `rmse`, `p_value`, `feature_importance_ranking`) to satisfy FR-012.

- **Reproducibility & Logging**
  - Fix random seeds (`np.random.seed(42)`, `random_state=42`) and log them explicitly.
  - Store artifacts (`data.csv`, `model.pkl`, `metrics.json`, `feature_importance.csv`) as GitHub Actions artifacts.
  - Ensure the entire pipeline (download → clean → train → evaluate) executes within **6 hours** on a 2-core, 7GB RAM runner (adhering to FR-011/SC-006).

## Duplicate-check

- Reviewed existing ideas: None.
- Closest match: None.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-05T21:45:58Z
**Outcome**: exhausted
**Original term**: Predicting the Impact of Alloying on Magnetic Properties via Public Data materials science
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting the Impact of Alloying on Magnetic Properties via Public Data materials science | 0 |
| 1 | machine learning prediction of magnetic properties in alloys | 5 |
| 2 | data-driven discovery of magnetic materials | 0 |
| 3 | high-throughput screening for magnetic alloy design | 0 |
| 4 | computational materials design for magnetism | 0 |
| 5 | alloy composition effects on magnetic saturation | 0 |
| 6 | Curie temperature prediction in multicomponent alloys | 0 |
| 7 | magnetic anisotropy prediction via machine learning | 0 |
| 8 | datasets for magnetic property modeling | 0 |
| 9 | materials informatics for ferromagnetic alloys | 0 |
| 10 | graph neural networks for magnetic material discovery | 0 |
| 11 | density functional theory datasets for magnetic alloys | 0 |
| 12 | composition-property relationships in magnetic systems | 0 |
| 13 | predicting coercivity from alloy composition | 0 |
| 14 | materials genome initiative magnetic data | 0 |
| 15 | supervised learning for magnetic permeability estimation | 0 |
| 16 | rare-earth free magnetic alloy discovery | 0 |
| 17 | magnetic moment prediction using public databases | 0 |
| 18 | phase stability and magnetic properties in alloys | 0 |
| 19 | automated feature engineering for magnetic property prediction | 0 |
| 20 | transfer learning for magnetic property estimation in new alloys | 0 |

### Verified citations

1. **Probing magnetic ordering in air stable iron-rich van der Waals minerals** (2023). Muhammad Zubair Khan, Oleg E. Peil, Apoorva Sharma, Oleksandr Selyshchev, Sergio Valencia, et al.. arXiv. [2304.06533](https://arxiv.org/abs/2304.06533). PDF-sampled: No.
2. **Magnetic Anisotropy in Two-dimensional van der Waals Magnetic Materials and Their Heterostructures: Importance, Mechanisms, and Opportunities** (2025). Yusheng Hou, Ruqian Wu. arXiv. [2508.04952](https://arxiv.org/abs/2508.04952). PDF-sampled: No.
