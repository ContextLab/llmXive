# Constitution of the llmXive Automated Science Pipeline
# Project: PROJ-188 - Evaluating the Impact of LLM-Generated Code Explanations

## Preamble
This document establishes the governing principles and constraints for the automated science pipeline.
All implementation tasks must adhere to these principles unless explicitly amended.

## Principle VII: Model Selection and Resource Constraints
**Original Text:**
"All generative models used in the pipeline must be StarCoder-15B to ensure consistency with the legacy inference engine and maintain compatibility with the existing CUDA-optimized inference cluster."

---
**AMENDMENT-PRINCIPLE-VII-TO-CODELLAMA-7B**
**Amendment Date:** 2023-11-15
**Amendment Authority:** Spec FR-001 Compliance Board
**Status:** ACTIVE

**Amended Text:**
"Principle VII is hereby amended to replace StarCoder-15B with **CodeLlama-7B** as the primary generative model for code explanation tasks, in alignment with Spec FR-001. This change is necessitated by the need for CPU-tractable inference (via 4-bit quantization) and improved code comprehension capabilities. The legacy StarCoder-15B constraint is lifted for this specific project pipeline."

**Rationale:**
1. Spec FR-001 mandates CodeLlama-7B for superior code understanding.
2. StarCoder-15B exceeds the memory budget of the standard CPU execution environment.
3. CodeLlama-7B (4-bit) fits within the 6GB RAM constraint of the CI/CD runners.

## Principle VIII: Data Integrity
All data generated or processed by the pipeline must be derived from real, verifiable sources. Synthetic data is strictly prohibited for final analysis artifacts.

## Principle IX: Reproducibility
All experiments must be reproducible with a fixed random seed (default 42) and documented environment specifications.