# Implementation Notes

## Reproducibility Strategy
The project strictly adheres to Constitution Principle I: Reproducibility.
- **Seed Management**: `code/config.py` implements `verify_and_apply_seed()`. If `DOOMSCROLL_SEED` is not set in the environment, a warning is logged, and the run proceeds only if explicitly allowed, but the seed is not applied.
- **Logging**: Every random seed applied is logged with the timestamp and value.

## Data Integrity
- **No Synthetic Data**: The pipeline is designed to fail if the real data source is unreachable. No fallback to synthetic data generation is implemented to prevent fabrication.
- **Mathematical Coupling**: The `check_construct_validity` function in `validity.py` explicitly checks if `baseline_anxiety` and `anxiety_score` are derived from the same items. If they are identical, the process halts immediately.

## Statistical Rigor
- **Power Analysis**: A hard stop is enforced if $N < 30$ post-cleaning. A warning is issued if $30 \le N < 100$.
- **Assumption Checking**: The `model.py` module includes automated checks for linearity, homoscedasticity (Breusch-Pagan), and normality (Shapiro-Wilk). Results are saved to the JSON output files.

## Robustness Logic
The robustness check in `robustness.py` is conditional:
- It calculates the correlation between `social_media_engagement` and `news_exposure_freq`.
- The subset analysis is **only** performed if $r > 0.3$. Otherwise, a warning is logged, and the full sample results are used as the primary finding.

## Future Considerations
- **Proxy Flagging**: The logic for distinguishing `general_anxiety` from `anticipatory_anxiety` (FR-008) is currently a placeholder for future expansion if the dataset metadata requires dynamic mapping.
- **Performance**: For datasets > 10k rows, consider implementing chunked processing in `ingest.py` and `clean.py`.
