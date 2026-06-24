# Quickstart: Running the Knot‑Complexity Analysis

These instructions assume you have a recent version of Git and Python 3.11 installed.

## 1. Clone the repository
```bash
git clone https://github.com/your-org/quantifying-knot-complexity.git
cd quantifying-knot-complexity
```

## 2. Set up the Python environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Download the raw Knot Atlas data
```bash
python -m code.download.knot_atlas_loader \
    --output data/raw/knot_atlas_raw.json \
    --max-retries 5 \
    --initial-delay 1 \
    --max-delay 32
```
The script implements exponential‑backoff (FR) and caches partial results after a few consecutive failures.

## 4. Parse and clean the dataset
```bash
python -m code.data.parser \
    --input data/raw/knot_atlas_raw.json \
    --output data/processed/knots_cleaned.csv
python -m code.data.validator \
    --input data/processed/knots_cleaned.csv \
    --output data/processed/knots_validated.csv
```
The validator adds `data_quality_flags` and `missing_invariant_flags` (FR‑002, FR‑009) and writes a checksum manifest.

## 5. Verify core‑invariant precision (SC‑008)
```bash
python -m code.analysis.precision \
    --dataset data/processed/knots_validated.csv \
    --reference https://knotinfo.org/api/lookup
```
The step aborts if the braid‑index match rate falls below an acceptable core‑invariant coverage threshold.

## 6. Generate data‑quality reports (SC‑013)
```bash
python -m code.analysis.generate_quality_reports \
    --input data/processed/knots_validated.csv \
    --output docs/reproducibility/
```
Creates `data_quality_report.md` and `invariant_coverage.md`.

## 7. Document tie‑breaking rules (SC‑007)
```bash
python -m code.data.tie_breaker \
    --output docs/reproducibility/tie_breaking_rules.md
```

## 8. Filter to hyperbolic knots (FR‑012)
```bash
python -m code.analysis.filter_hyperbolic \
    --input data/processed/knots_validated.csv \
    --output data/processed/hyperbolic_knots.csv
```
Excludes records with `hyperbolic_volume = 0` and writes `hyperbolic_exclusions.md`.

## 9. Cross‑check hyperbolic volume (FR‑013, SC‑014)
```bash
python -m code.analysis.validation_phase2 \
    --dataset data/processed/hyperbolic_knots.csv \
    --reference https://knotinfo.org/api/volume \
    --output docs/reproducibility/validation_scope.md
```

## 10. Compute correlations and effect sizes (FR‑006, SC‑009)
```bash
python -m code.analysis.correlations \
    --dataset data/processed/hyperbolic_knots.csv \
    --output docs/correlations/
```
Outputs include Spearman ρ, Pearson r, Cohen’s d, mean differences and variance ratios.

## 11. Fit regression models (including alternating as covariate) and assess multicollinearity (FR‑005, SC‑005, SC‑002)
```bash
python -m code.analysis.regression_with_alternating \
    --dataset data/processed/hyperbolic_knots.csv \
    --output-dir docs/models
```
Outputs:
- `model_summary.csv`
- VIF report (`multicollinearity_assessment.md`).

## 12. Residual family analysis (FR‑011, SC‑012)
```bash
python -m code.analysis.residuals \
    --model docs/models/best_model.pkl \
    --dataset data/processed/hyperbolic_knots.csv \
    --output docs/reproducibility/residual_analysis.md
```

## 13. Additional invariants (Phase 9, SC‑010)
```bash
python -m code.analysis.additional_invariants \
    --input data/processed/hyperbolic_knots.csv \
    --output docs/additional_invariants/
```
Computes arc index, Seifert circle count, bridge number and validates against KnotInfo (≥ 90 % match).

## 14. Review reproducibility artefacts
- Checksums: `docs/reproducibility/checksums.sha256`  
- Random seeds: `docs/reproducibility/random_seeds.md`  
- Full log: `docs/reproducibility/run.log`

All artefacts are version‑controlled; re‑running the pipeline from step 3 on a fresh runner reproduces identical results.

## Verified Datasets
- **Knot Atlas** – Primary source of knot invariants. URL: https://katlas.org (verified dataset).  
