# Research: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Summary

This research plan investigates the relationship between the atomic composition of aluminum alloys (specifically Cu, Mg, Si, Zn, Mn) and their Poisson's ratio. The study utilizes public materials databases (Materials Project, NIST) to construct a dataset, applies compositional data analysis techniques (ILR transformation) to handle the unit-sum constraint, and employs a Random Forest regressor to model the relationship. All findings are framed as associational due to the observational nature of the data.

## Dataset Strategy

### Primary Data Source
The project will attempt to fetch data from the **Materials Project API** and **NIST Materials Data Repository**.
- **Materials Project**: Requires an API key (`MP_API_KEY`). The pipeline will check for this environment variable. If missing, it will attempt a keyless read (if available for the specific subset) or halt with a configuration error.
- **NIST MDR**: Public access for certain datasets.
- **Fallback**: If both sources fail or return zero records, the pipeline will halt with a "Data Availability Failure" error. The project **cannot** proceed with synthetic or unrelated datasets.

**Note on Verified Datasets**: The provided "Verified datasets" block does not contain a specific aluminum alloy dataset with Poisson's ratio and composition. Therefore, the plan relies on the API sources as the primary method, adhering to the principle of not fabricating data sources.

### Data Availability Verification
- **Feasibility**: The pipeline will implement a streaming approach if the dataset is large, but given the expected scale (<2000 entries), a full download is feasible within the 7 GB RAM limit.
- **Minimum Sample Size**: The pipeline requires a minimum of **N=50** independent records to proceed. This threshold is based on literature suggesting that Random Forest feature importance becomes unstable below this sample size for compositional data.

## Methodology

### 1. Data Extraction and Filtering
- **Source**: Materials Project / NIST.
- **Filtering Criteria**:
  - Monolithic aluminum alloys (exclude composites).
  - Presence of Poisson's ratio (independent measurement, not derived).
  - Presence of Young's modulus.
  - Presence of atomic fractions for Cu, Mg, Si, Zn, Mn.
  - Sum of major elements (Cu+Mg+Si+Zn+Mn) must be ≥ 0.95 (to ensure Al balance is valid).
- **Normalization**:
  - Elastic constants: GPa.
  - Composition: Atomic fractions summing to 1.0.
  - **Unit Conversion**: If data is in weight percent (wt%), convert to atomic percent (at%) using standard atomic weights.

### 2. Data Independence Verification
- **Protocol**: Explicitly filter for records where Poisson's ratio is measured via **Ultrasonic** or **Resonant** methods.
- **Derived Values**: If metadata indicates the value is derived from Young's Modulus (E) and Shear Modulus (G) without independent measurement of G, the record is excluded. This prevents the model from learning the mathematical identity $\nu = E/(2G) - 1$.

### 3. Feature Engineering
- **Compositional Transformation**: Apply **Isometric Log-Ratio (ILR)** transformation to the atomic fractions.
- **Basis Definition**: Use a **Sequential Binary Partition (SBP)** based on periodic table groups (e.g., (Cu, Mg) vs (Si, Zn, Mn) vs Al) to ensure reproducibility of the ILR coordinates.
- **Target**: Poisson's ratio.

### 4. Modeling
- **Algorithm**: Random Forest Regressor.
- **Validation**:
  - 5-fold Cross-Validation on the training set.
  - 80/20 Train/Test split (held-out test set).
- **Metrics**: Mean Absolute Error (MAE).
- **Threshold**: If CV MAE > 0.05, compare against a **Null Baseline** (predicting the mean). If the model performs no better than the mean, flag as "No Signal Detected".

### 5. Interpretation
- **Feature Importance**: Extract via **Grouped ILR Importance**. This aggregates the importance of ILR coordinates based on their underlying log-ratios (e.g., log(Cu/Al), log(Mg/Al)) to rank elements. This is mathematically sound for compositional data and avoids invalid back-transformation.
- **Collinearity**: Compute Variance Inflation Factors (VIF) on the **ILR-transformed features** (not raw compositions). Flag if any VIF > 5.
- **Framing**: All results are explicitly labeled as **associational**, not causal.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Not required, as the primary outcome is a single continuous variable (Poisson's ratio).
- **Power Analysis**: Minimum N=50 required. If N < 50, the pipeline halts. This ensures sufficient power to detect non-trivial effect sizes and stable feature importance.
- **Causal Claims**: Explicitly avoided. The dataset is observational; no randomization or identification strategy is present.
- **Collinearity**: Addressed via ILR transformation for modeling. VIF is computed on ILR features to detect remaining redundancy. Raw VIF is not computed (infinite due to closure).
- **Measurement Validity**: The pipeline will filter for Poisson's ratio values derived from independent measurements (e.g., ultrasonic) if metadata is available. Records with missing or ambiguous metadata are excluded by default.

## Compute Feasibility

- **CPU-First**: Random Forest on <2000 samples is trivial for CPU.
- **Memory**: <2000 rows × ~10 columns fits easily in 7 GB RAM.
- **Time**: Training and inference will take <30 minutes.
- **GPU**: Not required. The plan does not use deep learning or CUDA.

## Risk Mitigation

- **Data Scarcity**: If <50 entries are found (or <50 after independence filtering), the project halts with a clear error.
- **Missing Variables**: If a required element (e.g., Mn) is missing in a row, the row is excluded.
- **API Failure**: If Materials Project/NIST APIs are down or require auth not provided, the pipeline halts.
- **Model Performance**: If Test MAE > 0.05 AND > Null Baseline, the result is flagged as "No Signal Detected" or "High Noise".