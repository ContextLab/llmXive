# CI/CD Setup Guide

This document provides instructions for setting up continuous integration for the Sleep Chronotype and Moral Judgement study pipeline.

## CI Runner Requirements

### Hardware Specifications
- **CPU**: 2 cores minimum
- **RAM**: 7 GB minimum
- **GPU**: Not required (CPU-only execution)
- **Disk**: 14 GB free space minimum

### Software Stack
- **R**: Version 4.3 or higher
- **Python**: Version 3.8 or higher
- **Git**: Latest stable version

## CI Configuration

### GitHub Actions Example

```yaml
name: Pipeline CI

on:
 push:
 branches: [ main, develop ]
 pull_request:
 branches: [ main, develop ]

jobs:
 setup-and-validate:
 runs-on: ubuntu-latest

 steps:
 - uses: actions/checkout@v3

 - name: Set up R
 uses: r-lib/actions/setup-r@v2
 with:
 r-version: '4.3'

 - name: Set up Python
 uses: actions/setup-python@v4
 with:
 python-version: '3.9'

 - name: Install R dependencies
 run: |
 Rscript -e "install.packages('renv')"
 Rscript code/00_setup_r_env.py

 - name: Set up project structure
 run: |
 python code/setup_project_structure.py
 python code/setup_data_structure.py

 - name: Run unit tests
 run: |
 Rscript -e "testthat::test_dir('tests/')"

 - name: Validate quickstart
 run: |
 python code/06_validate_quickstart.py

 - name: Verify CI compatibility
 run: |
 python code/07_verify_ci_compatibility.py

 - name: Run full pipeline
 run: |
 Rscript code/01_ingest.R
 Rscript code/02_classify.R
 Rscript code/02.5_aggregate_exclusions.R
 Rscript code/02.6_reliability.R
 Rscript code/03_analysis.R
 Rscript code/07_regression_test.R
 python code/04_render_report.py
 python code/05_validate_report.py

 - name: Upload artifacts
 uses: actions/upload-artifact@v3
 with:
 name: analysis-results
 path: |
 reports/
 data/derived/
 logs/
```

### GitLab CI Example

```yaml
stages:
 - setup
 - test
 - analyze
 - validate

variables:
 R_VERSION: "4.3"
 PYTHON_VERSION: "3.9"

setup:
 stage: setup
 image: rocker/r-ver:${R_VERSION}
 script:
 - apt-get update && apt-get install -y python3 python3-pip
 - pip3 install -r requirements.txt
 - Rscript -e "install.packages('renv')"
 - Rscript code/00_setup_r_env.py
 - python3 code/setup_project_structure.py
 - python3 code/setup_data_structure.py

unit-tests:
 stage: test
 image: rocker/r-ver:${R_VERSION}
 script:
 - Rscript -e "testthat::test_dir('tests/')"
 artifacts:
 reports:
 when: always
 paths:
 - logs/

quickstart-validate:
 stage: test
 image: rocker/r-ver:${R_VERSION}
 script:
 - python3 code/06_validate_quickstart.py

ci-compatibility:
 stage: test
 image: rocker/r-ver:${R_VERSION}
 script:
 - python3 code/07_verify_ci_compatibility.py

full-pipeline:
 stage: analyze
 image: rocker/r-ver:${R_VERSION}
 script:
 - Rscript code/01_ingest.R
 - Rscript code/02_classify.R
 - Rscript code/02.5_aggregate_exclusions.R
 - Rscript code/02.6_reliability.R
 - Rscript code/03_analysis.R
 - Rscript code/07_regression_test.R
 - python3 code/04_render_report.py
 - python3 code/05_validate_report.py
 artifacts:
 paths:
 - reports/
 - data/derived/
 - logs/
 expire_in: 1 week
```

## Resource Monitoring

### Memory Usage
Monitor memory usage during pipeline execution:
```bash
# Before running pipeline
free -h

# During execution (in another terminal)
top -p <PID>
```

### CPU Usage
```bash
# Check CPU cores available
nproc

# Monitor CPU during execution
top -H -p <PID>
```

### Disk Space
```bash
# Check available disk space
df -h
```

## Troubleshooting CI Issues

### Common CI Failures

1. **Out of Memory**
 - Increase CI runner RAM allocation
 - Reduce dataset size if possible
 - Add memory monitoring steps

2. **Timeout**
 - Increase job timeout limits
 - Optimize slow scripts
 - Add caching for dependencies

3. **Missing Dependencies**
 - Ensure all packages are listed in `requirements.txt` or `renv.lock`
 - Verify package installation steps in CI config

4. **Permission Errors**
 - Check file permissions in CI environment
 - Ensure scripts are executable

### Debugging Tips

1. **Enable verbose logging**
 ```yaml
 env:
 VERBOSE: "true"
 ```

2. **Add debugging steps**
 ```yaml
 - name: Debug info
 run: |
 R --version
 python --version
 free -h
 df -h
 ```

3. **Save intermediate artifacts**
 ```yaml
 artifacts:
 paths:
 - logs/
 - data/processed/
 ```

## Performance Optimization

### Caching Dependencies
Cache R and Python packages to speed up CI runs:

```yaml
- name: Cache R packages
 uses: actions/cache@v3
 with:
 path: ${{ env.R_LIBS_USER }}
 key: ${{ runner.os }}-r-${{ hashFiles('**/renv.lock') }}

- name: Cache Python packages
 uses: actions/cache@v3
 with:
 path: ~/.cache/pip
 key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

### Parallel Execution
Run independent tasks in parallel:
```yaml
- name: Run parallel tests
 run: |
 Rscript tests/test-classify.R &
 Rscript tests/test-analysis.R &
 wait
```

## Security Considerations

### Environment Variables
Store sensitive data as CI environment variables:
- API keys
- Database credentials
- Private data paths

### Data Privacy
- Never commit raw data to version control
- Use `.gitignore` to exclude sensitive files
- Sanitize logs before uploading

## Monitoring and Alerts

### Build Status
- Configure notifications for build failures
- Set up Slack/Discord integration

### Performance Metrics
Track:
- Build duration
- Resource usage
- Test coverage

## Best Practices

1. **Fail fast**: Run quick checks before long-running tasks
2. **Cache dependencies**: Reduce installation time
3. **Parallelize**: Run independent tasks concurrently
4. **Monitor resources**: Ensure CI runner has sufficient capacity
5. **Keep artifacts**: Save logs and outputs for debugging
6. **Document**: Maintain up-to-date CI configuration
