---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Generation on Software Security: A Static Analysis Study

**Field**: computer science

## Research question

How do security vulnerability patterns in LLM-generated code compare to those in human-written code across common software functionalities?

## Motivation

LLMs are increasingly used to generate production code, but it is unclear whether the security characteristics of this code differ systematically from human-authored code. Understanding this relationship is critical for software security practices, as current static analysis tools were trained and tuned on human-written code patterns. If LLM-generated code exhibits distinct vulnerability profiles, this would necessitate new analysis approaches and impact how organizations integrate AI code generation into secure development pipelines.

## Literature gap analysis

### What we searched

Literature searches were attempted using queries related to "LLM code generation security vulnerabilities," "static analysis AI-generated code," and "machine learning software vulnerability detection" across Semantic Scholar and arXiv. The provided literature block contained only one paper on quantum materials simulation (Quantum ESPRESSO), which is unrelated to software security or code generation.

### What is known

*None of the provided literature results are defensibly on-topic for this research question.*

### What is NOT known

No published work has systematically compared the security vulnerability patterns between LLM-generated and human-written code using standardized static analysis tooling. There is no established baseline for whether LLM-generated code exhibits higher, lower, or qualitatively different vulnerability distributions than human-authored code across common software functionalities.

### Why this gap matters

Software development teams adopting LLM code generation tools need evidence-based guidance on whether their existing security review processes remain effective. Filling this gap would enable organizations to make informed decisions about integrating AI code generation into secure development workflows and identify whether new static analysis approaches are needed.

### How this project addresses the gap

This project will generate code samples using public LLM APIs for standardized prompts across common software functionalities, then apply multiple open-source static analysis tools to both the generated code and comparable human-written code from public repositories. The vulnerability detection rates and patterns will be compared statistically to determine whether LLM-generated code exhibits distinct security characteristics.

## Expected results

We expect to observe measurable differences in vulnerability patterns between LLM-generated and human-written code, with LLM-generated code potentially showing higher rates of injection flaws and authentication bypass vulnerabilities due to training data biases. The level of evidence needed is statistical significance (p<0.05) across multiple code samples and tool configurations to establish whether these differences are systematic rather than random variation.

## Methodology sketch

- Download public dataset of human-written code with known vulnerabilities (e.g., Devign dataset from GitHub or CodeXGLUE benchmarks)
- Generate equivalent code samples using public LLM APIs (e.g., HuggingFace open models) for standardized prompts matching the human code functionality
- Run open-source static analysis tools (Semgrep, SonarQube community edition) on both code sets using Docker containers compatible with GHA runner specifications
- Extract vulnerability findings from tool output in structured format (JSON)
- Calculate precision and recall metrics by comparing tool findings against known vulnerability labels
- Perform statistical comparison of vulnerability rates between LLM-generated and human-written code using chi-square or Fisher's exact test
- Visualize vulnerability type distributions across both code sources using bar charts
- Document all tool configurations and versions for reproducibility

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None identified.
- Verdict: NOT a duplicate

---

**Scope note**: This methodology is designed for GitHub Actions free-tier runners (2 CPU, 7GB RAM, 14GB SSD, 6h max). All datasets are publicly available, and static analysis tools run within memory constraints when processing code samples in batches. No GPU or specialized hardware is required.
