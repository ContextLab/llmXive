# Configuration Module

This directory contains configuration files and utilities for project-wide settings.

## Purpose

Manage environment configuration including random seeds, memory limits, and other
project-wide parameters.

## Key Files

- `env.yaml`: Main configuration file with:
 - Fixed random seeds for numpy, sklearn, shap
 - Memory limit flags (max_ram_gb)
 - Other environment-specific settings

## Configuration Requirements

- All random seeds must be fixed for reproducibility (Constitution V)
- Memory limits must be documented (FR-007)
- Configuration changes must be tracked in state/artifact_hashes.yaml

## References

- Constitution V: Reproducibility through fixed seeds
- Constitution VII: Document configuration parameters
- FR-007: RAM limit enforcement
