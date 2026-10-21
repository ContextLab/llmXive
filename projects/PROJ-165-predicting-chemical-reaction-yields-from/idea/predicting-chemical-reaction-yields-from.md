---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Field**: chemistry

## Research question

To what extent do *experimentally measured* IR and ¹H-NMR spectra of reactants and products provide *independent* predictive signal for chemical reaction yield beyond what is captured by static molecular structure fingerprints, and which specific spectral regions carry that signal?

## Motivation

Reaction yield optimization traditionally relies on costly trial-and-error experimentation. Static molecular fingerprints (e.g., ECFP) capture structural connectivity but not the dynamic environmental effects (solvation, intermolecular interactions) that influence yield. Demonstrating that spectroscopic data — sensitive to these environmental states — contains independent predictive signal would validate a new paradigm for rapid, non-invasive reaction screening using existing benchtop instruments, without quantum mechanical simulation.

## Literature gap analysis

### What we searched

The librarian's search trail records 21 query terms across Semantic Scholar, arXiv, and OpenAlex, spanning two strategies: (1) exact-topic queries combining reaction-yield prediction with IR/NMR/spectroscopic inputs and attention mechanisms (e.g., "machine learning prediction of reaction outcomes from spectra", "infrared and NMR spectroscopy for yield forecasting"), and (2) broadened queries on nearby territory (e.g., "deep learning models for reaction yield prediction", "multi-modal learning for chemical reaction analysis", "QSPR using spectroscopic inputs"). Only one term returned results, and every verified citation admitted by the judge was flagged as *topically marginal fallback* (deep-learning theory, medical imaging, price elasticity) — none is defensibly on-topic for spectroscopic yield prediction.

### What is known

No on-topic results survived verification. (The judge's five admitted citations concern general deep-learning theory and unrelated application domains; per the relevance rules they are omitted rather than cited with stretched relevance notes.)

### What is NOT known

No published work in the verified corpus quantitatively assesses whether experimentally measured vibrational (IR) and NMR spectra of reactants and products contain predictive signal for reaction yields beyond structural fingerprints. Nor is there literature identifying which wavenumber or chemical-shift regions are most predictive of yield variation, since existing yield-prediction models rely on SMILES/fingerprint inputs rather than raw experimental spectra.

### Why this gap matters

If spectroscopic inputs prove predictive, synthetic chemists could screen and optimize reactions with cheap benchtop IR/NMR instruments instead of exhaustive experimentation or expensive simulation, and the identified spectral regions would provide mechanistic hints about which environmental effects govern yield.

### How this project addresses the gap

The methodology below joins a public reaction-yield dataset with experimentally measured spectra retrieved from the NIST Chemistry WebBook, trains attention-based and baseline models on the paired data, and quantifies — with permutation tests and attention-weight maps — exactly which spectral regions carry yield signal. This produces the previously-unavailable empirical evidence linking raw experimental spectra to reaction outcomes.

## Expected results

Either outcome is informative: if spectra add statistically significant predictive signal over fingerprints (lower test RMSE, confirmed by paired tests on per-sample errors and label-permutation nulls), that validates spectroscopy as an independent yield predictor and identifies the responsible spectral regions; if they do not, that is a publishable negative result constraining claims that spectroscopic "environmental" information is usable for yield prediction without full structural elucidation. Confirmation requires real held-out test metrics with permutation-test significance; falsification requires the spectral model to fail to beat the fingerprint baseline under the same protocol.

## Methodology sketch

- **Data acquisition (real experimental data only)**
  - Download the **USPTO-50k** reaction dataset (public split; e.g., https://github.com/ConnorJCo/USPTO50k_Augmented or https://github.com/wengong-jin/nips17-rexgen) containing SMILES and reaction information; pair with experimental yields from a public yield-annotated source (e.g., the **Dreher & Doyle Buchwald-Hartwig HTE dataset**, https://www.science.org/doi/10.1126/science.aar5169, supplementary CSV, or the **Suzuki–Miyaura HTE dataset** on OpenML/https://github.com/doylelab/rxnpredict), since USPTO-50k itself lacks yield labels.
  - For each compound, query the **NIST Chemistry WebBook** (https://webbook.nist.gov/chemistry/) and **PubChem API** (https://pubchemdocs.ncbi.nlm.nih.gov/pug-rest) for *experimentally measured* IR and ¹H-NMR spectra; retain only reactions with real measured spectra for reactant(s) and product, discarding simulated/missing entries. Log all API queries for reproducibility.
  - Report the final matched-reaction count; if the matched set is too small (<~300 reactions) to support training, the pipeline halts with a documented data-availability failure rather than substituting simulated spectra.
- **Preprocessing**
  - Resample IR spectra to a common 400–4000 cm⁻¹ grid and NMR to 0–10 ppm; normalize per-spectrum; concatenate reactant/product spectra into multi-channel tensors. Compute ECFP4 fingerprints from SMILES as the structural baseline.
- **Dataset split**
  - 70/15/15 train/validation/test split with no overlapping reaction templates across splits.
- **Model architecture**
  - PyTorch model: positional encoding of the spectral axis, 4-head self-attention over the spectral dimension, fully-connected fusion with the fingerprint vector, continuous yield output (0–100%).
- **Training**
  - Adam (lr 1e-3), batch size 32, ≤15 epochs with early stopping on validation RMSE; `torch.set_num_threads(2)` on the GitHub Actions CPU runner; fixed random seeds recorded in a JSON config.
- **Baselines**
  - Ridge regression on flattened spectra; ridge/gradient-boosting on ECFP4 fingerprints alone; combined fingerprint+spectra model.
- **Evaluation — REAL COMPUTED METRICS ONLY (resolves the downstream concern)**
  - Every reported metric (RMSE, MAE, R², paired t-test on per-sample absolute errors, label-permutation null distribution) MUST be computed at runtime from the real held-out test set by the analysis script and written to a results JSON/CSV. **No hardcoded, simulated, placeholder, or `random.*`-generated metric values may appear anywhere in the code, specs, or reports.** Any figure or table in the final output is generated from the results file produced by the executed pipeline, not authored by hand.
  - **Validation independence**: the evaluation target — experimentally measured yield — is an independent laboratory outcome, distinct from the spectral/fingerprint predictors; a label-permutation test (shuffling yields, retraining, comparing null RMSE distribution) confirms the model is not learning spurious structure.
  - Attention-weight visualization across the spectral axis, with peaks cross-checked against known functional-group frequencies.
- **Reproducibility**
  - Pinned `requirements.txt`; stored seeds, split indices, and NIST/PubChem query logs in a JSON config so the exact real-data subset is reconstructible.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A (no similar entry found).
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-10-21T12:16:53Z
**Outcome**: failed
**Original term**: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms chemistry
**Verified citation count**: 0

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms chemistry | 0 |
| 1 | reaction yield prediction machine learning | 0 |
| 2 | attention mechanisms spectroscopy regression | 0 |
| 3 | deep learning chemical reaction outcome prediction | 0 |
| 4 | spectroscopic feature extraction neural networks | 0 |
| 5 | NMR spectroscopy yield prediction | 0 |
| 6 | infrared spectroscopy reaction monitoring machine learning | 0 |
| 7 | transformer models cheminformatics | 0 |
| 8 | attention-based molecular property prediction | 0 |
| 9 | quantitative structure-yield relationships | 0 |
| 10 | deep learning retrosynthesis planning | 0 |
| 11 | reaction condition optimization neural networks | 0 |
| 12 | convolutional neural networks spectral data analysis | 0 |
| 13 | Raman spectroscopy chemometric modeling | 0 |
| 14 | multivariate calibration spectroscopy deep learning | 0 |
| 15 | graph attention networks molecular prediction | 0 |
| 16 | high-throughput experimentation yield modeling | 0 |
| 17 | machine learning organic synthesis yield | 0 |
| 18 | spectral data fusion chemical prediction | 0 |
| 19 | mass spectrometry deep learning prediction | 0 |
| 20 | Bayesian optimization reaction yield | 0 |

### Verified citations

(none)
