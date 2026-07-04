# Research: Predicting Alloy Phase Diagrams from Compositional Data

## Dataset Strategy

The primary data source for this project is the **Materials Project API**. The plan relies on the assumption that the public API provides sufficient CALPHAD-assessed temperature-composition phase boundary data for binary systems.

**Verified Datasets**:
*Note: The provided "# Verified datasets" block in the user message lists specific HuggingFace datasets for LOSO, MAE, and MAESTRO, which are unrelated to alloy phase diagrams. As per the instruction "For dataset references in research.md, cite ONLY the URLs listed in the '# Verified datasets' block", and since none of those URLs contain alloy phase data, the following table reflects the actual source required by the spec (Materials Project) while noting the discrepancy.*

| Dataset Name | Description | Verified URL (from User Message) | Status / Action |
| :--- | :--- | :--- | :--- |
| Materials Project Phase Data | Binary/Ternary alloy phase stability and CALPHAD-assessed temperature-composition coordinates. | **None provided in verified list** | **Critical Gap**: The spec requires experimental data (SC-001), but the verified dataset list contains no relevant sources. The plan proceeds by implementing the API fetcher (`FR-001`) to retrieve CALPHAD data from `materialsproject.org`. The final report will explicitly state that experimental validation is not possible with this source. |
| Elemental Properties | Atomic radius, electronegativity, valence electron count (for descriptors). | **None provided** | **Action**: Use a local, static lookup table (e.g., `pymatgen` or a curated CSV) for these constants to avoid external API dependencies for descriptors. |

**Dataset Fit Assessment**:
The spec requires predicting phase boundaries from composition. The Materials Project API is the canonical source for CALPHAD data. However, the **Verified Datasets** block provided in the prompt contains no relevant alloy data.
*   **Mismatch**: The provided verified datasets (LoSoNA, MAESTRO) are for NLP/Time-series, not materials science.
*   **Resolution**: The implementation plan must rely on the **Materials Project API** directly (as per `FR-001`). The "Verified Datasets" constraint in the prompt instructions prevents fabricating a URL. Therefore, the `research.md` explicitly states that the dataset source is the Materials Project API (via code implementation) and notes the absence of a pre-verified URL in the provided list. The `data/` folder will store the raw JSON/CSV fetched by the script, checksummed per Constitution Principle III.

**Data Source Gap**:
The Materials Project API primarily stores DFT-calculated formation energies and convex hull data, not experimental phase diagram coordinates (T vs. composition). The API does not natively expose the specific 'phase boundary' rows required for the target variable (temperature) without complex post-processing of thermodynamic data or reliance on a separate experimental database (e.g., NIST-JANAF or SGTE) which is not cited. The plan proceeds with the CALPHAD-assessed data available via the API, acknowledging that this is a proxy for experimental data.

**Fallback Strategy**:
Since no verified experimental dataset URL exists in the provided list, and the Materials Project API may not contain the specific 'temperature-composition' coordinates, the plan explicitly states that if the API fails to provide the data, the pipeline will fail gracefully with an `NO_DATA_FOUND` error. **No fallback to a non-verified source is implemented** to avoid fabricating URLs. The research question is noted as potentially unanswerable with current resources if the API does not provide the required data.

## Methodological Rigor

### Statistical Approach
1.  **Model**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
2.  **Cross-Validation**: Leave-One-System-Out (LOSO).
    *   *Rationale*: Ensures the model generalizes to unseen chemical systems (combinations of elements), not just unseen compositions within the same system.
    *   *Generalization Limitation*: If a test system contains an element not present in the training set, it will be excluded from the evaluation to prevent descriptor calculation errors. The model does not claim to extrapolate to entirely new chemistry. It interpolates in descriptor space.
    *   *Multiple Comparison Correction*: Not applicable as the primary metric is an aggregate MAE/R² across folds. However, per `FR-004`, metrics are reported per fold.
    *   *Power Justification*: The sample size is determined by the availability of phase boundary data in the Materials Project. If the dataset is small (<1000 samples), the plan will acknowledge the power limitation in the final report. A power analysis will be conducted to determine the minimum detectable effect size. If the sample size is insufficient for [deferred] power, the limitation will be explicitly stated.
3.  **Baseline**: Null model predicting the global mean temperature (`FR-009`).
4.  **Collinearity**: Elemental descriptors (radius, electronegativity) are often correlated. Random Forest handles non-linear interactions well, but independent effects cannot be claimed for correlated predictors. The report will focus on **predictive accuracy** (MAE/R²) rather than feature importance coefficients to avoid misinterpretation.
5.  **Measurement Validity**: Elemental properties (radius, electronegativity) are standard physical constants with high validity. Phase boundary data from Materials Project is **CALPHAD-assessed**, not experimental. The plan treats this as the "ground truth" for the study but explicitly notes the limitation regarding experimental validation.

### Feature Set Limitations
- The model uses only global descriptors (mean atomic radius, electronegativity variance, valence electron count).
- **Hume-Rothery Rules**: Complex phase stability rules (e.g., crystal structure dependencies) are not captured by these global descriptors. The plan acknowledges that the model may fail to capture complex topological features (e.g., invariant reactions in Fe-C) and that such failures are due to feature insufficiency, not model failure.

### Domain Complexity (Fe-C)
- The Fe-C system involves complex invariant reactions (eutectic, peritectic) and metastable phases (cementite) that are highly sensitive to kinetics and specific thermodynamic parameters not captured by simple compositional descriptors.
- The plan limits the scope for Fe-C to predicting primary liquidus/solidus lines. Full phase field reconstruction for Fe-C is noted as out of scope for a composition-only model.

### Computational Feasibility
- **Hardware**: 1 CPU core (Constitution VI), 7 GB RAM, no GPU.
- **Strategy**:
  - Use `scikit-learn` (CPU-optimized).
  - Limit `n_estimators` to a reasonable value (e.g., 100-200) to balance performance and runtime.
  - If the raw dataset exceeds memory or runtime limits, implement random sampling (documented in `data_ingestion.py`) to ensure the pipeline completes within 6 hours.
  - No deep learning or 8-bit quantization (incompatible with CPU-only constraint).

## Error Handling & Edge Cases

| Scenario | Error Code | Action |
| :--- | :--- | :--- |
| Missing temperature coordinates | `MISSING_TEMP_COORDS` | Exclude row, log warning. |
| Low data density (<5 samples OR std dev > 0.5) | `LOW_DATA_DENSITY` | Flag system, report error. (Matches spec Edge Cases). |
| High prediction variance (std dev > 0.5) | `HIGH_VARIANCE` | Flag system, report error (extends `LOW_DATA_DENSITY` logic). |
| API Rate Limit | `API_RATE_LIMIT_EXCEEDED` | Exponential backoff (max 3 retries), then fail gracefully. |
| No data found | `NO_DATA_FOUND` | Fail gracefully. |

## Decision Rationale

*   **Why Random Forest?** It is robust to non-linear relationships, handles mixed data types well, and is computationally efficient on CPU compared to neural networks. It avoids the need for complex feature scaling.
*   **Why LOSO?** The spec explicitly requires testing generalization to unseen systems. K-fold CV would leak system-specific information.
*   **Why not Deep Learning?** The dataset size is likely insufficient for deep learning, and the CPU constraint makes training prohibitively slow.
*   **Why CALPHAD Data?** It is the only available source for phase boundary temperatures via the Materials Project API. Experimental data is not available in the provided verified list.
*   **Why VCS instead of IoU?** IoU is a segmentation metric for discrete regions. Phase diagrams are continuous functions. Calculating IoU requires arbitrary binarization, making the metric scientifically invalid for this regression task. VCS (MAE of boundary lines) is the appropriate metric.