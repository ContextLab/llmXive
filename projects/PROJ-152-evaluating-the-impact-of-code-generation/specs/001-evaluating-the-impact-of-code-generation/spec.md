# Specification: Evaluating the Impact of Code Generation Models on Code Security

## 1. Introduction
This project evaluates the security implications of using Large Language Models (LLMs) for code generation. We compare three open-source models (StarCoder-Base, CodeGen, GPT-NeoX) across a standardized set of security-focused prompts.

## 2. Scope and Constraints (Amended)

### 2.1 Resource Constraints
The project is constrained by the following execution environment limitations:
- **Memory**: GitHub Actions runners are limited to 7GB RAM.
- **Time**: Maximum execution time per run is 6 hours.
- **Compute**: CPU-only inference (no GPU access).

### 2.2 Amended Scope (FR-002, SC-005)
Due to the resource constraints listed above, the original scope of N=100 prompts has been amended to **N=30 prompts** and **N=90 code snippets**.
- **Prompt Composition**:
 - 10 prompts sourced from the CodeXGLUE dataset (filtered for security relevance).
 - 20 handcrafted prompts covering specific web security categories (SQL, XSS, Auth, Injection).
- **Snippet Generation**:
 - Each prompt is processed by 3 models, resulting in 30 prompts * 3 models = **90 total snippets**.
- **Justification**: This reduction ensures the pipeline can complete within the 6-hour window and 7GB memory limit while maintaining statistical validity for the comparative analysis.

## 3. Functional Requirements

### 3.1 Data Acquisition (FR-001)
- System shall download prompts from CodeXGLUE via HuggingFace.
- System shall filter prompts based on security keywords (SQL, XSS, auth, etc.).
- System shall store a subset of top candidates (N=10) with checksums.

### 3.2 Generation (FR-002) [AMENDED]
- System shall generate code snippets for **N=30 prompts** (10 CodeXGLUE + 20 Handcrafted).
- System shall generate exactly **N=90 snippets** (30 prompts * 3 models).
- Models must be loaded with 4-bit quantization to fit memory constraints.
- Generation timeout is set to 120s per snippet.

### 3.3 Analysis (FR-003)
- System shall run Bandit, Semgrep, and CodeQL on generated snippets.
- System shall map raw scanner output to NIST severity levels.

### 3.4 Metrics & Statistics (FR-004)
- System shall calculate Vulnerability Density (V/100LOC).
- System shall perform Kruskal-Wallis and Dunn's tests.
- System shall perform ZINB regression if zero-inflation >= 20%.

## 4. Non-Functional Requirements

### 4.1 Reproducibility (SC-005) [AMENDED]
- All random seeds must be pinned.
- All artifacts must be hashed and logged in `state.yaml`.
- The dataset size is fixed at **N=30 prompts** to ensure reproducibility within the 6-hour CI window.

### 4.2 Performance
- Pipeline must complete within 6 hours on a standard GitHub Actions runner (7GB RAM).
- Model loading must use CPU-compatible 4-bit quantization.

## 5. Data Models
- **Prompts**: JSON structure with ID, text, source, and category.
- **Snippets**: CSV with snippet_id, model, prompt_id, code, line_count.
- **Findings**: CSV with finding_id, snippet_id, scanner, CWE, severity.

## 6. Validation Criteria
- Success is defined as the generation of `data/generated/snippets.csv` (90 rows) and `data/findings/raw_findings.csv` within the time/memory budget.
- Statistical significance is determined at p < 0.05 (Bonferroni adjusted).