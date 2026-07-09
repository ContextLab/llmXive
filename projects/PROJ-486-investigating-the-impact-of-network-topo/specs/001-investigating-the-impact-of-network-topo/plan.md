# Implementation Plan: Pipeline Validation - Investigating the Impact of Network Topology on Neural Entrainment (Simulated Data)

**Branch**: `001-network-topology-entrainment` | **Date**: 2023-10-27 | **Spec**: `spec.md`

## Summary

This project implements a **computational pipeline validation** to test the hypothesis that resting‑state network topology (Clustering Coefficient, Characteristic Path Length) predicts neural entrainment strength to rhythmic stimuli. Because no verified public dataset contains both HCP fMRI connectivity matrices **and** rhythmic entrainment metrics for the same subjects, the study operates as a **pipeline validation** that uses **synthetic entrainment data** when real matched data are unavailable. All results derived from synthetic data are clearly labeled `data_source: "synthetic"` and the final report includes a disclaimer that the analysis validates the code, not the biological hypothesis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.4.2`, `networkx==3.2.1`, `scipy==1.13.0`, `matplotlib==3.8.4`, `nibabel==5.2.1`, `pyyaml==6.0.1`  
**Storage**: Local filesystem (`data/` for raw/processed, `artifacts/` for plots/reports).  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow).  
**Target Platform**: Linux (`ubuntu-latest` GitHub Actions runner).  
**Performance Goals**: Complete full pipeline < 6 h; Memory < 7 GB RAM.  
**Constraints**: CPU‑only; no GPU, no large‑model training.  
**Statistical Rigor**: Bonferroni correction for N = 2; **Partial Correlation** to test unique effects; Power warning for N < 30; all analyses are correlational (associational framing).  
**Scope Note**: The pipeline will **always** run; if real matched entrainment data are missing, it will **switch** to synthetic data (see "Synthetic Data Fallback Policy").

## Constitution Check

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned (`seed=42`) in `download.py` and `analysis.py`; `requirements.txt` pins exact versions; data fetched from canonical URLs **or** generated deterministically. |
| **II. Verified Accuracy** | **Pass** | The HCP URL is verified. The external entrainment dataset is not available; the synthetic fallback is verified as a deterministic process. No unverified citations are used. |
| **III. Data Hygiene** | **Pass** | Raw data preserved; derivations written to new files; checksums recorded in `state/`. |
| **IV. Single Source of Truth** | **Pass** | All statistics in `paper/` trace back to rows in `data/processed/results.csv` and code in `code/`. |
| **V. Versioning Discipline** | **Pass** | Content hashes tracked for all artifacts; timestamps managed by Advancement‑Evaluator. |
| **VI. Statistical Rigor** | **Pass** | Bonferroni correction applied; **Partial Correlation** used for unique effects; significance flagged if N < 30. |
| **VII. Multimodal Data Alignment** | **Pass** | Inner join on `subject_id` with explicit logging; sensitivity analysis for AAL/Power 264 atlases documented. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-impact-of-network-topo/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── correlation_results.schema.yaml
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── topology_metrics.schema.yaml
└── tasks.md
```

### Source Code (repository root)

```text
projects/PROJ-486-investigating-the-impact-of-network-topo/
├── code/
│   ├── __init__.py
│   ├── download.py          # Downloads HCP parquet and generates synthetic entrainment
│   ├── preprocess.py        # Loads/parcellates (if needed)
│   ├── metrics.py           # NetworkX graph metric calculation
│   ├── analysis.py          # Correlation, Bonferroni, Partial Correlation, Power check
│   ├── viz.py               # Scatter plots, robustness bar chart
│   └── main.py              # Orchestrator
├── data/
│   ├── raw/
│   ├── processed/
│   └── checksums.txt
├── artifacts/
│   ├── plots/
│   └── reports/
├── tests/
│   ├── test_metrics.py
│   └── test_analysis.py
└── requirements.txt
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Synthetic Data Fallback** | Required by US‑1/US‑2 when real entrainment data are missing. | Skipping fallback would cause the pipeline to halt with no output. |
| **Partial Correlation** | Required to disentangle unique effects of CC and CPL, which are mathematically coupled. | Separate univariate tests with a VIF flag are statistically invalid for unique effect attribution. |
| **Power Warning Logic** | Required by US‑2 and SC‑004 to flag low‑sample analyses. | Silent execution would mislead users. |
| **Robustness Bar Chart (SC‑002)** | Required to show absolute differences for both AAL and Power264. | A single‑atlas chart would not meet SC‑002. |
| **Multivariate Limitation Disclaimer** | Required by scientific soundness concerns. | Ignoring the limitation would produce misleading interpretations. |

## Implementation Phases

### Phase 0: Data Availability Check & Synthetic Generation
1. **Download**: Fetch HCP connectivity data from the verified HuggingFace source `jonxuxu/HCP-flat` via `pandas.read_parquet`.
2. **Validate**: Ensure required columns (`subject_id`, connectivity matrix) exist.
3. **Synthetic Entrainment Generation** (Fallback):
   - Fixed random seed `42`.
   - Draw raw entrainment values from `Normal(mean=0.5, sd=0.1)`.
   - Impose a modest linear relationship with the primary topology metric (e.g., `entrainment = 0.5 + 0.3 * (clustering_coefficient - mean_cc) + ε`) to emulate a realistic effect size (`r≈0.3`).  
   - Save to `data/raw/synthetic_entrainment.csv` and tag `data_source: "synthetic"`.
   - **Mandatory Fallback**: If real entrainment data is missing or the inner join yields N < 30, the system **MUST** use this synthetic data. It does not halt.

### Phase 1: Metric Calculation
1. **Compute**: For each subject and atlas (Schaefer, AAL, Power264), construct a weighted graph from the connectivity matrix using `networkx`.
2. **Metrics**:
   - **Clustering Coefficient**: Global average of local clustering coefficients.
   - **Characteristic Path Length**: Average shortest path length (weighted).
3. **Collinearity Check**: Calculate Variance Inflation Factor (VIF) between the two metrics across subjects.  
   - **Implementation Detail**: In `analysis.py`, if `VIF > 5`, the system will **not** suppress significance based on a heuristic. Instead, it will proceed to **Partial Correlation** (Phase 2) to isolate unique effects.

### Phase 2: Correlation Analysis (Unique Effects)
1. **Test**:
   - **Primary**: Spearman rank correlation between each topology metric and entrainment strength (univariate).
   - **Unique Effects**: **Partial Correlation** between each topology metric and entrainment strength, controlling for the other topology metric. This addresses the mathematical coupling of CC and CPL.
2. **Bonferroni Correction**: Adjust p‑values for the two tests (N = 2) on the partial correlations.
3. **Power Check**: If `N < 30`, set `power_warning = "Power Warning: N < 30 (Exploratory)"`.
4. **Significance Flag**: `is_significant = (p_adj < 0.05)`.

### Phase 3: Robustness Sensitivity Analysis (SC‑002)
1. **Repeat**: Re‑run Phases 1‑2 for AAL and Power264 atlases.
2. **Effect‑Size Difference**: Compute absolute differences in Spearman |r| (from the **partial correlation** results) between Schaefer and each alternative atlas.
   - `diff_AAL = |r_partial_Schaefer - r_partial_AAL|`
   - `diff_Power = |r_partial_Schaefer - r_partial_Power264|`
3. **Visualization**: Generate a **single bar chart** (`artifacts/plots/robustness_bar.png`) with two bars:
   - Bar 1: `diff_AAL`
   - Bar 2: `diff_Power`
   - **Y‑axis label**: `"Absolute Difference in Effect Size (|r|)"`  
   - Include a legend indicating each alternative atlas.
   - **Explicit Requirement**: This chart must visualize the difference for **both** AAL and Power 264 simultaneously.

### Phase 4: Reporting
1. **Outputs**:
   - `data/processed/results.csv` (merged topology + entrainment + partial correlation stats + warnings).
   - `artifacts/plots/scatter_schaefer.png` (primary scatter with 95 % CI).
   - `artifacts/plots/robustness_bar.png` (SC‑002 bar chart).
   - `artifacts/reports/summary.txt` containing:
     * Correlation statistics (r, p, p_adj) for each metric (partial correlation).
     * Power warning.
     * Explicit disclaimer: *"All entrainment values are synthetic; the analysis validates the computational pipeline, not the biological hypothesis."*
2. **Schema Validation**: Results are validated against the contracts in `contracts/`.

## Statistical Methodology

### 1. Graph Metric Calculation
* Input: Weighted connectivity matrix per subject.
* Method: Construct `networkx.Graph` (weighted edges).
* Metrics: Global clustering coefficient; characteristic path length (average of shortest paths).

### 2. Correlation & Unique Effects (Revised)
* **Univariate Test**: Spearman rank correlation (CC vs Entrainment, CPL vs Entrainment).
* **Unique Effects Test**: **Partial Correlation**. To address the mathematical coupling of CC and CPL, the primary hypothesis test for unique contributions will use partial correlation (e.g., `scipy.stats.partialcorr`).
* **Multiple‑Comparison**: Bonferroni correction for N = 2 tests (on the partial correlations).
* **Significance**: `p_adj < 0.05`.

### 3. Collinearity & VIF
* VIF is calculated as a diagnostic. If `VIF > 5`, it confirms high coupling.
* **Correction**: Instead of suppressing significance, the pipeline uses **Partial Correlation** to isolate the unique effect of each metric. This resolves the methodological inconsistency of using VIF in a univariate framework.

### 4. Robustness (SC‑002)
* Absolute differences in **partial correlation** effect sizes are plotted in a single bar chart with the y‑axis label **"Absolute Difference in Effect Size (|r|)"**.

### 5. Limitations (Statistical Soundness)
* The pipeline performs **partial correlations** to test unique effects, acknowledging that CC and CPL are coupled. This is a more rigorous approach than separate univariate tests.
* The analysis remains correlational; no causal claims are made.

## Compute Feasibility (CI Constraints)

* Runtime: Metric computation on 200‑node graphs for ≤ 500 subjects < 1 min; full pipeline < 30 min on GitHub Actions runner.
* Memory: Parquet files < 1 GB; total RAM usage < 4 GB.
* No GPU required; all libraries are CPU‑compatible.

## Quick Reference of File Paths
* `code/download.py` – data download & synthetic generation.  
* `code/metrics.py` – graph metric functions.  
* `code/analysis.py` – correlation, Bonferroni, Partial Correlation, Power check.  
* `code/viz.py` – scatter and robustness bar chart creation.  
* `data/raw/` – HCP parquet + synthetic entrainment CSV.  
* `data/processed/results.csv` – final merged table.  
* `artifacts/plots/` – visualizations.