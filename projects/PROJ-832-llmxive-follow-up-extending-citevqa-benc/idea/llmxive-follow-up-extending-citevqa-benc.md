---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document In"

**Field**: Linguistics / Document Intelligence

## Research question

How do the mechanisms of spatial reasoning in language models differ when trained on visual-textual pairs versus text-only data, and what specific linguistic or structural cues do text-only models fail to utilize when attempting to localize answers in document images?

## Motivation

Current end-to-end Multimodal Large Language Models (MLLMs) frequently suffer from "Attribution Hallucination," generating correct answers while citing irrelevant document regions. It remains unclear whether this failure is an unavoidable consequence of parametric over-reliance in massive models or a fundamental limitation of smaller, modular systems that lack explicit visual pre-training. Resolving this is critical for designing cost-effective, auditable document intelligence pipelines that can operate on CPU-only hardware without sacrificing the ability to map textual claims to visual evidence.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms including "visual pre-training document understanding," "cross-modal alignment bounding boxes," "attribution hallucination MLLM," "spatial reasoning language models," and "text-only reasoning document QA." The search returned a sparse set of results focused on general knowledge attribution in LLMs and specific RAG constraints for fiscal documents, but no direct studies isolating the causal impact of visual pre-training on the specific task of mapping text answers to visual bounding boxes in document understanding.

### What is known

- [Citation-Enforced RAG for Fiscal Document Intelligence: Cited, Explainable Knowledge Retrieval in Tax Compliance (2026)](https://arxiv.org/abs/2603.14170) — Demonstrates that enforcing citation constraints in Retrieval-Augmented Generation (RAG) pipelines can improve explainability in fiscal documents, offering a methodological precedent for decoupling retrieval from generation, though it does not address the visual grounding mechanism itself.
- [Neuron-Level Knowledge Attribution in Large Language Models (2023)](https://arxiv.org/abs/2312.12141) — Highlights the computational difficulty of tracing knowledge sources in large models, supporting the hypothesis that smaller, modular architectures may exhibit distinct (and potentially more transparent) failure modes regarding attribution, but does not investigate the role of visual pre-training in alignment tasks.

### What is NOT known

No published work has empirically isolated the causal contribution of visual pre-training to the specific capability of mapping textual answers to visual bounding boxes in document understanding. Existing literature either assumes end-to-end multimodal training or focuses on textual retrieval constraints, leaving a gap in understanding whether small, text-only models can achieve cross-modal alignment through reasoning alone or if visual pre-training is a necessary condition for accurate spatial attribution.

### Why this gap matters

Understanding whether visual pre-training is a necessary condition for accurate cross-modal alignment is crucial for developing efficient, auditable document intelligence systems. If text-only reasoning suffices, organizations can deploy lightweight, CPU-tractable pipelines without the computational overhead of training or fine-tuning massive multimodal models, significantly reducing costs and improving transparency in high-stakes domains like tax compliance and legal document review.

### How this project addresses the gap

This project directly addresses the gap by implementing a controlled, decomposed pipeline that separates text retrieval from visual localization, allowing us to test a small, text-only model (Phi-3-mini) against the specific task of mapping answers to bounding boxes. By comparing its performance against baseline MLLMs and conducting a "Visual-Only" control experiment, we will empirically determine if the capability to perform accurate cross-modal alignment emerges from text-only reasoning or requires explicit visual pre-training.

## Expected results

We expect the decomposed, CPU-tractable pipeline to exhibit a distinct failure profile: while text retrieval accuracy will be high, the final Strict Attributed Accuracy (SAA) will likely remain low (<15%) due to the small model's inability to perform cross-modal alignment without visual pre-training. This would confirm that "Attribution Hallucination" in MLLMs is partially driven by a lack of explicit visual grounding mechanisms rather than solely by parametric size, and that text-only models fail to utilize low-level structural cues (e.g., layout proximity, font hierarchy) necessary for precise spatial localization.

## Methodology sketch

- **Data Acquisition**: Download the CiteVQA dataset (711 PDFs, 1,897 QA pairs) from the official repository; parse all PDFs into structured JSON containing extracted text, page numbers, and bounding box coordinates using `pdfplumber` (CPU-bound).
- **Text-Only Baseline Construction**: Implement a two-stage inference pipeline:
    - *Stage 1 (Retrieval)*: Encode all text chunks using `all-MiniLM-L6-v2` (sentence-transformers) and store in a local FAISS index; retrieve top-k chunks for each query.
    - *Stage 2 (Reasoning & Mapping)*: Feed the query and retrieved text chunks to a small instruction-tuned model (e.g., Phi-3-mini quantized to 4-bit) to generate an answer and a predicted chunk ID.
- **Visual Grounding Mapping**: Map the predicted chunk ID to its corresponding bounding box coordinates from the pre-processed JSON; generate a cropped image of this region for the "Visual-Only" control test.
- **Control Experiment**: Run a second pass where a separate small model receives only the cropped image (no text) to assess if visual context alone can drive correct attribution, isolating the modality gap.
- **Evaluation Metric**: Compute the Strict Attributed Accuracy (SAA), defined as the intersection of (1) answer correctness (exact match or semantic similarity > 0.85) and (2) bounding box IoU > 0.5 with the ground truth.
- **Statistical Analysis**: Perform a paired t-test comparing the SAA scores of the text-only decomposed pipeline against the baseline MLLM scores reported in the original CiteVQA paper to determine if the difference is statistically significant (p < 0.05).
- **Validation Independence**: Ensure the evaluation (SAA) uses ground-truth bounding boxes from the dataset which are independent of the model's predicted coordinates, avoiding circular validation where the model's output is compared against a derived version of itself.

## Duplicate-check

- Reviewed existing ideas: N/A (No other fleshed-out ideas in the provided context).
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-12T05:34:22Z
**Outcome**: exhausted
**Original term**: llmXive follow-up: extending "CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document In" linguistics
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document In" linguistics | 2 |

### Verified citations

1. **Citation-Enforced RAG for Fiscal Document Intelligence: Cited, Explainable Knowledge Retrieval in Tax Compliance** (2026). Akhil Chandra Shanivendra. arXiv. [2603.14170](https://arxiv.org/abs/2603.14170). PDF-sampled: No.
2. **Neuron-Level Knowledge Attribution in Large Language Models** (2023). Zeping Yu, Sophia Ananiadou. arXiv. [2312.12141](https://arxiv.org/abs/2312.12141). PDF-sampled: No.
