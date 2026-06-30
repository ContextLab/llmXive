# Research: Reproduce & Validate Domino Speculative Decoding Framework

## 1. Problem Statement
The goal is to validate the Domino speculative decoding framework on a CPU-only environment. The primary challenge is the mismatch between the paper's likely GPU-accelerated setup (claiming a substantial speedup) and the strict constraints of the target CI environment (2 vCPU, 7GB RAM, no GPU).

**Methodological Resolution**: Instead of validating the *magnitude* of the speedup (which is hardware-dependent), we will validate the *mechanism*: does the draft model's acceptance rate correlate with throughput improvements? We will also measure the acceptance rate to explain why speedup may be < 1.0 on CPU.

## 2. Dataset Strategy
The benchmark requires a set of prompts to measure latency and throughput.
* **Requirement**: A small, diverse set of text prompts (limited to a reasonable token count) to keep runtime manageable and avoid OOM.
* **Verified Sources**:
 * *cnn_dailymail*: ` (Verified Source).
* **Strategy**: We will use the `cnn_dailymail` dataset (specifically the `1.0.0` or `3.0.0` split) and implement a **strict pre-processing filter** in the `runner.py` script to select only prompts with <= 512 tokens. This ensures we use a verified source while adhering to the time and memory constraints.
* **Constraint**: We will NOT invent a dataset URL. If the verified datasets are unsuitable (e.g., too long for the model context), we will fall back to a synthetic, hard-coded list of short prompts within the `runner.py` script to guarantee feasibility, noting this deviation in the report.
* **Rejection of Previous Sources**: The `lex-friddman` podcast dataset was rejected because transcripts are typically thousands of tokens long, exceeding the 512-token limit and risking OOM. The `ramil` and `sanskrit` datasets were rejected due to lack of relevance to general-purpose English LLM benchmarking.

## 3. Model Strategy
* **Target**: The paper mentions "Qwen3".
* **Constraint Check**: Qwen3 is likely a large model (>7B parameters). Loading a large language model in FP32 requires significant RAM. In FP, ~14GB. Even quantized (4-bit), it may require significant overhead on CPU.
* **Decision**: We will **substitute** the model with a smaller, CPU-feasible alternative.
 * **Candidate 1**: `Qwen/Qwen2-1.8B` (~1.8B params). Fits easily in 7GB RAM (FP16/FP32).
 * **Candidate 2**: `meta-llama/Llama-3-8B` (Quantized). *Risk*: 8-bit quantization often requires `bitsandbytes` (CUDA). Avoid unless a pure CPU quantization loader is confirmed.
 * **Selected Strategy**: Use `Qwen/Qwen2-1.8B` as the primary test model. It is small enough to run on CPU within memory limits and supports the HuggingFace `transformers` API used by Domino.
* **Rationale**: The goal is to validate the *algorithm* (Domino vs. Baseline), not the specific model weights. If Domino provides a speedup on a small model, it validates the mechanism. We will explicitly log this substitution.

## 4. Compute Feasibility & Methodology
* **Hardware**: 2 vCPU, 7GB RAM, No GPU.
* **Library Constraints**:
 * **PyTorch**: Must use the CPU-only wheel (`pip install torch --index-url).
 * **Quantization**: **NO** `bitsandbytes`, `load_in_8bit`, or `load_in_4bit` as these require CUDA. We will use standard FP16 or FP32.
 * **Domino Script**: The `run_hf_benchmark.sh` must be patched or wrapped to:
 1. Set `CUDA_VISIBLE_DEVICES=""`.
 2. Force `device_map="cpu"`.
 3. Inject the substituted model name.
* **Timeout**: A hard 45-minute timeout will be enforced via a shell wrapper or `timeout` command to prevent CI failure.
* **Memory Management**: We will process prompts in small batches (or one by one) to avoid accumulating memory overhead.
* **Statistical Rigor**: To account for CPU scheduling variance, we will run **5 independent iterations** (n=5) for each prompt. The final metrics will be the mean and standard deviation of these runs. This allows us to distinguish algorithmic speedup from noise.

## 5. Statistical & Validation Rigor
* **Metric**: Speedup Ratio = `Baseline_Latency / Domino_Latency`.
* **Baseline**: Standard autoregressive decoding (no draft).
* **Domino**: Speculative decoding with draft model.
* **Primary Success Criterion**:
 1. **Mechanism Validation**: The acceptance rate is measured and reported. If the acceptance rate is high (>50%) but speedup is < 1.0, we can attribute it to CPU overhead.
 2. **Statistical Significance**: A t-test (or non-parametric equivalent) is performed on the 5 runs to determine if the observed speedup is statistically significant (p < 0.05).
* **Comparison to Paper**: The paper claims a substantial improvement factor. We will explicitly state: "On CPU, speedup is expected to be lower due to lack of parallelism in GPU kernels. A speedup > 1.0 confirms the algorithm works, even if not at the magnitude of the GPU result."
* **Spec Conflict Handling**: We will execute FR-007 (compare to 5.49x) but flag the result as "Methodologically Invalid" in the report. The primary validation is the mechanism (acceptance rate).
* **Error Handling**: If the model fails to load (OOM), the script must catch the exception and output a "Failed: OOM" status with the memory stats.

## 6. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Model too large for 7GB RAM | Use `Qwen2-1.8B` instead of Qwen3. |
| `bitsandbytes` import error | Force CPU-only install; patch imports in `requirements-hf.txt` or `runner.py`. |
| Benchmark takes > 45 mins | Reduce prompt count to 5; enforce timeout; use n=5 runs (total ~25 runs). |
| Domino script hardcodes GPU | Patch the script or inject environment variables (`CUDA_VISIBLE_DEVICES`). |
| Dataset tokens > 512 | Implement strict token-length filter in `runner.py` before benchmarking. |