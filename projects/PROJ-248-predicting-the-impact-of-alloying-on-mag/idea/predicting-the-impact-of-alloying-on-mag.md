---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Field**: materials science

## Research question

How do alloying composition and crystal structure determine saturation magnetization and Curie temperature in bulk transition‑metal alloys, and which elemental descriptors carry the most predictive signal?

## Motivation

Experimental measurement of magnetic moments and Curie temperatures for alloy systems is time‑consuming and costly, limiting the speed of permanent‑magnet discovery. A data‑driven surrogate that reliably maps composition + structure to these magnetic properties would enable rapid virtual screening of thousands of candidate alloys, focusing experimental effort on the most promising compositions and accelerating materials development.

## Related work

- **High‑throughput calculations of magnetic topological materials (2020)** – https://arxiv.org/abs/2003.00012  
  Demonstrates large‑scale DFT computation of magnetic properties (including magnetic moments and Curie temperatures) and the use of machine‑learning models to predict them, providing a methodological precedent for high‑throughput alloy magnetism prediction.

- **Nanostructured exchange‑coupled hard/soft composites: from the local magnetization profile to an extended 3D simple model (2011)** – https://arxiv.org/abs/1110.5737  
  Shows how alloy composition and microstructural arrangement jointly determine macroscopic magnetic performance, underscoring the relevance of linking compositional/structural descriptors to magnetic outcomes.

- **Probing magnetic ordering in air‑stable iron‑rich van der Waals minerals (2023)** – https://arxiv.org/abs/2304.06533  
  Highlights the sensitivity of magnetic ordering to subtle changes in composition and crystal structure, illustrating the broader principle that composition‑structure relationships govern magnetic properties.

- **Magnetic anisotropy in two‑dimensional van der Waals magnetic materials and their heterostructures (2025)** – https://arxiv.org/abs/2508.04952  
  Discusses mechanisms by which structural motifs affect magnetic anisotropy, reinforcing the importance of structural descriptors when modeling magnetic behavior.

## Expected results

- Achieve an R² ≥ 0.80 for saturation magnetization and ≥ 0.75 for Curie temperature on a held‑out test set of experimentally or DFT‑validated alloys.  
- Identify a ranked list of elemental descriptors (e.g., atomic radius, d‑electron count, electronegativity) that contribute the most to predictive performance via feature‑importance analysis.  
- Demonstrate that a nonlinear ensemble model (Random Forest or Gradient Boosting) significantly outperforms a linear baseline (p < 0.01 in a paired t‑test on residuals).

## Methodology sketch

- **Data acquisition**  
  - Use the Materials Project REST API (public endpoint) to download all entries labeled with `magnetic_type` ≠ `NM` and with available `magnetic_moment` and `curie_temperature` fields (≈ 4 000 bulk alloys).  
  - Supplement with the Open Quantum Materials Database (OQMD) magnetic dataset via a direct `wget` of the CSV release (URL provided in OQMD documentation).  

- **Data cleaning & preprocessing**  
  - Exclude entries lacking complete composition strings or crystal‑structure information.  
  - Convert each composition to a standardized formula using `pymatgen`.  
  - Resolve duplicate entries by keeping the most recent DFT calculation.  

- **Feature engineering**  
  - Encode composition as fractional elemental abundances.  
  - Compute element‑wise averages of physical properties (atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus) using `matminer`’s `ElementProperty` featurizer.  
  - Add crystal‑structure descriptors: space‑group number, lattice parameters (a, b, c, α, β, γ), and packing fraction.  

- **Model training**  
  - Split the dataset 80/20 (train/test) with stratification on `magnetic_type`.  
  - Train two regressors per target (saturation magnetization, Curie temperature):  
    - Random Forest Regressor (`n_estimators=300`, `max_depth=20`).  
    - Gradient Boosting Regressor (`learning_rate=0.05`, `n_estimators=500`).  
  - Hyper‑parameter tuning via `GridSearchCV` with 5‑fold cross‑validation (limited to ≤ 30 min total runtime).  

- **Evaluation & validation independence**  
  - Compute R², MAE, and RMSE on the held‑out test set.  
  - Perform a paired t‑test comparing residuals of each ensemble model against a linear regression baseline to assess statistical significance.  
  - Validation is independent because the target magnetic properties are derived from DFT/experiment, whereas all input features are elemental/structural descriptors not containing magnetic information.  

- **Interpretability**  
  - Extract feature importances from the best‑performing model.  
  - Visualize the top 10 descriptors with `matplotlib` and report their physical interpretation.  

- **Reproducibility**  
  - All code written in Python 3.11, dependencies listed in `requirements.txt`.  
  - Random seeds fixed (`np.random.seed(42)`, `random_state=42`).  
  - Store the cleaned dataset (`data.csv`), trained model (`model.pkl`), and evaluation metrics (`metrics.json`) as GitHub Actions artifacts.  
  - Entire pipeline designed to complete within a single 6‑hour GHA job on the free‑tier runner (≈ 2 GB RAM peak, < 10 GB SSD usage).  

## Duplicate-check

- Reviewed existing ideas: None.
- Closest match: None.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-24T10:09:19Z
**Outcome**: exhausted
**Original term**: Predicting the Impact of Alloying on Magnetic Properties via Public Data materials science
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting the Impact of Alloying on Magnetic Properties via Public Data materials science | 4 |

### Verified citations

1. **Probing magnetic ordering in air stable iron-rich van der Waals minerals** (2023). Muhammad Zubair Khan, Oleg E. Peil, Apoorva Sharma, Oleksandr Selyshchev, Sergio Valencia, et al.. arXiv. [2304.06533](https://arxiv.org/abs/2304.06533). PDF-sampled: No.
2. **Nanostructured exchange coupled hard / soft composites: from the local magnetization profile to an extended 3D simple model** (2011). V. Russier, K. Younsi, L. Bessais. arXiv. [1110.5737](https://arxiv.org/abs/1110.5737). PDF-sampled: No.
3. **Magnetic Anisotropy in Two-dimensional van der Waals Magnetic Materials and Their Heterostructures: Importance, Mechanisms, and Opportunities** (2025). Yusheng Hou, Ruqian Wu. arXiv. [2508.04952](https://arxiv.org/abs/2508.04952). PDF-sampled: No.
4. **High-throughput calculations of magnetic topological materials** (2020). Yuanfeng Xu, Luis Elcoro, Zhida Song, Benjamin J. Wieder, M. G. Vergniory, et al.. arXiv. [2003.00012](https://arxiv.org/abs/2003.00012). PDF-sampled: No.
