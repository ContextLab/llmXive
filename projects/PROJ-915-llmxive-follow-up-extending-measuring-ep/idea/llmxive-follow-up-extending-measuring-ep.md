---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Measuring Epistemic Resilience of LLMs Under Misleading Medical Contex"

**Field**: linguistics / AI Safety

## Research question

How does the presence of explicit logical contradictions between an authority-framed prompt and external medical knowledge influence the epistemic resilience of large language models, and what linguistic markers in the prompt determine whether the model prioritizes the authority framing or the contradictory evidence?

## Motivation

Prior work (MedMisBench) established that LLMs frequently abandon correct medical judgments when confronted with plausible but false authority framing, creating a critical safety gap in real-world deployment. While existing mitigations often rely on expensive fine-tuning or complex retrieval-augmented generation (RAG) pipelines, there is a lack of evidence regarding the specific linguistic conditions under which models fail to integrate contradictory external knowledge. Addressing this gap is essential for deploying safe, low-resource clinical triage tools in environments where compute is limited and for understanding the linguistic determinants of AI hallucination.

## Related work

- [LLM Robustness Against Misinformation in Biomedical Question Answering (2024)](https://arxiv.org/abs/2410.21330) — Demonstrates that retrieval-augmented generation (RAG) can reduce confabulation, providing a methodological precedent for using external context to improve LLM robustness, though this project investigates the specific linguistic failure modes of authority framing.
- [Combating Misinformation in the Age of LLMs: Opportunities and Challenges (2023)](https://arxiv.org/abs/2311.05656) — Discusses the broader landscape of misinformation threats and the potential of LLMs as both vectors and detectors, framing the specific challenge of "authority-framed" falsehoods addressed in this study.
- [Can LLM-Generated Misinformation Be Detected? (2023)](https://arxiv.org/abs/2309.13788) — Explores detection mechanisms for LLM-generated errors, offering a conceptual basis for analyzing how models process conflicting information sources.
- [Medical Misinformation in AI-Assisted Self-Diagnosis: Development of a Method (EvalPrompt) for Analyzing Large Language Models (2023)](https://arxiv.org/abs/2307.04910) — Demonstrates the development of evaluation methods for medical LMs, validating the necessity of rigorous benchmarking against misleading contexts similar to those used in MedMisBench.

## Expected results

We expect to identify specific linguistic markers (e.g., imperative mood, specific citation patterns, or modal verbs) that correlate strongly with a model's failure to prioritize contradictory medical evidence over authority framing. A successful outcome would be confirmed by a statistically significant correlation (p < 0.05) between the density of these markers and the model's adherence to the false authority, demonstrating that epistemic resilience is a function of prompt linguistics rather than just model architecture.

## Methodology sketch

- **Data Acquisition**: Download the MedMisBench dataset from the original repository; isolate the subset containing "Authority-framed" and "Exception-poisoning" attacks to ensure a controlled set of contradictory prompts.
- **Linguistic Feature Extraction**: Process the prompt texts using a standard NLP pipeline (e.g., spaCy) to extract linguistic features, including sentence structure, modal verb frequency, citation density, and imperative vs. declarative mood ratios.
- **Baseline Response Generation**: Run a quantized 3B parameter LLM (CPU-only, e.g., via `llama.cpp`) on the isolated subset to generate responses without intervention, recording the "Attack Success Rate" (ASR) as the ground truth for failure.
- **Contradiction Mapping**: Manually annotate or script-match the "correct" medical fact for each prompt item to establish the binary label of "contradiction present" vs. "contradiction accepted."
- **Statistical Modeling**: Perform a logistic regression analysis where the dependent variable is the model's adherence to the false authority (binary: 0/1) and the independent variables are the extracted linguistic features.
- **Independence Verification**: Ensure the evaluation target (model adherence to authority) is measured independently of the linguistic features used as predictors; the model's output is the observed phenomenon, while the features are the structural properties of the input, satisfying the independence requirement for validation.
- **Resource Constraint Check**: Ensure the entire pipeline (data processing, inference, and regression analysis) completes within the 6-hour GitHub Actions free-tier limit on 2 CPU cores and 7GB RAM.

## Duplicate-check

- Reviewed existing ideas: None found in the immediate corpus for this specific "linguistic marker" extension of MedMisBench.
- Closest match: None (closest prior work is the original MedMisBench paper itself, which this project extends by focusing on the linguistic determinants of failure).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-15T05:12:10Z
**Outcome**: exhausted
**Original term**: llmXive follow-up: extending "Measuring Epistemic Resilience of LLMs Under Misleading Medical Contex" linguistics
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "Measuring Epistemic Resilience of LLMs Under Misleading Medical Contex" linguistics | 4 |

### Verified citations

1. **Combating Misinformation in the Age of LLMs: Opportunities and Challenges** (2023). Canyu Chen, Kai Shu. arXiv. [2311.05656](https://arxiv.org/abs/2311.05656). PDF-sampled: No.
2. **Can LLM-Generated Misinformation Be Detected?** (2023). Canyu Chen, Kai Shu. arXiv. [2309.13788](https://arxiv.org/abs/2309.13788). PDF-sampled: No.
3. **LLM Robustness Against Misinformation in Biomedical Question Answering** (2024). Alexander Bondarenko, Adrian Viehweger. arXiv. [2410.21330](https://arxiv.org/abs/2410.21330). PDF-sampled: No.
4. **Medical Misinformation in AI-Assisted Self-Diagnosis: Development of a Method (EvalPrompt) for Analyzing Large Language Models** (2023). Troy Zada, Natalie Tam, Francois Barnard, Marlize Van Sittert, Venkat Bhat, et al.. arXiv. [2307.04910](https://arxiv.org/abs/2307.04910). PDF-sampled: No.
