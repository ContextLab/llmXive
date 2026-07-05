# Deployment Guide

## Overview

This guide describes how to deploy the "Assessing the Impact of Data Resolution on Statistical Power" pipeline in a production environment.

## Requirements

- Python 3.9+
- 7GB+ RAM
- Disk space for raw and derived data (~10GB)
- Internet access for initial data download

## Deployment Steps

1. **Clone Repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-421-assessing-the-impact-of-data-resolution-
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Configure Environment**:
 - Edit `code/config.py` with production paths and API keys.
 - Set environment variables if needed (e.g., `HF_TOKEN`).

4. **Run Pipeline**:
 ```bash
 python code/setup_dirs.py
 python code/data_ingestion.py
 python code/resampling.py
 python code/analysis.py
 python code/generate_final_report.py
 ```

5. **Verify Outputs**:
 - Check `data/results/final_report.md` for completion.
 - Verify `figures/power_curve.png` exists.

## Automation

The pipeline can be automated via cron or a job scheduler. Example cron job:
```
0 2 * * * cd /path/to/project && python code/generate_final_report.py >> logs/cron.log 2>&1
```

## Monitoring

- Monitor disk usage for `data/` directories.
- Check logs for errors.
- Verify output integrity periodically.

## Scaling

For larger regions or higher resolutions, consider:
- Increasing RAM.
- Using distributed processing (future work).
- Optimizing window sizes in `utils.py`.
