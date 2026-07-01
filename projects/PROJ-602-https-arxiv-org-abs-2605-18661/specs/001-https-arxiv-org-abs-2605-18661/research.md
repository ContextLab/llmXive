# Research: AI for Auto-Research: Roadmap & User Guide Reproduction

## Overview
This research phase investigates the feasibility of reproducing the "AI for Auto-Research" pipeline on a CPU-only GitHub Actions runner. The primary challenge is the potential mismatch between the vendor code's requirements (likely GPU-accelerated LLMs) and the target environment (limited vCPU and RAM resources).

## Verified Datasets
The project does not download external datasets. It operates on the vendored code `external/awesome-ai-auto-research`.
- **Source**: `external/awesome-ai-auto-research` (Git Submodule)
- **Status**: Verified (Assumed present in repo root).
- **Note**: If the vendor code requires external API keys (e.g., OpenAI, Anthropic), the reproduction will run in "Mock Mode" to avoid cost and network dependency, unless a free-tier API is explicitly provided and logged.

## Dataset Strategy
| Variable/Component | Source | Verification Method | Fit for Purpose |
| :--- | :--- | :--- | :--- |
| **Vendor Code** | `external/awesome-ai-auto-research` | Git submodule initialization | **High**: This is the subject of the reproduction. |
| **API Usage Logs** | Vendor code output | Parsing `logs/` directory | **High**: Required for cost estimation (FR-003). |
| **Generated Artifacts** | Pipeline output | File system scan | **High**: Required for validation (FR-002). |
| **LLM Model** | Mock / Local (if small) | `src/mocks/llm_mock.py` | **Medium**: Replaces heavy GPU models to fit CI. |
| **Semantic Check Model** | `sentence-transformers/all-MiniLM-L6-v2` | CPU-tractable embedding model | **High**: Used for lightweight hallucination detection. |

## Methodological Decisions

### 1. CPU-Only Adaptation Strategy
**Decision**: The reproduction will prioritize "Mock Mode" for LLM inference, but include a "Semantic Sanity Check" for artifacts.
**Rationale**: The paper claims a low cost and "novelty," which implies real LLM usage. However, running a real LLM on a minimal CPU runner is infeasible (would exceed 6h and RAM).
**Implementation**:
- **CUDA Patcher**: `src/utils/cuda_patcher.py` forcibly injects `torch.set_device('cpu')` and patches `torch.cuda.is_available()` to return `False` to prevent vendor code from failing on initialization.
- If the vendor code attempts to load a large model, `src/mocks/llm_mock.py` will intercept the call and return a pre-defined, structurally valid text block.
- **Semantic Check**: The generated text will be analyzed using `sentence-transformers/all-MiniLM-L6-v2` to check for internal coherence and similarity to known "hallucination templates" (e.g., repetitive nonsense, fake citations).
- **Limitation**: This means the "novelty" and "cost" claims of the paper **cannot be fully validated numerically** if mock mode is active. The report will explicitly state "Unverifiable" for these claims. This is a necessary trade-off to ensure the pipeline runs.

### 2. Fabrication Detection Heuristics (Hybrid Approach)
**Decision**: Use a hybrid of syntactic heuristics and semantic embedding checks.
**Rationale**: Pure syntactic checks (empty strings, "TODO") have near-zero sensitivity to actual hallucinations. A secondary LLM judge is too heavy. Embedding models offer a middle ground.
**Implementation**:
- **Structural (Syntactic)**: Check for empty strings, "TODO", "PLACEHOLDER", "Lorem Ipsum", and repetitive patterns. This detects "empty" or "placeholder" content.
- **Semantic**: Use `all-MiniLM-L6-v2` to generate embeddings for generated paragraphs. Compare against a small set of "fake" templates (e.g., "Lorem ipsum dolor sit amet...") and check for low perplexity (indicating nonsense).
- **Scoring**: Calculate a `fabrication_score` (0.0-1.0).
  - High syntactic flags + High semantic anomaly = High score.
  - Low syntactic flags + Low semantic anomaly = Low score.
- **Limitation**: This may miss subtle hallucinations but provides a better proxy than heuristics alone. The report will explicitly state this limitation.

### 3. Cost Estimation
**Decision**: Calculate cost from logs; default to "N/A" if logs are missing or mock mode is active.
**Rationale**: The paper claims a significant value. If the vendor code does not log API calls, or if we run in mock mode, the cost is not calculable.
**Implementation**:
- Parse `logs/api_usage.json`.
- If present: Sum `cost` field.
- If absent or Mock Mode: Report "Cost not calculable (no logs found or mock mode active)".
- **Validation**: The report will explicitly state "Cost Claim: Unverifiable" if mock mode is used.

## Risk Assessment
- **Risk**: Vendor code crashes on CPU.
  - **Mitigation**: `src/utils/cuda_patcher.py` forces CPU mode; `src/mocks/llm_mock.py` provides a fallback.
- **Risk**: API rate limits.
  - **Mitigation**: Retry logic with exponential backoff (FR-006).
- **Risk**: No valid artifacts generated.
  - **Mitigation**: Validation script fails the build if artifacts are missing (SC-002).
- **Risk**: Semantic check is too heavy.
  - **Mitigation**: Use a lightweight sentence-transformer model that fits in RAM.; process text in small chunks.

## Validation Tiering
To ensure construct validity:
- **Structural Validation**: Pass/Fail (Artifacts exist, format valid).
- **Semantic Validation**: Risk Score (0.0-1.0).
- **Claim Validation**: "Verified", "Unverifiable", or "Failed".
  - If Mock Mode: "Cost" and "Novelty" claims are "Unverifiable".
  - If Real Mode: Claims are "Verified" or "Failed" based on logs and semantic score.