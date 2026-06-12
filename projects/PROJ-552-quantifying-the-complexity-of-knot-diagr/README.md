# PROJ-552: Quantifying the Complexity of Knot Diagrams

## Overview

This project quantifies the complexity of knot diagrams using crossing number and braid index as primary invariants. We analyze prime knots with crossing number ≤13, focusing on hyperbolic knots.

## Research Questions

1. What is the relationship between crossing number and braid index?
2. How well do these invariants predict hyperbolic volume?
3. What is the measurement precision across different knot classes?

## Methodology

- Download knot data from Knot Atlas (crossing number, braid index, hyperbolic volume)
- Establish measurement precision thresholds
- Fit regression models (linear, polynomial, logarithmic)
- Validate against KnotInfo and OEIS reference values

## Project Structure

See `docs/PROJECT_STRUCTURE.md` for detailed directory layout.

## Quick Start

1. Run `code/setup/create_structure.py` to create directories
2. Install dependencies from `pyproject.toml`
3. Execute download pipeline: `python -m code.download.knot_atlas_downloader`
4. Run analysis: `python -m code.analysis.regression`

## Reproducibility

All operations are logged with timestamps. Random seed is pinned at 42.
See `docs/reproducibility/` for detailed logs and validation reports.

## Reviewers

- Dan Rockmore (mathematical intuition, human readability)
- Marie Curie (standard of evidence, measurement precision)