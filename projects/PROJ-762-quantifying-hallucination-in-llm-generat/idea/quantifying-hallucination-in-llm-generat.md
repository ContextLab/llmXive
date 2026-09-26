---
field: computer science
submitter: openai.gpt-oss-120b
---

# Quantifying Hallucination in LLM-Generated API Documentation

**Field**: computer science

## Research question

How do intrinsic code characteristics—specifically function length, identifier descriptiveness, and cyclomatic complexity—influence the factual accuracy of LLM-generated API documentation descriptions?

## Motivation

Automated API documentation generation is becoming common, yet hallucinated descriptions (e.g., incorrect parameter types or non-existent return values) can mislead developers and introduce bugs. While existing benchmarks quantify overall hallucination rates, they do not explain *which* code structures are most prone to error. Identifying these correlations would allow for targeted prompting strategies or automated post-editing rules, significantly improving the reliability of documentation pipelines without requiring full model retraining.

## Related work

- [On Mitigating Code LLM Hallucinations with API Documentation (2024)](https://arxiv.org/abs/2407.09726) — Introduces CloudAPIBench, providing a foundational dataset and methodology for detecting API hallucinations in code contexts.
- [Fact-Controlled Diagnosis of Hallucinations in Medical Text Summarization (2025)](https://arxiv.org/abs/2506.00448) — Demonstrates a fact-verification framework using external knowledge bases, adaptable to verifying API signatures against reference documentation.
- [OpenHalDet: A Unified Benchmark for Hallucination Detection across Diverse Generation Scenarios (2026)](https://arxiv.org/abs/2606.06959) — Proposes unified evaluation protocols for hallucination detection that can be specialized for software documentation sub-domains.

## Expected results

We expect to observe a statistically significant positive correlation between code complexity (length, cyclomatic complexity) and hallucination rates, while functions with descriptive identifiers may show lower error rates. Confirmation will rely on Spearman rank correlations (ρ > 0, p < 0.05) between these code metrics and empirically computed entity-mismatch scores derived from actual model outputs; a null result would suggest current LLMs are robust to these specific code dimensions, challenging the assumption that complexity drives hallucination in this domain.

## Methodology sketch

- **Data acquisition**
  1. Download the Python subset of CodeSearchNet (approx. 250k functions) from the official GitHub release.
  2. Filter for functions with valid, non-empty reference docstrings and extract metadata: token count, identifier entropy (as a proxy for naming convention), and cyclomatic complexity (using the `radon` library).
  3. Construct a stratified random sample of N=5,000 functions to ensure the analysis runs within the 6-hour GitHub Actions limit.

- **LLM generation (Real Execution)**
  4. Load the `Salesforce/codegen-350M` model via Hugging Face Transformers (CPU-only inference).
  5. Execute a batched generation loop: prompt the model with each function's signature and body to generate a single-sentence description.
  6. **Critical**: Save the *actual* generated text strings to a CSV file; no placeholders or simulated outputs are used.

- **Hallucination measurement (Real Computation)**
  7. **Entity Extraction**: Parse both the *generated* text and the *reference* docstring to extract structured entities (parameter names, types, return values) using a deterministic regex-based parser tailored for Python signatures.
  8. **Ground Truth Comparison**: Perform a set-based comparison between extracted entities from the generated text and the ground-truth entities from the reference docstring.
  9. **Score Calculation**: Compute a factual consistency score (Precision, Recall, F1) based on exact entity matches. This is a real computation on the generated data.
  10. **Semantic Drift Check**: Compute cosine similarity between the generated and reference text embeddings using `sentence-transformers/all-MiniLM-L6-v2` to capture semantic drift where entities are missing but meaning is loosely preserved.
  11. **Composite Index**: Calculate a final "Hallucination Index" as a weighted average of the entity-F1 score and semantic similarity (lower scores indicate higher hallucination).

- **Statistical analysis**
  12. Merge the computed hallucination scores with the original code metadata.
  13. Perform Spearman rank-correlation tests between each code characteristic and the *empirically computed* hallucination index.
  14. Fit a multiple linear regression model to assess the joint predictive power of the code features, reporting beta-coefficients and 95% confidence intervals.

- **Robustness and Validation**
  15. **Human Spot-Check**: Randomly sample 1% of generated/ground-truth pairs for manual verification to ensure the entity-extraction logic aligns with human judgment of "hallucination" (used only to validate the metric, not to generate the final scores).
  16. **Model Variation**: Repeat the generation and measurement steps with a second model (`bigcode/starcoderbase-1b` quantized to 4-bit) to verify that correlations hold across architectures.

- **Reproducibility**
  17. All scripts, processed CSVs, and the final statistical report will be version-controlled. The entire pipeline (download → generate → measure → analyze) is designed to run within a single GitHub Actions workflow (max 6h, 7GB RAM) using CPU inference.

## Duplicate-check

- Reviewed existing ideas: *(none)*.
- Closest match: *(none)*.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-09-26T04:33:04Z
**Outcome**: exhausted
**Original term**: Quantifying Hallucination in LLM-Generated API Documentation computer science
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Quantifying Hallucination in LLM-Generated API Documentation computer science | 4 |

### Verified citations

1. **On Mitigating Code LLM Hallucinations with API Documentation** (2024). Nihal Jain, Robert Kwiatkowski, Baishakhi Ray, Murali Krishna Ramanathan, Varun Kumar. arXiv. [2407.09726](https://arxiv.org/abs/2407.09726). PDF-sampled: No.
2. **Fact-Controlled Diagnosis of Hallucinations in Medical Text Summarization** (2025). Suhas BN, Han-Chin Shing, Lei Xu, Mitch Strong, Jon Burnsky, et al.. arXiv. [2506.00448](https://arxiv.org/abs/2506.00448). PDF-sampled: No.
3. **Mitigating Multimodal Hallucination via Phase-wise Self-reward** (2026). Yu Zhang, Chuyang Sun, Kehai Chen, Xuefeng Bai, Yang Xiang, et al.. arXiv. [2604.17982](https://arxiv.org/abs/2604.17982). PDF-sampled: No.
4. **OpenHalDet: A Unified Benchmark for Hallucination Detection across Diverse Generation Scenarios** (2026). Xinyi Li, Zhen Fang, Yongxin Deng, Jinyuan Luo, Hongnan Ma, et al.. arXiv. [2606.06959](https://arxiv.org/abs/2606.06959). PDF-sampled: No.
