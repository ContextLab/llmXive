# Sensitivity Analysis Plan

## 1. Limitation: Missing Medication Data

The primary dataset (OpenNeuro ds000030) lacks comprehensive medication status information for all subjects in its sidecar metadata. As confirmed by task **T015.5** (`code/preprocessing/metadata.py`), the `medication_status` field is absent from the available JSON sidecars. Consequently, the primary analysis cannot control for the potential confounding effects of antipsychotic medication on brain network metrics.

This absence enforces a strict interpretation of the primary results: **the findings are associational only**. We cannot claim that observed differences in graph metrics (e.g., global efficiency, centrality) are independent of medication effects.

## 2. Sensitivity Analysis Strategy: Simulated Covariates

To address this limitation and assess the robustness of our conclusions, we implement a sensitivity analysis plan as required by **FR-006**. This analysis treats the missing medication status as a "what-if" scenario.

### 2.1. Implementation Details
- **Source**: Task **T031** (`code/classification/sensitivity_analysis.py`).
- **Method**: A synthetic covariate `sim_med_status` is generated using a Bernoulli distribution with $p=0.5$ (seed=42) to simulate a realistic 50/50 split of medicated vs. unmedicated subjects.
- **Integration**: This simulated covariate is appended to the primary feature matrix (`data/processed/features.csv`) to create `data/processed/features_sim_med.csv`.
- **Execution**: The classification pipeline (Logistic Regression/SVM with nested CV) is re-run on this augmented dataset (Task **T031b**).

### 2.2. Rationale
By introducing a random but structured covariate that mimics the potential distribution of medication status, we can observe how the model's performance metrics (accuracy, p-value, Cohen's d) shift when a hidden confounder is explicitly modeled. If the results remain stable or the significance holds despite this artificial confounding, it strengthens the associational claim. Conversely, if the results degrade significantly, it highlights the fragility of the findings in the absence of real medication data.

## 3. Conclusion: Associational Only

The primary hypothesis test (Classification of Schizophrenia vs. Control based on brain network metrics) remains **associational only**. The simulation performed in this sensitivity analysis is strictly a "what-if" exploration and **does not** validate the primary hypothesis as causal or fully confounder-controlled.

The final report (Task **T032b**) will explicitly label the primary findings as "Exploratory (Underpowered)" or "Associational" depending on the outcome of the Minimum Detectable Effect (MDE) and the sensitivity analysis results. This transparency ensures compliance with **Constitution Principle VI** regarding the rigorous reporting of limitations and data gaps.

## 4. Policy Compliance

This plan adheres to the project's "Fail Loudly" policy (Task **T040**). No synthetic data is used to *replace* real measurements for the primary analysis. The simulation is isolated solely to the sensitivity analysis branch (`features_sim_med.csv`), ensuring the integrity of the primary feature set (`features.csv`) derived from real neuroimaging data.