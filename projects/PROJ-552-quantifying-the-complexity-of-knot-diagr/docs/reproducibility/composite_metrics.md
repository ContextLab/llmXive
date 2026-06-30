# Composite Metrics Overview

This document consolidates the definitions, implementations, and results for all composite metrics used in the knot complexity analysis project.

## 1. Introduction

Composite metrics combine multiple knot invariants or structural properties to provide a more nuanced measure of knot complexity. This section aggregates the various composite approaches explored in the project.

## 2. Standard Composite Metrics

The standard composite metrics are implemented in `code/analysis/composite_metric.py`.

### 2.1 Definition

The primary composite metric integrates crossing number, braid index, and hyperbolic volume (where available) into a normalized score.

### 2.2 Implementation Details

Refer to `code/analysis/composite_metric.py` for the core calculation logic, including handling of missing invariants and normalization factors.

## 3. Extended Composite Metrics

Extended variations are implemented in `code/analysis/composite_metric_extended.py`.

### 3.1 Purpose

These metrics incorporate additional invariants such as signature, determinant, and Jones polynomial coefficients to refine complexity estimation for specific knot families.

### 3.2 Usage

The extended metrics are particularly useful for distinguishing between knots that share similar crossing numbers but differ in topological complexity.

## 4. Linear Composite Metrics

Linear combinations are defined in `code/analysis/composite_metric_linear.py`.

### 4.1 Approach

This module implements weighted linear sums of invariants, optimized for interpretability and direct correlation with crossing number.

## 5. Entropy-Based Composite Metrics

Entropy-based measures are handled in `code/analysis/composite_metric_entropy.py`.

### 5.1 Concept

These metrics utilize the Shannon entropy of invariant distributions to quantify the unpredictability or information content of a knot's structural profile.

## 6. Seifert Surface-Based Metrics

Metrics derived from Seifert surface properties are located in `code/analysis/composite_metric_seifert.py`.

### 6.1 Derivation

These metrics leverage the genus and Euler characteristic of minimal Seifert surfaces to assess complexity.

## 7. Novel Composite Metrics

Experimental and novel composite metrics are implemented in `code/analysis/composite_metric_novel.py`.

### 7.1 Innovation

This module contains non-standard combinations and heuristic approaches proposed to capture complex topological features not well-represented by traditional linear models.

## 8. Results and Validation

Results from applying these metrics are documented in the associated reproduction logs and JSON outputs. Key findings include:

- Strong correlation between extended composite metrics and hyperbolic volume.
- Entropy-based metrics provide distinct clustering for alternating vs. non-alternating knots.
- Novel metrics show promise in identifying specific knot families but require further validation.

## 9. Future Work

Future iterations may integrate machine learning models to dynamically weight the components of composite metrics based on knot family characteristics.
