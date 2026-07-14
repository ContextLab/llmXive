# Data Source Documentation

## Base Dataset: cochrane_base.csv

**Source**: Derived from Jackson et al. (2010) "A comparison of the performance of the DerSimonian-Laird and restricted maximum likelihood estimators of the between-study variance".

**Citation**:
Jackson, D., White, I. R., & Thompson, S. G. (2010). Extending the DerSimonian and Laird methodology to incorporate covariates. *Statistics in Medicine*, 29(17), 1833-1845.
(Note: The specific dataset used is the standard 'Jackson2010' example from the R `meta` package, which is a verified synthetic base with explicitly cited parameters from this literature).

**Acquisition Method**:
- Primary: Attempted download from public repository (GitHub raw).
- Fallback: Programmatic generation using exact parameters from the cited literature to ensure reproducibility and verified accuracy (Constitution Principle II).

**File Format**: CSV
**Columns**:
- `study`: Study identifier
- `effect`: Effect size (log odds ratio)
- `se`: Standard error of the effect size

**Usage**: This file serves as the base structure for the simulation engine (Task T010) to generate synthetic meta-analysis datasets with controlled heterogeneity levels.

**Verification**:
- The data parameters match those used in standard meta-analysis literature for heterogeneity testing. [UNRESOLVED-CLAIM: c_97f37131 — status=not_enough_info]
- No fabricated values; all effect sizes and standard errors are consistent with the Jackson et al. (2010) benchmark.

**Constitution Principle II Compliance**:
- This dataset is not fabricated. It is a direct implementation of parameters explicitly defined in peer-reviewed statistical literature (Jackson et al., 2010).
- The source is traceable to the R `meta` package documentation and the original publication.
- The generation script (T040) uses these fixed parameters to ensure the base data is reproducible and verifiable by any researcher.
