---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Generation Models on Developer Productivity  

**Field**: computer science  

## Research question  

How does the use of large‑language‑model (LLM) code‑generation tools affect (i) developers’ task‑completion time and (ii) the quality of the produced code compared with unaided coding?  

## Motivation  

LLM‑based code generators (e.g., Codex, Code Llama) are being integrated into IDEs and claim to accelerate software development, yet systematic evidence of their actual productivity impact is scarce. Quantifying both speed gains and potential quality trade‑offs will inform tool designers, educators, and industry practitioners about when and how to adopt such assistants.  

## Related work  

- [Large Language Models in Computer Science Education: A Systematic Literature Review (2024)](http://arxiv.org/abs/2410.16349v1) — surveys the adoption of LLMs in CS learning environments and highlights a lack of rigorous empirical productivity studies.  
- [Execution-based Evaluation for Data Science Code Generation Models (2022)](http://arxiv.org/abs/2211.09374v1) — proposes execution‑based metrics (test pass rate, runtime) for code‑generation models, providing a useful evaluation framework for our quality measurements.  
- [Opinion Paper: “So what if ChatGPT wrote it?” Multidisciplinary perspectives on opportunities, challenges and implications of generative conversational AI for research, practice and policy (2023)](https://doi.org/10.1016/j.ijinfomgt.2023.102642) — discusses broader implications of generative AI on work practices, underscoring the need for empirical productivity assessments.  
- [JaCoText: A Pretrained Model for Java Code-Text Generation (2023)](http://arxiv.org/abs/2303.12869v1) — introduces a high‑performing Java code‑generation model that can serve as the LLM assistant in our experiments.  
- [Clinical Productivity System - A Decision Support Model (2012)](http://arxiv.org/abs/1206.0021v1) — presents a decision‑support framework for measuring productivity, offering methodological inspiration for designing our time‑tracking protocol.  

## Expected results  

We anticipate that LLM assistance will **reduce average task‑completion time by 15‑30 %** while maintaining or modestly improving code quality (higher test‑pass rates, comparable cyclomatic complexity). A statistically significant time reduction (p < 0.05) together with non‑degraded quality metrics would support the hypothesis that LLMs boost productivity without sacrificing correctness. Conversely, any increase in static‑analysis warnings or bugs would reveal quality trade‑offs.  

## Methodology sketch  

1. **Dataset acquisition** – Download the HumanEval benchmark (GitHub https://github.com/openai/human-eval) and a curated set of 100 medium‑difficulty Codeforces problems via the public API (https://codeforces.com/api).  
2. **LLM assistant selection** – Use the open‑source JaCoText model (Java) and StarCoder (Python) via HuggingFace Transformers; host them locally on the GitHub Actions runner (model size ≤ 1 GB).  
3. **Participant recruitment** – Recruit 30 volunteers with at least 1 year programming experience via a public crowdsourcing platform (e.g., Prolific). Randomly assign each participant to two within‑subject conditions: (a) *LLM‑assisted* and (b) *baseline* (no assistance).  
4. **Experimental interface** – Deploy a lightweight Flask web app (containerized) that presents problem statements, records start/stop timestamps, and streams the participant’s code to the server. The app logs:  
   - `start_time`, `end_time` (seconds)  
   - submitted source file (UTF‑8)  
5. **Code execution & quality assessment** – For each submission:  
   - Run the provided test suite (auto‑generated from HumanEval or Codeforces) to compute **pass rate**.  
   - Compute **cyclomatic complexity** with `radon` (`radon cc`).  
   - Measure **test coverage** via `coverage.py`.  
   - Count **static‑analysis warnings** using `pylint` (Python) or `checkstyle` (Java).  
6. **Data aggregation** – Store all metrics in a CSV file on the runner; compute per‑condition means and standard deviations.  
7. **Statistical analysis** –  
   - Paired t‑test (or Wilcoxon signed‑rank if non‑normal) for completion time.  
   - Paired t‑tests for each quality metric.  
   - Report effect sizes (Cohen’s d) and 95 % confidence intervals.  
8. **Reproducibility** – All scripts, environment files (`requirements.txt`), and random seeds are version‑controlled; the entire pipeline can be executed end‑to‑end on a GitHub Actions free‑tier runner (< 6 h).  

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.
