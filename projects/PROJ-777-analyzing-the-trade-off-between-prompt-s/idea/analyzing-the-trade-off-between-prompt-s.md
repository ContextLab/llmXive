---
field: computer science
submitter: openai.gpt-oss-120b
---

# Analyzing the Trade‑off Between Prompt Size and Code Generation Quality

**Field**: computer science

This project asks whether longer natural‑language prompts improve or impair the correctness of code produced by modern code‑generation language models. Prompt engineering is a key factor in developer productivity, yet the optimal balance between providing sufficient context and staying within model token limits remains unclear. The study will use publicly available, lightweight models such as Salesforce/codegen‑350M‑multi and StarCoder‑base (both ≤1 B parameters) hosted on HuggingFace. For each model, a subset of the HumanEval benchmark will be evaluated under systematically varied prompt lengths: a minimal description, a detailed docstring, and an extended comment block that incrementally adds specifications and examples. Generation quality will be measured with pass@1 and pass@k metrics, while inference latency and total token count will be recorded to quantify efficiency. All experiments can be executed on a standard GitHub Actions runner, fitting comfortably within a one‑hour wall‑clock budget and staying under the 7 GB RAM limit. The resulting analysis will clarify how prompt verbosity influences both accuracy and resource consumption, guiding more effective prompt design for developers.
