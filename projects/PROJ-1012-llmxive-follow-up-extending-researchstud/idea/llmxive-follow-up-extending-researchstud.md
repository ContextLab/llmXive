---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "ResearchStudio-Reel: Automate the Last Mile of Research from Paper to "

## Summary of the prior work
ResearchStudio-Reel automates the "last mile" of research dissemination by composing five agent skills to convert a single paper PDF into three editable artifacts: a conference poster, a narrated talk video, and a bilingual blog post. Its core innovations include a shared upstream extractor (Paper2Assets) to ensure factual consistency across artifacts, deterministic primitives wrapped in "measured-fill loops" with hard pass/fail render gates, and a unified interactive HTML viewer (Paper2Reel) that synchronizes navigation across all three formats. The system uniquely produces native, editable files (PowerPoint and Word) rather than static renders, outperforming prior isolated systems on aesthetic and information consistency benchmarks.

## Proposed extension
**Research Question:** Can a lightweight, rule-based "layout-aware fact-checker" running entirely on CPU reduce hallucinated citations and figure misattribution in the generated artifacts by 40% compared to the current LLM-based "measured-fill" loop, without increasing generation latency? This matters because while ResearchStudio-Reel solves the *format* consistency problem, it still relies on VLMs for semantic verification, which is computationally expensive and prone to subtle factual drift in dense scientific texts; a CPU-tractable alternative would enable real-time, scalable deployment in resource-constrained environments like local lab servers or browser-based tools.

## Methodology sketch
**Data:** We will use the 500-paper test set from the original Paper2Poster benchmark, augmented with a manually verified "Gold Truth" JSON file containing exact figure IDs, citation strings, and claim-to-evidence spans for each paper.
**Procedure:** 
1. Implement a deterministic "Layout-Aware Fact-Checker" (LAFC) module that uses regex and simple graph traversal on the extracted `Paper2Assets` bundle to cross-reference generated content against the Gold Truth (e.g., verifying that "Figure 3" in the blog text actually maps to the figure object labeled "Figure 3" in the asset bundle).
2. Replace the VLM-based verification step in the original "measured-fill loop" with this LAFC module for the extension condition, while keeping the original LLM-based loop as the baseline.
3. Run both pipelines on a standard CPU-only server (e.g., 8-core Intel Xeon) to measure latency and token costs.
4. Evaluate the output artifacts using a new "Factual Precision" metric (percentage of correct figure/citation references) and a "Drift Score" (semantic distance between original claims and generated summaries).
**Expected Result:** The LAFC extension will achieve a ≥40% reduction in hallucinated references (specifically figure misattribution and citation errors) compared to the baseline, while reducing average generation time by 60% and eliminating GPU dependency, with no statistically significant drop in overall readability scores.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **ResearchStudio-Reel: Automate the Last Mile of Research from Paper to Poster, Video, and Blog** — Lingao Xiao, Yalun Dai, Yangyu Huang, Qihao Zhao, Wenshan Wu, Hugo He, Ruishuo Chen, Jin Jiang, Qianli Ma, Jiahuan Zhang, Xin Zhang, Ying Xin, Yang Ou, Yan Xia, Scarlett Li, Longbo Huang, Zhipeng Zhang, Yang He, Yap Kim Hui, Yan Lu. https://arxiv.org/abs/2607.04438.

```bibtex
@article{orig_arxiv_2607_04438,
  title = {ResearchStudio-Reel: Automate the Last Mile of Research from Paper to Poster, Video, and Blog},
  author = {Lingao Xiao and Yalun Dai and Yangyu Huang and Qihao Zhao and Wenshan Wu and Hugo He and Ruishuo Chen and Jin Jiang and Qianli Ma and Jiahuan Zhang and Xin Zhang and Ying Xin and Yang Ou and Yan Xia and Scarlett Li and Longbo Huang and Zhipeng Zhang and Yang He and Yap Kim Hui and Yan Lu},
  year = {2026},
  eprint = {2607.04438},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.04438},
  url = {https://arxiv.org/abs/2607.04438}
}
```
