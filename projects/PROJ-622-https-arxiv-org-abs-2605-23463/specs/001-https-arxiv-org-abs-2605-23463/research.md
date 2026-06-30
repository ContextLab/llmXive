# Research: Reproduce & Validate StepAudio 2.5 Technical Report

## Dataset Strategy

The reproduction relies on the `WenetSpeech_testnet_long.json` configuration file provided within the vendored submodule `external/wenetspeech-testnet-long`.

| Dataset Name | Source / URL | Verified Status | Variable Fit Analysis |
| :--- | :--- | :--- | :--- |
| WenetSpeech (Testnet Long) | `external/wenetspeech-testnet-long/WenetSpeech_testnet_long.json` (Manifest) + **Remote WenetSpeech Corpus** | **Verified (Manifest Only)** | **High Fit**: The JSON is expected to contain `audio_url` (or `audio_path` pointing to remote) and `transcription` fields. <br> *Critical*: The audio files are **NOT** bundled in the submodule. The plan MUST implement a **streaming/chunked download** strategy to fetch audio files on-demand from the official WenetSpeech source (e.g., Baidu Cloud/AWS S3) to stay within the 14GB disk limit. <br> *Constraint*: If the JSON contains local paths implying bundled data >14GB, the run halts with `E_DISK_EXCEEDED`. |
| StepAudio 2.5 Model Weights | **UNVERIFIED (arXiv:2605.23463 is future-dated)** | **Blocking Constraint** | **Critical Check**: The arXiv ID `2605.23463` is invalid. The plan must locate a valid, existing model source. If not found, the run halts with `E_SCOPE_INVALID`. No fallback to other models is permitted. |

**Decision**: The plan assumes the audio data is fetched via a streaming mechanism triggered by the wrapper script. If the dataset requires >14GB of disk space for caching, the plan will implement a "streaming" strategy where files are deleted immediately after processing.

## Paper Claims Extraction (StepAudio 2.5 Technical Report)

*Note: The specific values are deferred to the implementation phase where the paper is parsed. The following are the expected claim categories based on the spec.*

| Claim Category | Metric | Paper Claim (Reference) | Validation Target |
| :--- | :--- | :--- | :--- |
| **ASR Performance** | Word Error Rate (WER) | [deferred] (Abstract/Results Table) | Extract WER from `results.json`. **Calculate 95% CI via Bootstrap (N>=30) or Exact Binomial Test (N<30).** Compare against [deferred] using statistical significance, not a fixed threshold. |
| **TTS Quality** | Mean Opinion Score (MOS) | [deferred] (Qualitative/Quantitative) | **Proxy Metric**: Use DNSMOS P.835. **Comparison**: Compare against public baselines (e.g., Whisper). **If the paper claims human MOS, flag as "Needs Clarification"** (no calibration study possible). |
| **Latency** | Real-time Factor (RTF) | [deferred] (e.g., < 0.1s) | Measure `end_time - start_time` vs audio duration. |
| **State-of-the-Art** | Baseline Comparison | [deferred] (e.g., vs Whisper, Conformer) | Validate if the output includes a comparison table or if the script is designed to benchmark against a baseline. |

## Compute Feasibility Analysis

**Constraint**: GitHub Actions Free Tier (2 vCPU, 7GB RAM, 14GB Disk, 6h limit, No GPU).

1.  **Memory Pressure**:
    *   *Risk*: Audio models (especially transformers) often exceed 7GB RAM when loaded in full precision.
    *   *Mitigation*: **Strict Protocol**: The plan does **not** attempt to force quantization (e.g., `torch.ao.quantization`) via environment variables, as this violates the "no modification" constraint (FR-001) and is technically infeasible for pre-compiled models without graph modification.
    *   *Action*: Phase 0 will detect if the model requires >7GB RAM or GPU. If so, the run terminates with `E_MODEL_MISSING`. The project status becomes "Blocked" until a CPU-compatible variant is provided or the spec is updated.
2.  **Runtime**:
    *   *Risk*: Processing the full "long" test set may exceed 6 hours on 2 vCPUs.
    *   *Mitigation*: If `total_entries > MAX_PROCESSABLE_ENTRIES` (defined as [deferred] entries), the plan will use **stratified random sampling** based on `speaker_id` and `duration` to ensure representativeness. The sampling method, seed, and `strata_columns` must be logged in `run_metadata.json`.
3.  **Disk Space**:
    *   *Risk*: Intermediate audio files and model weights may exceed 14GB.
    *   *Mitigation*: The wrapper script will monitor disk usage and delete intermediate artifacts (e.g., raw audio buffers) immediately after processing. **Streaming download** is mandatory for audio files.

## Statistical & Methodological Rigor

*   **Reproducibility**: The plan mandates `run_metadata.json` to capture the exact environment hash (Python version, library versions) and **sampling strategy** (if used) to ensure the results can be replicated.
*   **Validation Method**:
    *   **WER**: Instead of a fixed heuristic (e.g., [deferred] difference), the plan uses **Bootstrap Resampling (N>=30)** or **Exact Binomial Test (N<30)** to calculate a 95% confidence interval or p-value. A "Discrepancy" is only flagged if the paper's claimed WER falls outside this interval or the p-value < 0.05.
    *   **MOS**: The plan acknowledges that MOS is a human metric. The validation will use **DNSMOS P.835** as a proxy. The report will explicitly state: "Proxy Metric: DNSMOS (Comparison: Public Baseline)" and compare the proxy against a calibrated benchmark, or flag as "Needs Clarification" if the paper only reports human MOS.
*   **Bias**: The "testnet" subset may not be representative of the full WenetSpeech distribution. The validation report will explicitly state this limitation.

## Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Invalid Scope (arXiv ID)** | High (Run fails) | Verify arXiv ID/HF repo existence. If not found, exit with `E_SCOPE_INVALID` and "Blocked" status. |
| **GPU Dependency / RAM Exceeded** | High (Run fails) | Check `prepare.py` for `device='cuda'` or model size >7GB. If found, **exit with `E_MODEL_MISSING`**. No forced quantization. |
| **Network Timeout** | Medium (Run hangs) | Implement retry logic (3 attempts, exponential backoff) in the wrapper script. |
| **Corrupted Input** | Medium (Run crashes) | Implement pre-flight validation of `WenetSpeech_testnet_long.json` against `contracts/wenetspeech-config.schema.yaml`. |
| **Disk Space Exceeded** | High (Run fails) | Pre-flight check for local paths implying bundled data. If detected, exit with `E_DISK_EXCEEDED`. |
| **Missing Ground Truth** | High (Validation impossible) | Pre-flight check for `transcription` field in input JSON. If missing, exit with `E_MISSING_GROUND_TRUTH`. |
| **Small Sample Size** | Medium (Statistical invalidity) | If N < 30, switch from Bootstrap to Exact Binomial Test. |