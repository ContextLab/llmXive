# Project Plan: Quantifying the Impact of Code Ownership

## Goal
Determine if higher code ownership concentration (Gini) correlates with higher bug density,
while controlling for code churn, complexity, size, and age.

## Methodology
1. **Data Collection**: Clone 10+ active Python repos with depth 1000.
2. **Ownership Calculation**: Parse git logs to calculate Gini per module.
3. **Quality Metrics**: Count bugs (issues) linked to modules via path proximity.
4. **Statistical Analysis**: Spearman correlation, VIF diagnostics, non-linearity tests.
5. **Sensitivity Analysis**: Sweep p-value thresholds and correlation cutoffs.

## Constraints
- **RAM**: Peak usage ≤ 7 GB (disk-based intermediate storage).
- **Time**: Total runtime ≤ 6 hours.
- **Data**: Raw git data gitignored; ownership CSVs version-controlled.
- **Framing**: Results are associational, not causal.

## Phases
1. Setup (Phase 1)
2. Foundational Infrastructure (Phase 2)
3. User Story 1: Data Collection (Phase 3)
4. User Story 2: Metrics Calculation (Phase 4)
5. User Story 3: Statistical Analysis (Phase 5)
6. Polish & Documentation (Phase N)

## Dependencies
- Python 3.11+
- GitHub API (requires token)
- Git installed locally
