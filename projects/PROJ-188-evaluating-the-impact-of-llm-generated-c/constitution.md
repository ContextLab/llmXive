# Constitution of the llmXive Automated Science Pipeline

## Version 2.0.0

### Preamble
This document establishes the immutable principles governing the generation,
validation, and analysis of code explanations within the llmXive pipeline.
All automated agents and human operators must adhere to these principles.

---

## Principle I: Reproducibility
Every experiment must be fully reproducible. All code, data, and configuration
must be version-controlled and accessible. Random seeds must be fixed.

## Principle II: Data Integrity
No synthetic data shall be used to replace missing real-world observations.
If data is unavailable, the experiment must fail explicitly rather than
fabricate results.

## Principle III: Transparency
All model parameters, hyperparameters, and preprocessing steps must be
documented and traceable to the final output.

## Principle IV: Ethical Use
Generated content must not contain harmful, biased, or proprietary information
unless explicitly authorized and sanitized.

## Principle V: Validation First
Any claim of improvement must be supported by statistically significant
evidence derived from a controlled study design.

## Principle VI: Open Source
All pipeline components, excluding proprietary datasets or API keys, must be
open source and available for community review.

## Principle VII: Model Authorization
All LLM-generated explanations MUST be produced using CodeLlama-7B (or TinyLlama fallback) via the HuggingFace `transformers` library with a fixed token limit of 200 and pinned random seeds.

---
*Last Updated: 2024-01-15*
*Amendment Reference: T000a, T000b*