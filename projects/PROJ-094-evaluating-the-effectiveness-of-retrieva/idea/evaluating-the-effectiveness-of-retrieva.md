---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Effectiveness of Retrieval-Augmented Generation for Code Search

**Field**: computer science

## Research question

Can integrating retrieval-augmented generation (RAG) into code search pipelines significantly improve precision and recall compared to keyword-based baselines and direct LLM prompting under resource-constrained conditions?

## Motivation

Code search is critical for developer productivity, but traditional keyword search lacks semantic understanding while direct LLM prompting often hallucinates non-existent APIs. RAG offers a middle ground by grounding outputs in existing codebases, yet its efficacy for *search* specifically—rather than generation—remains under-evaluated in settings compatible with standard CI/CD environments.

## Related work

- [EVOR: Evolving Retrieval for Code Generation (2024)](http://arxiv.org/abs/2402.12317v2) — Proposes evolving retrieval strategies for code generation, highlighting the gap between static knowledge pipelines and dynamic code search needs.
- [DeepCodeSeek: Real-Time API Retrieval for Context-Aware Code Generation (2025)](http://arxiv.org/abs/2509.25716v1) — Introduces a technique to expand code and index for predicting APIs, directly addressing limitations in standard RAG query-document applications for code.
- [Reconstructing Context: Evaluating Advanced Chunking Strategies for Retrieval-Augmented Generation (2025)](http://arxiv.org/abs/2504.19754v1) — Investigates how chunking strategies affect RAG grounding, providing methodological guidance for indexing code snippets.
- [LLM-as-a-Judge: Rapid Evaluation of Legal Document Recommendation for Retrieval-Augmented Generation (2025)](http://arxiv.org/abs/2509.12382v1) — Demonstrates using LLMs as evaluators for recommendation quality, suggesting a metric framework for assessing code search relevance beyond exact matches.

## Expected results

We expect RAG-enhanced search to outperform keyword baselines in semantic relevance (measured by nDCG) and reduce hallucination rates compared to direct prompting. Evidence will be confirmed if retrieval precision exceeds 0.7 on standard code search benchmarks and statistical tests show significant improvement over baselines (p < 0.05).

## Methodology sketch

- Download the CodeSearchNet dataset (GitHub subset) from HuggingFace Datasets to ensure reproducibility without new collection.
- Preprocess code snippets by filtering for common languages (Python, Java) and limiting context length to fit 7GB RAM.
- Index the code corpus using `sentence-transformers/all-MiniLM-L6-v2` embeddings stored in a CPU-compatible FAISS index.
- Construct a query set of 200 natural language code search prompts derived from existing documentation issues.
- Retrieve top-k candidates (k=10) for each query using cosine similarity and generate summaries via a small open-source model (e.g., CodeGen-mono-350M).
- Evaluate precision@k, recall@k, and nDCG against ground-truth labels using scikit-learn metrics.
- Apply a paired t-test to compare RAG performance against a keyword baseline (BM25) and a direct LLM baseline.
- Log runtime and memory usage to verify compliance with GitHub Actions free-tier constraints.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: None identified.
- Verdict: NOT a duplicate
