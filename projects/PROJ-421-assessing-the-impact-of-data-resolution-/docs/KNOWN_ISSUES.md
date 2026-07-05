# Known Issues

## Current Issues

### None

## Resolved Issues

### Issue: Memory error during analysis
**Status**: Resolved
**Solution**: Implemented windowed I/O in `utils.py`.

### Issue: Download timeout
**Status**: Resolved
**Solution**: Added retry logic with exponential backoff.

### Issue: Checksum mismatch
**Status**: Resolved
**Solution**: Verified source URL and updated checksums.

## Future Issues

- **Large Region Analysis**: May require distributed processing.
- **High Resolution**: May exceed memory limits even with windowed I/O.
- **Complex Land Cover**: Binary indicator map may oversimplify patterns.

## Reporting Issues

If you encounter a new issue, please report it on the project repository with:
- Description of the issue.
- Steps to reproduce.
- Expected vs. actual behavior.
- Logs (if applicable).
