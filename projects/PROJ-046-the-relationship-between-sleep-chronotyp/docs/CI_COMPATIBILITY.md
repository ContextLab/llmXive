# CI Runner Compatibility Verification

This document describes the compatibility verification process for the Sleep Chronotype project, ensuring that all pipeline components can run within the specified CI runner constraints.

## Constraints

The CI runner environment must meet the following requirements:

- **CPU**: At least 2 cores
- **RAM**: At least 7 GB
- **GPU**: Not required (CPU-only execution)
- **R Version**: 4.3+
- **Dependencies**: All R packages must be manageable via `renv`

## Verification Script

The project includes a verification script that checks these constraints:

```bash
# From the project root:
python code/07_verify_ci_compatibility.py
```

### What the Script Checks

1. **CPU Cores**: Verifies at least 2 CPU cores are available
2. **RAM**: Verifies at least 7 GB of RAM is available
3. **GPU**: Confirms the environment is CPU-only (no GPU required)
4. **R Installation**: Checks that R 4.3+ is installed and accessible
5. **renv Initialization**: Verifies that `renv` is properly initialized with `renv.lock` and `renv/` directory

### Expected Output

A successful run will produce output like:

```
============================================================
CI Runner Compatibility Verification
============================================================

Results:
------------------------------------------------------------
[PASS] CPU Cores: CPU cores: 4 (required: >= 2)
[PASS] RAM: 8.00 GB (required: >= 7 GB)
[PASS] GPU (CPU-only): No GPU detected (CPU-only environment as required)
[PASS] R Installation: R version 4.3.2 installed
[PASS] renv: renv initialized (renv.lock and renv/ directory present)
------------------------------------------------------------
All CI compatibility checks PASSED.
The environment meets the requirements: 2 CPU, 7GB RAM, no GPU.
```

### Exit Codes

- `0`: All checks passed
- `1`: One or more checks failed

## Integration with CI/CD

This script should be run as part of the CI pipeline setup to ensure the runner environment is compatible before executing the main analysis pipeline.

Example GitHub Actions step:

```yaml
- name: Verify CI Compatibility
 run: python code/07_verify_ci_compatibility.py
```

## Troubleshooting

### Common Issues

1. **Insufficient CPU Cores**
 - Ensure the runner has at least 2 CPU cores allocated
 - Check cloud provider runner configuration

2. **Insufficient RAM**
 - Verify the runner has at least 7 GB of RAM
 - Consider upgrading the runner tier if running on cloud infrastructure

3. **R Not Found**
 - Ensure R is installed and added to the PATH
 - For Ubuntu: `sudo apt-get install r-base`
 - For macOS: Install via Homebrew: `brew install r`

4. **renv Not Initialized**
 - Run the setup tasks (T001-T003) to initialize `renv`
 - Ensure `renv.lock` and `renv/` directory exist in the project root

## Platform-Specific Notes

### Linux
- Uses `/proc/meminfo` for RAM detection
- Uses `os.cpu_count()` for CPU detection

### macOS
- Uses `sysctl` for RAM detection
- Uses `os.cpu_count()` for CPU detection

### Windows
- Uses Windows API for RAM detection
- Uses `os.cpu_count()` for CPU detection

## Maintenance

If the CI runner constraints change, update both:
1. This documentation
2. The thresholds in `code/07_verify_ci_compatibility.py`
