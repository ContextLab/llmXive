# Spec: OPD Generalization Gap in Unified Diffusion

## Problem Statement
Does RL-Unified fine-tuning on diffusion models create a generalization gap where OOD performance degrades significantly more than ID performance?

## User Stories
- US1: Data Acquisition and Prompt Curation
- US2: CPU-Only Inference Execution
- US3: Statistical Analysis of Generalization Gap

## Functional Requirements
- FR-001: Fetch Qwen-Image-2.0 and Qwen-Image-2.0-RL weights.
- FR-002: Curate leakage-free ID and OOD prompt sets.
- FR-003: Generate images on CPU-only environment.
- FR-004: Score images using VLM reward models.
- FR-005: Compute Generalization Gap (OOD degradation - ID degradation).
- FR-006: Perform Paired T-Test with HC3 Robust Errors.
- FR-007: Bootstrap Resampling for CI stability.
- FR-008: External Consistency Check with Human Proxy (Image-Reward).
