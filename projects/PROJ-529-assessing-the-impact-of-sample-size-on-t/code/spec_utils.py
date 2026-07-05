"""
Utility functions for creating the specs directory structure and placeholder files.
"""
import os
import json
from typing import Dict, Any


def create_specs_structure(base_dir: str) -> None:
    """
    Create the specs directory structure and placeholder files.

    Args:
        base_dir: The base directory where the specs folder will be created.
    """
    # Define the directory structure
    directories = [
        "001-assessing-the-impact-of-sample-size-on-t",
    ]

    # Define the placeholder files for each directory
    # Each key is a directory, and the value is a dict of filename -> content
    files = {
        "001-assessing-the-impact-of-sample-size-on-t": {
            "plan.md": """# Plan: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Overview
This project investigates how sample size (number of studies, k) affects the stability
and reliability of meta-analytic estimates. We will analyze real-world meta-analyses
to determine the minimum k required for stable effect size estimates.

## Objectives
1. Acquire a corpus of real-world meta-analyses (or fallback to simulation)
2. Generate bootstrap subsamples for varying k values
3. Compute stability and coverage metrics
4. Detect diminishing returns thresholds using GAM modeling

## Success Criteria
- SC-001: Process at least 50 real-world meta-analyses
- SC-003: Identify minimum k for stable coverage (within ±2% of nominal)
- SC-006: Quantify sensitivity of thresholds to reference value perturbations

## Timeline
- Phase 1: Setup (1 week)
- Phase 2: Foundational (2 weeks)
- Phase 3: US1 - Data Acquisition (2 weeks)
- Phase 4: US2 - Metrics Computation (2 weeks)
- Phase 5: US3 - Threshold Detection (2 weeks)
""",
            "spec.md": """# Specification: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## User Stories

### US1: Data Acquisition and Subsampling Pipeline
As a researcher, I want to acquire real-world meta-analyses and generate bootstrap subsamples
so that I can analyze the impact of sample size on meta-analytic reliability.

**Acceptance Criteria:**
- AC-001: Download at least 50 meta-analyses from Cochrane/Campbell
- AC-002: Generate up to 100 bootstrap subsamples for each k (3 to N)
- AC-003: Log all subsample iterations with seeds and estimator types

### US2: Stability and Coverage Metric Computation
As a researcher, I want to compute pooled effect sizes and derive stability/coverage metrics
so that I can quantify the reliability of meta-analytic estimates at different sample sizes.

**Acceptance Criteria:**
- AC-004: Fit FE/RE models with appropriate estimator switching (DL for k≥10, REML for k<10)
- AC-005: Calculate SD of pooled effects across subsamples for each k
- AC-006: Compute CI coverage rates for each k

### US3: Threshold Detection and Visualization
As a researcher, I want to detect diminishing returns thresholds and generate diagnostic plots
so that I can identify the minimum k required for stable meta-analytic estimates.

**Acceptance Criteria:**
- AC-007: Fit GAM model to stability metrics and detect changepoint
- AC-008: Generate stability curve plots with confidence bands
- AC-009: Save threshold estimates to JSON and update research.md
""",
            "research.md": """# Research Notes: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Background
Meta-analyses combine results from multiple studies to produce a pooled effect estimate.
However, the reliability of these estimates depends on the number of studies (k) included.
This project investigates the relationship between k and meta-analytic stability.

## Key Questions
1. What is the minimum k required for stable effect size estimates?
2. How does coverage rate vary with k?
3. At what point do we observe diminishing returns in stability?

## Methodology
- Data: Real-world meta-analyses from Cochrane/Campbell (fallback: simulation)
- Subsampling: Bootstrap resampling for k = 3 to N
- Models: Fixed Effects (FE) and Random Effects (RE) with estimator switching
- Analysis: GAM modeling for threshold detection

## Preliminary Findings
*To be updated as analysis progresses*
""",
            "data-model.md": """# Data Model: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Entities

### MetaAnalysis
- meta_id: str (unique identifier)
- title: str
- source: str (Cochrane, Campbell, or Simulation)
- total_studies: int
- effect_sizes: List[float]
- standard_errors: List[float]
- pooled_effect: Optional[float]
- pooled_se: Optional[float]
- model_type: Optional[str] (FE or RE)

### Subsample
- subsample_id: str
- meta_id: str
- k: int (number of studies in subsample)
- seed: int
- effect_sizes: List[float]
- standard_errors: List[float]
- pooled_effect: float
- pooled_se: float
- model_type: str (FE or RE)
- estimator: str (DL, REML, etc.)

### StabilityMetric
- metric_id: str
- meta_id: str
- k: int
- sd_effects: float (standard deviation of pooled effects across subsamples)
- coverage_rate: float (proportion of CIs containing full-sample estimate)
- nominal_coverage: float (target coverage rate, e.g., 0.95)
- threshold_detected: bool
""",
            "contracts/api_endpoints.md": """# API Contracts: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Endpoints

### Data Acquisition
- `GET /api/v1/meta-analyses` - List all meta-analyses
- `GET /api/v1/meta-analyses/{meta_id}` - Get specific meta-analysis
- `POST /api/v1/download` - Trigger data download from Cochrane/Campbell

### Subsampling
- `POST /api/v1/subsample` - Generate bootstrap subsamples for given k values
- `GET /api/v1/subsamples/{meta_id}` - List all subsamples for a meta-analysis

### Metrics
- `GET /api/v1/metrics/{meta_id}` - Get stability metrics for a meta-analysis
- `POST /api/v1/metrics/calculate` - Calculate metrics for all meta-analyses

### Analysis
- `POST /api/v1/analysis/threshold` - Detect threshold for stability
- `GET /api/v1/analysis/plots` - Retrieve diagnostic plots
""",
            "contracts/requirements.md": """# Requirements: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Functional Requirements

### FR-001: Data Acquisition
- The system shall acquire at least 50 real-world meta-analyses
- Fallback to simulation if real data acquisition fails

### FR-002: Subsampling
- The system shall generate up to 100 bootstrap subsamples for each k
- Subsamples must be logged with seeds and estimator types

### FR-003: Model Selection
- Use DerSimonian-Laird (DL) estimator for k ≥ 10
- Use Restricted Maximum Likelihood (REML) estimator for k < 10

### FR-004: Stability Metrics
- Calculate SD of pooled effects across subsamples for each k
- Compute CI coverage rates for each k

### FR-005: Threshold Detection
- Fit GAM model to stability metrics
- Detect inflection point where derivative < 0.05

### FR-006: Visualization
- Generate stability curve plots with confidence bands
- Generate coverage plots by study count

### FR-007: Configuration
- All thresholds must be configurable via config.py
- Default nominal coverage target: 0.95
- Default stability threshold: 0.05

### FR-008: Error Handling
- Handle zero-variance studies gracefully
- Handle negative variance estimates
- Implement boundary clamping

### FR-009: Sensitivity Analysis
- Perturb reference value by its SE
- Quantify variation in coverage rates

### FR-010: Memory Safety
- Implement chunked data processing for large corpora
- Ensure memory usage stays within limits
""",
        }
    }

    # Create directories and files
    for dir_name in directories:
        dir_path = os.path.join(base_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

        # Create files for this directory
        if dir_name in files:
            for filename, content in files[dir_name].items():
                file_path = os.path.join(dir_path, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Created file: {file_path}")

    # Create top-level specs files
    top_level_files = {
        "README.md": """# Specs Directory

This directory contains the specification documents for the llmXive research projects.

## Structure

Each project has its own subdirectory with the following files:

- `plan.md`: High-level project plan and timeline
- `spec.md`: Detailed user stories and acceptance criteria
- `research.md`: Research notes and preliminary findings
- `data-model.md`: Data model and entity definitions
- `contracts/`: API contracts and requirements

## Usage

These documents serve as the source of truth for project requirements and guide
the implementation of tasks in the `tasks.md` file.
""",
        "project_index.json": json.dumps(
            {
                "projects": [
                    {
                        "id": "001-assessing-the-impact-of-sample-size-on-t",
                        "title": "Assessing the Impact of Sample Size on Meta-Analytic Reliability",
                        "status": "active",
                        "created": "2024-01-01",
                    }
                ],
                "last_updated": "2024-01-01",
            },
            indent=2,
        ),
    }

    for filename, content in top_level_files.items():
        file_path = os.path.join(base_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created file: {file_path}")