# CI Verification Guide

## Overview

This document describes the CI verification process for the Sleep Chronotype and Moral Judgement project.
The verification ensures that the CI runner meets the required resource constraints before executing the analysis pipeline.

## Resource Constraints

The project requires the following minimum resources:

- **CPU**: 2 cores minimum
- **RAM**: 7 GB minimum
- **GPU**: Not required (CPU-only execution)
- **R**: Version 4.3 or higher
- **renv**: Initialized project environment

## Verification Process

### Running the Verification Script

To verify CI compatibility, run the following command:

```bash
python code/07_verify_ci_compatibility.py
```

This script will check all required resources and report the results.

### Expected Output

The script will output a summary of each check:

```
============================================================
CI COMPATIBILITY VERIFICATION
============================================================
✓ PASS | CPU Cores: CPU cores check passed: 4 cores available
✓ PASS | RAM: RAM check passed: 8.00 GB available
✓ PASS | GPU Status: No GPU detected (acceptable for this project)
✓ PASS | R Installation: R version check passed: 4.3.1
✓ PASS | renv Initialization: renv is initialized
============================================================
OVERALL: CI environment is COMPATIBLE
```

### Exit Codes

- `0`: All checks passed, CI environment is compatible
- `1`: One or more checks failed, CI environment is incompatible

## CI Integration

### GitHub Actions

Add the following step to your CI workflow:

```yaml
- name: Verify CI Compatibility
 run: python code/07_verify_ci_compatibility.py
 if: ${{ runner.os == 'Linux' }}
```

### GitLab CI

Add the following job to your `.gitlab-ci.yml`:

```yaml
verify_ci_compatibility:
 stage: setup
 script:
 - python code/07_verify_ci_compatibility.py
 rules:
 - if: $CI_RUNNER_OS == "Linux"
```

### Jenkins

Add the following step to your Jenkinsfile:

```groovy
stage('Verify CI Compatibility') {
 steps {
 sh 'python code/07_verify_ci_compatibility.py'
 }
}
```

## Troubleshooting

### Common Issues

#### Insufficient CPU Cores

**Error**: "Insufficient CPU cores: 1 (minimum 2 required)"

**Solution**: Use a CI runner with at least 2 CPU cores.

#### Insufficient RAM

**Error**: "Insufficient RAM: 4.00 GB (minimum 7 GB required)"

**Solution**: Use a CI runner with at least 7 GB of RAM.

#### R Not Installed

**Error**: "R is not installed or not in PATH"

**Solution**: Install R 4.3 or higher on the CI runner.

#### renv Not Initialized

**Error**: "renv is not initialized (missing renv.lock or renv/ folder)"

**Solution**: Run `Rscript code/00_setup_r_env.py` to initialize renv before running the verification.

## Verification Results

The verification results are also saved to `code/07_ci_verification_results.json` in JSON format for programmatic access.

## Maintenance

Update this document when:

- Resource requirements change
- New verification checks are added
- CI platform configuration changes
- Troubleshooting steps are updated