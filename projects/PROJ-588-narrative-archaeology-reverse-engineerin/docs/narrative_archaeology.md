# Narrative Archaeology: Implementation Guide

## Overview
This document outlines the implementation of the "Early vs. Late Event Stability" analysis
as the primary strategy for Story Memory Reconstruction.

## Analysis Strategy
1. **Data Ingestion**: Download and preprocess ds000234.
2. **Segmentation**: Align story events to BOLD signal.
3. **RSA**: Compute dissimilarity matrices for Early and Late phases.
4. **Comparison**: Test if Early-Late dissimilarity is significantly higher than Early-Early.

## Adaptation Notes
- The original "Encoding vs. Recognition" comparison (FR-004) is implemented as "Early vs. Late Event Stability" per the fallback authorization in FR-003 and FR-004.
- Semantic features (BERT) are used only for RSA or as covariates, not as primary predictors for the decoder.