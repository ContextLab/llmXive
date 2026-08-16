# Fallback Strategy Documentation

## Overview

This document details the escalation path and manual procedures to follow if the automated data collection pipeline (orchestrated by `code/collect/orchestrator.py` in Task T009c) fails to meet the minimum repository count requirement of **≥100 unique repositories**.

The primary data source is the HuggingFace dataset `akhousker/github-issues`. If this source is unavailable, invalid, or insufficient, the system automatically triggers a fallback to the GitHub API. If the API fallback also fails to meet the threshold, manual intervention is required.

## Automated Escalation Path

The `orchestrator.py` script implements the following logic:

1. **Primary Source Attempt**:
 - Attempt to load and validate the HuggingFace dataset (`akhousker/github-issues`) using `code/data/loader_hf.py`.
 - Validate against `contracts/dataset.schema.yaml`.
 - If valid and contains ≥100 unique repositories, proceed to preprocessing.
 - If invalid or insufficient, trigger Step 2.

2. **API Fallback Trigger**:
 - Load the curated repository list from `code/data/config.py`.
 - If the curated list is insufficient (<100 repos), invoke `code/data/discovery.py` to dynamically discover top-starred repositories via the GitHub API.
 - Fetch closed issues using `code/data/loader_api.py` with rate limit handling (≥60s wait).
 - Validate fetched data against `contracts/dataset.schema.yaml`.
 - If the combined count (Curated + Discovered) ≥100, merge data and proceed.
 - If the combined count <100, trigger **Fatal Error Handler** (Step 3).

3. **Fatal Error Condition**:
 - **Condition**: HuggingFace is unavailable/invalid AND API fallback (including dynamic discovery) yields <100 unique repositories.
 - **Action**: The orchestrator raises a `FatalError` with a clear message indicating the specific count achieved and the requirement failed.
 - **Output**: No `data/raw/*.parquet` file is written. The pipeline halts.

## Manual Repository List Expansion Procedure

If the automated pipeline halts due to the Fatal Error Condition, follow these steps to manually expand the repository list and re-run the collection.

### Step 1: Identify Missing Repositories

Review the error log from the orchestrator run to determine the current unique repository count.
- Example Error: `FatalError: Unique repository count (45) is below the required threshold (100).`
- Determine the number of additional repositories needed: `100 - current_count`.

### Step 2: Select High-Quality Repositories

Manually identify repositories that meet the following criteria to ensure data quality and language diversity:
- **Star Count**: ≥ 1,000 stars (ensures active community and issue history).
- **Activity**: Issues closed within the last 3 years (2022–2025).
- **Language Diversity**: Ensure representation across at least 5 distinct programming languages (e.g., Python, JavaScript, Java, C++, Go, Rust, Ruby).
- **Issue Volume**: Repositories should have a history of closed issues (avoid dormant projects).

**Recommended Sources for Discovery**:
- GitHub Trending (filter by language and time range).
- Awesome Lists (e.g., `awesome-python`, `awesome-javascript`).
- Major Open Source Foundation Repositories (Apache, CNCF, Linux Foundation).

### Step 3: Update the Curated List

1. Open the configuration file: `code/data/config.py`.
2. Locate the `CURATED_REPOSITORIES` list.
3. Append the new repository full names (format: `owner/repo`) to the list.
 ```python
 CURATED_REPOSITORIES = [
 # Existing entries...
 "new-owner/new-repo-1",
 "new-owner/new-repo-2",
 #...
 ]
 ```
4. Save the file.

### Step 4: Re-run the Collection Pipeline

Execute the collection pipeline again to fetch data for the expanded list:

```bash
python code/collect/orchestrator.py
```

The orchestrator will:
1. Skip the HuggingFace check (or re-verify if it was the failure point).
2. Use the updated `CURATED_REPOSITORIES` list.
3. Attempt to fetch issues via the GitHub API.
4. If the count now meets ≥100, it will merge and write `data/raw/github_issues_raw_api.parquet`.

### Step 5: Verification

After the pipeline completes:
1. Verify the existence of `data/raw/github_issues_raw_api.parquet`.
2. Run the completeness validation script (Task T011) to ensure the dataset meets the ≥95% completeness threshold.
3. Check `data/logs/completeness_report.json` for any schema violations.

## Contingency: API Rate Limit Exhaustion

If the manual expansion fails due to GitHub API rate limits (403 Forbidden):

1. **Wait**: The `loader_api.py` script automatically waits ≥60 seconds. If the limit is a hard reset (e.g., 5000 requests/hour), wait for the reset time.
2. **Token Rotation**: If using multiple GitHub tokens, ensure `code/utils/config.py` or environment variables are updated with additional tokens.
3. **Reduced Scope**: If tokens are exhausted, reduce the `PAGES_PER_REPO` limit in `code/data/loader_api.py` to fetch fewer pages per repository, prioritizing breadth (more repos) over depth (more issues per repo) to meet the ≥100 repo count.

## Compliance Notes

- **FR-001**: This strategy ensures the project can meet the ≥100 unique repository requirement even if the primary dataset source fails.
- **Constitutional Principle I**: All manual changes to `code/data/config.py` must be committed with a descriptive message linking to the specific repository additions.
- **Data Integrity**: Do not fabricate repository names or issue data. Only use real, publicly accessible GitHub repositories.

## Revision History

- **v1.0**: Initial implementation based on T009d requirements.
- **v1.1**: Added explicit steps for API rate limit exhaustion and token rotation.