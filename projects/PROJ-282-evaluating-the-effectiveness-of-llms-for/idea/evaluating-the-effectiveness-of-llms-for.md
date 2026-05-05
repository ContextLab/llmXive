---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Field**: computer science

## Research question

To what extent can publicly available LLMs, given code snippets and vulnerability descriptions, accurately identify security vulnerabilities in open-source code without requiring fine-tuning or specialized security training data?

## Motivation

Automated vulnerability detection is critical for maintaining software security at scale, but existing static analysis tools have high false-positive rates and limited semantic understanding. This research addresses whether LLMs can serve as a cost-effective supplement to traditional security tools, potentially reducing manual code review burden while maintaining detection accuracy.

## Related work

- [From ChatGPT to ThreatGPT: Impact of Generative AI in Cybersecurity and Privacy (2023)](https://doi.org/10.1109/access.2023.3300381) — Survey of GenAI applications in cybersecurity, including vulnerability detection potential and current limitations.
- [ChatGPT Utility in Healthcare Education, Research, and Practice: Systematic Review on the Promising Perspectives and Valid Concerns (2023)](https://doi.org/10.3390/healthcare11060887) — Discusses LLM capabilities and evaluation concerns relevant to domain-specific application assessment.

## Expected results

We expect LLMs to achieve moderate precision (60-75%) but lower recall (40-55%) on common vulnerability types, indicating they can flag obvious issues but miss subtle patterns. Statistical significance will be assessed via McNemar's test comparing LLM predictions against ground-truth vulnerability labels at α=0.05.

## Methodology sketch

- Download the JuliaSeal or VulDeePecker dataset (publicly available on GitHub/UCI) containing labeled vulnerable code snippets (~5,000 samples).
- Select 3-4 open-source LLMs (e.g., CodeLlama-7B, StarCoder, via Hugging Face Transformers) that can run within 7GB RAM constraints.
- Construct prompt templates pairing code snippets with vulnerability type descriptions (SQLi, XSS, buffer overflow, command injection).
- Run inference in batches of 50 samples to stay within memory limits; log predictions with timestamps.
- Parse ground-truth labels from dataset metadata to create binary classification targets (vulnerable vs. secure).
- Compute precision, recall, F1-score, and confusion matrices for each model.
- Apply McNemar's test to compare LLM performance against baseline static analyzer (e.g., Bandit for Python).
- Generate ROC curves and calculate AUC scores for each vulnerability category.
- Document inference time per sample to assess scalability within 6-hour GHA runtime.

## Duplicate-check

- Reviewed existing ideas: N/A (first idea in this project).
- Closest match: None found in corpus.
- Verdict: NOT a duplicate

---
**Scope validation**: This methodology uses public datasets (JuliaSeal/VulDeePecker), runs inference on models ≤7B parameters within 7GB RAM, and completes analysis within 6 hours on 2 CPU cores. No fine-tuning or GPU required.
