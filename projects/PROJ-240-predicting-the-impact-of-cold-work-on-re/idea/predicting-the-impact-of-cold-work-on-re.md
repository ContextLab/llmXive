---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

**Field**: materials science

## Research question

How does the degree of prior cold work deformation quantitatively influence the time-to-peak softening during recrystallization in aluminum alloys, and can a regression model trained on public materials data predict this relationship across varying compositions?

## Motivation

Cold work is a critical processing step that determines the final mechanical properties of aluminum alloys, yet predicting the subsequent heat treatment response often relies on empirical heuristics. Establishing a data-driven quantitative link between deformation levels and recrystallization kinetics would optimize processing schedules and reduce trial-and-error experimentation in industrial settings.

## Related work

- [Understanding the kinetics of static recrystallization in Mg-Zn-Ca alloys using an integrated PRISMS simulation framework (2026)](http://arxiv.org/abs/2602.16701v1) — Defines the fundamental mechanism of recrystallization kinetics (dislocation density transformation), providing a theoretical baseline despite being focused on Magnesium alloys.
- [Mining experimental data from Materials Science literature with Large Language Models: an evaluation study (2024)](http://arxiv.org/abs/2401.11052v3) — Validates the feasibility of extracting structured experimental parameters (e.g., deformation %, temperature) from unstructured scientific text to build training datasets.

## Expected results

We expect to observe a non-linear relationship where increased cold work initially accelerates recrystallization (reduced time-to-peak) but saturates at high deformation levels. Confirmation will be achieved via a regression model (e.g., Random Forest) achieving an R² > 0.6 on a held-out test set of public alloy data.

## Methodology sketch

- **Data Acquisition**: Query the NIST Materials Data Repository (https://www.nist.gov/materials) and HuggingFace Datasets (https://huggingface.co/datasets) for "aluminum recrystallization" or "aluminum cold work" using `wget` or `curl` to retrieve CSV/JSON files.
- **Data Cleaning**: Parse raw text data using Python (pandas) to extract numeric features: cold work percentage, alloy composition (wt% Mg, Si, Cu), annealing temperature, and time-to-peak softening.
- **Feature Engineering**: Normalize composition variables and encode categorical alloy series (e.g., 5xxx, 6xxx) as one-hot vectors.
- **Model Training**: Train a Random Forest Regressor (Scikit-learn, CPU-only) to predict time-to-peak softening using cold work and composition as inputs.
- **Validation**: Perform 5-fold cross-validation to assess generalization; apply a t-test to compare predicted vs. actual means on the test fold to verify statistical significance (p < 0.05).
- **Resource Check**: Ensure all computation completes within 6 hours on a 2-CPU runner by limiting dataset size to <10,000 rows and avoiding GPU-dependent libraries.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None (similarity sketch: N/A).
- Verdict: NOT a duplicate
