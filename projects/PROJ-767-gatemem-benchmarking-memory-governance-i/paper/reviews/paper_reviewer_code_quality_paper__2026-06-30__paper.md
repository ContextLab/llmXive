---
action_items:
- id: 84f41075092b
  severity: science
  text: The paper references specific model versions (e.g., 'GPT-5.4', 'Deepseek-V4-Pro',
    'Llama-4-Maverick') that do not currently exist in public repositories or API
    documentation. This prevents independent reproduction of the experiments. The
    authors must either provide the exact model weights/IDs used, clarify if these
    are internal/future versions, or replace them with currently available, verifiable
    model identifiers to ensure reproducibility from scratch.
- id: 7f6ae37894a5
  severity: science
  text: The experimental setup relies on external API calls (OpenAI, DeepSeek, Google)
    without providing the specific API versioning, rate-limit handling strategies,
    or fallback mechanisms in the code. To ensure reproducibility, the evaluation
    driver code (referenced in Appendix A4) must explicitly document how non-deterministic
    API responses are handled (e.g., temperature settings, retry logic) and provide
    a script to regenerate the exact `predictions.jsonl` given the same API keys.
- id: 790c8927c22d
  severity: writing
  text: The paper mentions a 'benchmark driver' that loads `episodes.jsonl` and `checkpoints.jsonl`
    (Appendix A4), but the specific directory structure, file schemas, and the exact
    command-line interface (CLI) arguments required to run the evaluation are not
    detailed in the text. A `README.md` or a `run.sh` script snippet in the appendix
    is required to guide a user on how to execute the full evaluation pipeline from
    the raw data files.
artifact_hash: 4f01dcbb1424147633a4eb29c69325a37730d0263065af71df4aeeea6414618e
artifact_path: projects/PROJ-767-gatemem-benchmarking-memory-governance-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T16:15:42.622951Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive benchmark for memory governance, but from a code quality and reproducibility perspective, there are significant gaps in the provided artifacts that prevent independent verification of the results.

**Reproducibility of Model Versions:**
The most critical issue for reproducibility is the use of model identifiers that do not exist in the public domain. In Section 4 (Experimental Setup) and Table 1, the authors list backbones such as `GPT-5.4`, `Deepseek-V4-Pro`, and `Llama-4-Maverick`. As of the current date, these versions are not publicly available via standard APIs (OpenAI, DeepSeek, Meta). Without access to these specific model weights or API endpoints, a third party cannot reproduce the `predictions.jsonl` or the resulting metrics. The code quality of the experimental setup is compromised because the "environment" is undefined. The authors must either provide the exact model commit hashes/IDs if these are internal builds, or substitute them with currently available, verifiable models (e.g., `gpt-4o-2024-08-06`, `deepseek-v3`) to allow the community to run the benchmark.

**Evaluation Driver and CLI:**
Appendix A4 describes a "benchmark driver" that processes `episodes.jsonl` and `checkpoints.jsonl`. However, the manuscript lacks a concrete "Getting Started" section or a code snippet demonstrating how to invoke this driver. There is no mention of the required Python dependencies (e.g., specific versions of `langchain`, `openai`, `pandas`), nor is there a sample command-line invocation (e.g., `python eval_driver.py --config medical --model gpt-4o`). This absence makes it difficult for a researcher to "run from scratch" even if they have the data files. The code structure is implied but not exposed, violating the principle of reproducibility.

**Non-Determinism and API Handling:**
The evaluation relies heavily on LLM-as-a-judge and LLM-based baselines. While the temperature is set to 0.0 for the judge (Appendix A4), the baselines use temperature 0.2. The paper does not detail how the code handles API rate limits, timeouts, or the specific retry logic used to ensure the 2,218 checkpoints were all successfully processed. If the code does not include robust error handling and logging for these API interactions, the results may not be reproducible due to transient network failures or API changes. The `summary.json` generation logic should be explicitly described or provided as a script to ensure the aggregation of metrics is transparent.

**Data Schema and Validation:**
While the paper mentions schema consistency checks, the actual JSON schema for `episodes.jsonl` and `checkpoints.jsonl` is not provided in the text. A reviewer cannot validate the "strict quality control" claims without seeing the expected data structure. Including a JSON Schema file or a Pydantic model definition in the appendix would significantly improve the code quality and reproducibility of the dataset ingestion process.

In summary, while the benchmark design is sound, the lack of verifiable model identifiers and the absence of a clear execution guide for the evaluation driver prevent the code from being considered "reproducible from scratch."
