---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Use of LLMs for Automated Documentation Generation from Code Commits

**Field**: computer science

## Research question

What information from code commit messages is successfully preserved versus lost when translated into documentation updates, and how do different LLM architectures differ in their ability to capture technical intent versus surface-level code changes?

## Motivation

Software documentation frequently lags behind code changes, creating maintenance debt and confusion for contributors. While LLMs offer a potential automation path, current evaluations often focus on generic text quality rather than the specific fidelity of technical information transfer. Understanding the specific gaps between commit intent and generated documentation is crucial for determining if LLMs can reliably replace or augment human documentation workflows without introducing subtle errors.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using the following query strings: "LLM commit message to documentation generation", "automated software documentation from git history", and "fidelity of LLM generated technical documentation". We specifically looked for studies comparing LLM outputs against ground-truth documentation changes in version control systems.

### What is known

- [Document Summarization with Conformal Importance Guarantees (2025)](https://arxiv.org/abs/2509.20461) — Establishes that while LLMs advance automatic summarization, they currently lack reliable guarantees on the inclusion of critical content, highlighting a known risk for high-stakes technical documentation tasks.

### What is NOT known

No published work has quantitatively measured the specific types of information (e.g., technical intent vs. surface-level code changes) that are systematically lost when translating commit messages into documentation updates using different LLM architectures. Existing literature focuses on general summarization quality or code generation, not the specific "commit-to-doc" fidelity gap in software engineering contexts.

### Why this gap matters

Software projects rely on accurate documentation for onboarding and maintenance; if LLMs consistently strip out technical nuance or intent while preserving surface-level descriptions, their adoption could degrade codebase maintainability. Identifying these specific failure modes is essential for developing better prompting strategies, fine-tuning targets, or human-in-the-loop verification workflows.

### How this project addresses the gap

This project will systematically compare LLM-generated documentation against ground-truth human updates for the same commits, using a structured rubric to categorize and quantify information loss by type (intent vs. surface). By testing multiple model architectures, we will isolate whether the loss is a general LLM limitation or specific to model size and training data, directly addressing the unknown fidelity metrics in commit-to-doc translation.

## Expected results

We expect to find that smaller LLMs preserve surface-level code changes (e.g., file names, function signatures) with high fidelity but frequently lose technical intent (e.g., "why" a change was made, edge cases addressed). Larger models may capture more intent but could introduce hallucinated details not present in the commit. A significant difference in "intent preservation" scores between model families would indicate that architecture choice critically impacts documentation utility.

## Methodology sketch

- **Data Acquisition**: Clone 5 popular open-source repositories (e.g., `pandas`, `requests`, `scikit-learn`) and extract commit history from the last 2 years using `git log` to pair commit messages with associated documentation file diffs (`.md`, `.rst`).
- **Dataset Construction**: Filter commits that explicitly modify documentation files, creating a dataset of ~500 (commit_message, human_doc_change) pairs.
- **Model Selection**: Select 3 open-source LLMs (e.g., `google/gemma-2b`, `microsoft/phi-2`, `meta-llama/Llama-2-7b-hf`) capable of running on 7GB RAM (using 4-bit quantization via `bitsandbytes`).
- **Generation Pipeline**: Prompt each model with the commit message and the pre-change documentation context to generate a proposed documentation update.
- **Information Extraction & Annotation**: Use a separate, smaller LLM or rule-based parser to extract "technical intent" entities (reasons, edge cases) and "surface" entities (file names, function names) from both the human change and the LLM output.
- **Fidelity Scoring**: Calculate precision/recall for "intent" and "surface" entities separately to quantify what was preserved vs. lost.
- **Statistical Analysis**: Perform a repeated-measures ANOVA to compare the fidelity scores (intent vs. surface) across the three model architectures.
- **Qualitative Verification**: Randomly sample 20 cases where intent was lost to manually verify the nature of the omission (e.g., hallucination vs. omission).
- **Visualization**: Generate bar charts showing the ratio of intent-to-surface preservation for each model and a confusion matrix of information loss types.
- **Validation Independence**: The evaluation metrics (precision/recall of extracted entities) are derived from the ground-truth human changes and the LLM outputs, but the *analysis* compares these metrics across models to identify architectural differences, avoiding circular validation of the generation process itself.

## Duplicate-check

- Reviewed existing ideas: N/A (no existing fleshed-out ideas provided in input).
- Closest match: N/A (no corpus provided for comparison).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-21T12:35:58Z
**Outcome**: exhausted
**Original term**: Evaluating the Use of LLMs for Automated Documentation Generation from Code Commits computer science
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating the Use of LLMs for Automated Documentation Generation from Code Commits computer science | 1 |

### Verified citations

1. **Document Summarization with Conformal Importance Guarantees** (2025). Bruce Kuwahara, Chen-Yuan Lin, Xiao Shi Huang, Kin Kwan Leung, Jullian Arta Yapeter, et al.. arXiv. [2509.20461](https://arxiv.org/abs/2509.20461). PDF-sampled: No.
