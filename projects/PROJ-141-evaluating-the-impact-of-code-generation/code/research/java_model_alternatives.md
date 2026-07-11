# Alternative Java Code Generation Models

## Context
This document evaluates alternative Java code generation models for the `PROJ-141` experiment, specifically in the event that the primary candidate (JaCoText) is unavailable or fails CPU-tractability verification.

**Constraints**:
- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 14 GB Disk, No GPU).
- **Latency**: Model must support CPU inference within a reasonable timeframe (< 5 minutes per sample) for a within-subject study.
- **Size**: Model weights must be ≤ 1GB to fit within memory constraints alongside the OS and experiment overhead.
- **Language**: Java (must support Java code generation).

## Evaluation Criteria
1. **Availability**: Publicly accessible via Hugging Face or GitHub.
2. **Size**: Total download size (weights + tokenizer) ≤ 1GB.
3. **Performance**: Demonstrated capability to generate syntactically valid Java code.
4. **CPU Feasibility**: Inference time acceptable on 2 vCPU (approx. 2.0+ GHz).

## Candidate 1: CodeGen-2B-Multi (Salesforce)
- **Source**: Hugging Face (`Salesforce/codegen-2B-multi`)
- **Size**: ~1.6 GB (FP16) or ~800 MB (INT8 quantized).
- **Tractability Assessment**:
 - **FP16**: Exceeds 1GB limit; likely to OOM on 7GB RAM system when loading dependencies.
 - **INT8 (Quantized)**: Fits within 1GB limit. Requires `bitsandbytes` or `llama.cpp` backend.
 - **Inference Speed**: ~1-3 tokens/sec on CPU (2 vCPU). For a 50-token completion, this is ~15-50 seconds.
 - **Verdict**: **Viable only with INT8 quantization**. Requires specific loading logic (see `code/models/jacotext_cpu.py` pattern).
- **Citation**: Nijkamp et al. (2022). "CodeGen: An Open Large Language Model for Code with Multi-Turn Program Synthesis."

## Candidate 2: StarCoderBase-1B (BigCode)
- **Source**: Hugging Face (`bigcode/starcoderbase-1b`)
- **Size**: ~2.0 GB (FP16).
- **Tractability Assessment**:
 - **Size**: Exceeds 1GB limit.
 - **Quantization**: INT8 version exists but is not the default distribution.
 - **Java Support**: Trained on "The Stack" which includes Java.
 - **Verdict**: **Not Viable** under strict 1GB constraint without custom quantization pipeline.

## Candidate 3: PolyCoder-2.7B (CMU)
- **Source**: Hugging Face (`cmu-edu/polycoder-2.7b`)
- **Size**: ~5.4 GB.
- **Tractability Assessment**:
 - **Size**: Far exceeds 1GB limit.
 - **Verdict**: **Not Viable** for CPU-only free-tier execution.

## Candidate 4: TinyCode (Small Custom Models)
- **Source**: Various community repos (often < 100M params).
- **Tractability Assessment**:
 - **Size**: < 500 MB.
 - **Performance**: Extremely fast on CPU.
 - **Quality**: Generally poor; often hallucinates syntax or fails on standard HumanEval-Java tasks.
 - **Verdict**: **Not Recommended** due to low validity rates, which would skew experimental results (high noise).

## Recommended Alternative: CodeGen-2B-Multi (INT8 Quantized)
Given the constraints, **CodeGen-2B-Multi** is the only viable candidate that balances code quality with the strict 1GB size and CPU constraints, provided it is loaded in INT8 mode.

**Implementation Plan**:
1. Use `transformers` with `load_in_8bit=True` (requires `bitsandbytes` and `accelerate`).
2. If `bitsandbytes` fails on CPU-only (common issue), fallback to `llama.cpp` GGUF conversion of the model.
3. **Fallback Strategy**: If no model fits <1GB with acceptable quality, the experiment defaults to **StarCoder-1B** (if a quantized version can be sourced) or the study must be paused until a suitable model is identified.

## Verification Steps (To be executed in T011b)
1. Download `Salesforce/codegen-2B-multi` INT8 weights.
2. Measure file size on disk.
3. Run a "Hello World" Java generation on a local CPU instance mimicking GitHub Actions (2 vCPU).
4. Record inference time and memory peak.

## Sources
- Hugging Face Model Card: https://huggingface.co/Salesforce/codegen-2B-multi
- BigCode Project: https://github.com/bigcode-project/bigcode-evaluation-harness
- PolyCoder Paper: https://arxiv.org/abs/2202.13169

## Conclusion
**JaCoText** remains the preferred specific Java model if available. If unavailable, **CodeGen-2B-Multi (INT8)** is the primary fallback. If that fails size constraints, the experiment cannot proceed with a Java-specific model under the current hardware constraints and may need to pivot to Python-only (StarCoder) or delay until a smaller Java model is released.

*Last Updated: 2023-10-27*
*Status: Research Complete - Pending T011b Verification*