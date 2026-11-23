# Design Decisions: Investigating the Validity of the Equipartition Theorem

## Primary Frequency Bin Selection

### Decision
The "primary frequency bin" used for Stability Check (SC-003) verification is defined as the **median of the unique frequency bin values** present in `data/derived/energy_samples.csv`.

### Justification

1. **Robustness to Outliers**: The median is a robust statistic that is less sensitive to extreme values or skewed distributions of frequency bins compared to the mean. In driven granular systems, the frequency spectrum may contain outliers due to transient driving conditions or experimental noise. Using the median ensures the primary bin represents the "typical" driving condition rather than being skewed by rare high-frequency events.

2. **Representativeness**: The median of unique frequency bins provides a central tendency that is guaranteed to be one of the actual observed frequency bins in the dataset. This ensures that the primary bin is always a valid, observed experimental condition rather than an interpolated or extrapolated value.

3. **Reproducibility**: The selection rule is deterministic and can be exactly reproduced by any researcher with access to `energy_samples.csv`. The algorithm is:
 - Extract all unique frequency bin values from the `frequency_bin` column.
 - Sort them in ascending order.
 - Select the median value (if even number of unique values, select the lower median or the average of the two middle values; in our implementation, we use `np.median` which returns the average of the two middle values if necessary).

4. **Alignment with SC-003 Requirements**: SC-003 requires verifying that the rejection decision remains identical across significance thresholds ($\alpha \in \{0.01, 0.05, 0.10\}$) and discrepancy boundaries. By selecting a single, well-defined "primary frequency bin," we create a consistent reference point for this stability analysis. The median choice ensures this reference point is stable even if the dataset is slightly modified (e.g., addition of a few new frequency bins at the extremes).

5. **Independence from Sample Size**: Unlike the mean, the median is not influenced by the number of samples in each bin. This is critical because frequency bins with higher sample counts (often lower frequencies in granular experiments) would otherwise dominate the selection if a weighted average were used.

### Implementation Details

- **Source File**: `data/derived/energy_samples.csv`
- **Column**: `frequency_bin`
- **Algorithm**: `np.median(np.unique(df['frequency_bin'].dropna()))`
- **Edge Case Handling**: If the dataset contains no frequency bins (empty or all NaN), the task will raise a `RuntimeError` indicating insufficient data for SC-003 verification.

### Traceability

- **Spec Reference**: SC-003 (Stability Check) requires a defined "primary frequency bin" for robustness verification.
- **Plan Reference**: Plan Methodology Updates specify that stability checks must be performed on a representative, stable reference bin.
- **User Story**: US3 (Sensitivity Analysis and Threshold Justification)

### Alternatives Considered

1. **Mean of Unique Bins**: Rejected due to sensitivity to outliers and potential for selecting a non-observed frequency value.
2. **Mode (Most Frequent) Bin**: Rejected because it depends on sample count distribution rather than the range of observed frequencies, potentially biasing toward low-frequency bins with longer observation times.
3. **First Bin**: Rejected as it is arbitrary and not representative of the full experimental range.
4. **User-Specified Bin**: Rejected to maintain objectivity and reproducibility; the selection rule must be data-driven, not user-configurable.

### Conclusion

The median of unique frequency bins provides a statistically robust, reproducible, and representative definition for the "primary frequency bin" required by SC-003. This choice ensures that the stability analysis is conducted on a meaningful and stable reference point, independent of sample size imbalances or extreme frequency outliers.