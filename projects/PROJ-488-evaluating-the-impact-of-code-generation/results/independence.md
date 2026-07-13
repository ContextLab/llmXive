# Independence Mitigation Report

**Method Used**: subsample

**Original Snippet Count**: 2000
**Final Snippet Count**: 847
**Number of Unique Repositories**: 847

## Approach

Subsampling was performed to ensure at most one snippet per repository.
This eliminates within-repository correlation by treating each repository
as an independent unit.

Algorithm:
1. Group all snippets by repository identifier.
2. Randomly select one snippet from each group.
3. Use the selected subset for all subsequent statistical tests.

## Details

**subsample_path**: data/processed/independence_subsampled.json
**unique_repositories**: 847

## Conclusion

Independence assumptions have been addressed using the chosen method.
Statistical tests should be interpreted with this mitigation in mind.