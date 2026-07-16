---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "SynthDocBench: Controlled Benchmark for Long-Context Visual Document U"

## Summary of the prior work
The paper introduces SynthDocBench, a fully synthetic benchmark that uses a combinatorial design to isolate specific failure modes in Vision Language Models (VLMs) during long-context document understanding, such as sharp performance degradation with document length and a systematic "middle-third" positional bias. By controlling variables like layout complexity and modality composition independently, the authors demonstrate that current frontier models often overfit to benchmark artifacts rather than achieving robust long-context reasoning, revealing that chart comprehension and cross-modal integration break down significantly in longer documents.

## Proposed extension
**Research Question:** Can we decouple the "middle-third" positional bias from attention mechanism limitations by introducing a "retrieval-as-a-tool" interface that forces models to explicitly query specific document regions before answering, and does this intervention disproportionately benefit models with smaller context windows?

This direction matters because the original paper identifies a severe positional bottleneck where models ignore the middle of long documents; if this is caused by attention dilution rather than a lack of visual understanding, a lightweight retrieval interface could serve as a CPU-tractable architectural patch that restores performance without requiring massive retraining or larger context windows.

## Methodology sketch
**Data:** We will extend the SynthDocBench generation pipeline to produce two versions of the same 200 documents: the original static PDF images and a parallel "retrieval-enabled" version where each document page is converted to a lightweight text-based index (OCR + layout metadata) stored in a CPU-accessible vector store or simple key-value dictionary.

**Procedure:** We will evaluate the same seven VLMs from the original study using a two-step prompting strategy on the retrieval-enabled set: (1) The model is prompted to generate a "search query" based on the question, (2) The system (running on CPU) executes a regex or keyword lookup against the pre-indexed document text to extract the relevant page snippets, and (3) The model answers using only the original image plus these retrieved snippets. We will specifically measure the accuracy delta on "middle-third" questions compared to the original static-image baseline.

**Expected Result:** We hypothesize that models with the steepest "middle-third" degradation in the original study will show the largest accuracy recovery (e.g., >15 percentage points) when provided with retrieved context, confirming that their failure is due to attention dilution rather than an inability to parse the visual content of the middle pages. Conversely, models that already perform well on static images should show minimal improvement, validating the diagnostic utility of this retrieval intervention.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **SynthDocBench: Controlled Benchmark for Long-Context Visual Document Understanding** — Abhigya Verma, Khyati Mahajan, Amit Kumar Saha, Shruthan Radhakrishna, Sagar Davasam, Vikas Yadav, Sai Rajeswar Mudumba. https://arxiv.org/abs/2607.10400.

```bibtex
@article{orig_arxiv_2607_10400,
  title = {SynthDocBench: Controlled Benchmark for Long-Context Visual Document Understanding},
  author = {Abhigya Verma and Khyati Mahajan and Amit Kumar Saha and Shruthan Radhakrishna and Sagar Davasam and Vikas Yadav and Sai Rajeswar Mudumba},
  year = {2026},
  eprint = {2607.10400},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.10400},
  url = {https://arxiv.org/abs/2607.10400}
}
```
