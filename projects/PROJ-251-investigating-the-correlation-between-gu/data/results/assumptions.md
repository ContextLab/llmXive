# Assumptions and Methodology Documentation

## Limit of Detection (LOD) Handling

**Task**: T011d - Merge Microbiome and Serology

### Choice Documented
In accordance with the project specification's edge case requirements, we have chosen to **impute** missing or non-detectable titer values rather than exclude the subjects entirely.

### Rationale
Antibody titers often report "ND" (Not Detected) or "0" when the concentration is below the assay's Limit of Detection. Excluding these subjects would lead to a significant loss of data, particularly in populations with low pre-vaccination immunity or weak post-vaccination responses. Imputation allows us to retain these subjects for analysis while acknowledging the uncertainty of the exact value.

### Implementation Details
- **Missing Value Indicators**: 'ND', '0', and explicit `NaN` values in `titer_baseline` and `titer_post` columns.
- **Imputation Value**: The default Limit of Detection (LOD) is set to **10.0**. Values marked as missing are imputed as **0.5 * LOD = 5.0**.
- **Configuration**: This behavior is controlled by `config.get_lod_handling_methods()` and `config.get_impute_lod()`. If `config.LOD_VALUE` is not explicitly set, the default of 10.0 is used.
- **Fallback**: If the LOD is undefined in the configuration and values are missing, the row is excluded (though the default is applied first).

### Reference
- Spec Edge Cases: "treat these as a specific value... with the choice documented".
- Task T011d Logic: Impute as a fraction of the limit of detection.
