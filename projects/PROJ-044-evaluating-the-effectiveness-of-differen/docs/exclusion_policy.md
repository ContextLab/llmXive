# Dataset Exclusion Policy

## Shakespeare Dataset Exclusion

This project explicitly **excludes** the Shakespeare dataset from the LEAF benchmark.

### Rationale

According to the project's `plan.md` Gap Analysis:
1. **No Verified Source**: There is no verified, programmatic source (e.g., a stable Hugging Face `datasets` ID or direct download URL) for the Shakespeare dataset that meets the project's reliability standards.
2. **Reproducibility Risk**: Attempting to fetch from unverified mirrors or hard-coded paths introduces significant reproducibility risks.
3. **Focus on FEMNIST**: FEMNIST provides a sufficient and verified testbed for the study's hypotheses regarding heterogeneity and differential privacy.

### Implementation

Any attempt to use the "shakespeare" dataset in the codebase will result in a clear error:

```python
if dataset_name != "femnist":
 raise ValueError(
 f"Dataset '{dataset_name}' is excluded per plan.md Gap Analysis. "
 "Only 'femnist' is supported."
)
```

This check is enforced in:
- `code/config.py` (Configuration validation)
- `code/data/download.py` (Data fetching logic)
- `code/data/partition.py` (Partitioning logic)

## Future Considerations

If a verified source for the Shakespeare dataset becomes available in the future, this policy may be revisited. Until then, all experiments and documentation are strictly FEMNIST-only.
