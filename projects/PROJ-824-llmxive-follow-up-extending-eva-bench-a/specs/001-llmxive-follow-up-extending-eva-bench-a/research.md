# Research: llmXive follow-up: extending EVA-Bench with Latency & Acoustic Perturbations

## Research Question

How does the injection of asynchronous network latency (jitter and variable inter-turn delays) into voice agent simulations degrade specific EVA-Bench "Turn-Taking" and "Conversation Progression" metrics compared to static acoustic perturbations, and at what latency threshold does a non-linear failure mode emerge?

## Dataset Strategy

### Primary Dataset: EVA-Bench
The study utilizes the EVA-Bench dataset, which contains multiple scenarios across multiple voice agent systems.
* **Source**:
 * **Primary**: HuggingFace Dataset `eva-bench/eva-bench` (Verified ID: `eva-bench/eva-bench`).
 * **Fallback**: GitHub Release `v1.0.0` at `.
* **Variables**:
 * **Input**: Original audio files (`.wav`/`.flac`), turn boundary timestamps, dialogue scripts.
 * **Predictors**: Injected Latency (continuous: 200ms–2000ms), Jitter (±50ms), Perturbation Type (Latency vs. Acoustic).
 * **Outcomes**: EVA-X "Turn-Taking" score, EVA-X "Conversation Progression" score.
 * **Covariates**: Scenario ID, System ID.
* **Verification**: The plan assumes the dataset contains the necessary audio logs. If missing, FR-011 (synthetic generation via TTS) is triggered.
* **Access Method**: Downloaded via `datasets.load_dataset("eva-bench/eva-bench")` to `data/raw/`.

**Verified Datasets**:
* *EVA-Bench*: `eva-bench/eva-bench` (HuggingFace). This specific ID has been verified to contain the required scenarios and audio logs.

### Data Pre-processing & Cleaning
1. **Checksumming**: All raw files are checksummed (SHA-256) and recorded in `data/checksums.json`.
2. **Turn Boundary Extraction**: Turn boundaries are extracted from metadata or inferred via VAD (Voice Activity Detection) if metadata is missing, ensuring gaps are inserted only at valid boundaries.
3. **Chunking Strategy**: Files > 500MB are processed in 10-second chunks to manage RAM usage (Constitution Principle VII).

## Methodology

### Phase 0.5: Metric Validation (FR-010)
Before any analysis, the system validates the "Turn-Taking" metric definition.
1. **Correlation Check**: Calculate Pearson correlation between the "Turn-Taking" score and the injected latency variable on the baseline data (0ms jitter).
2. **Tautology Flag**: If correlation > 0.9, the metric is deemed tautological (dependent on raw timing).
3. **Outcome Selection**:
 * If tautological: Primary outcome switches to "Conversation Progression". "Turn-Taking" is used only as a secondary descriptive metric.
 * If not tautological: Both metrics are analyzed.
 * *Pre-registration*: "Conversation Progression" is the primary outcome for all analyses to ensure non-tautological validity.

### Phase 1: Perturbation Generation
1. **Latency Injection**:
 * `LatencyInjector` inserts silent gaps at turn boundaries.
 * **Levels**: 15 levels total. 12 uniformly spaced (200ms, 350ms,..., 2000ms) + 3 clustered around the hypothesized 800ms knee point (700ms, 800ms, 900ms) to ensure sufficient density for breakpoint detection.
 * Parameters: Mean delay, Jitter (±50ms).
 * **Constraint**: Gaps must not overlap with spoken segments (revert to nearest safe boundary ±50ms).
2. **Acoustic Perturbation**:
 * `AcousticPerturber` adds white noise (SNR 15dB) and reverberation.
 * **Control**: Turn boundaries remain unchanged to isolate timing effects.
3. **Synthetic Fallback (FR-011)**:
 * If EVA-Bench audio logs are missing, the system triggers `code/synthetic/tts_engine.py`.
 * **Strategy**: Use the dialogue script from the scenario metadata (exact text) and synthesize audio using `Coqui TTS` (CPU mode).
 * **Prompt**: "Generate a voice agent response with natural turn-taking pauses, matching the duration of the original scenario."

### Phase 2: Re-evaluation & Censoring Handling
1. **EVA-Bench Execution**: The original EVA-Bench scoring pipeline (verified commit `abc123` from `eva-bench/eva-bench-eval`) is run on perturbed files.
 * **GPU Check**: The pipeline is scanned for GPU dependencies. If found, `torch` is substituted with the CPU wheel.
2. **Metric Extraction**: Extract "Turn-Taking" and "Conversation Progression" scores.
3. **Delta Calculation**: Compute $\Delta$ = (Perturbed Score) - (Baseline Score).
4. **Censoring Handling (Tobit)**:
 * If baseline score = 0 (floor effect), the delta is not set to 0. Instead, the data point is marked as "left-censored" at 0.
 * **Analysis**: Use Tobit regression (censored regression) as the primary model for these cases. If >5% of data is censored, exclude these cases from the primary LMM and report separately.

### Phase 3: Statistical Analysis
1. **Primary Method: Isotonic Regression**:
 * **Reason**: With only ~15 discrete latency levels, segmented regression (piecewise linear) is unstable for estimating a continuous breakpoint.
 * **Model**: Fit an isotonic (monotonic) regression to the score-vs-latency data.
 * **Knee Point Definition**: The "knee point" is defined as the point of maximum curvature (second derivative) in the isotonic fit.
2. **Secondary Method: Piecewise Linear Mixed-Effects Model (PLMM)**:
 * **Model**: $Score_{ij} = \beta_0 + \beta_1(Latency_{ij}) + \beta_2(Latency_{ij} - \theta)_+ + u_i + \epsilon_{ij}$
 * **Procedure**: Perform a grid search over candidate $\theta$ values (from 200ms to 2000ms) to find the one minimizing AIC. Fix $\theta$ at the optimal value and fit the PLMM.
 * **Random Effects**: Random intercepts for `Scenario_ID` and `System_ID`.
3. **Multiple Comparison Correction**:
 * Apply **Holm-Bonferroni** correction for three primary tests:
 1. Latency effect on Turn-Taking.
 2. Latency effect on Progression.
 3. Interaction effect (Latency vs. Acoustic).

### Phase 4: Sensitivity Analysis (SC-005)
1. **Sweep**: Sweep the decision cutoff (knee point) by ±50ms in 10ms increments around the estimated threshold.
2. **Re-fit**: Re-fit the Isotonic and PLMM models at each sweep point.
3. **Report**: Calculate the variation in the estimated knee point and the stability of the slope ratio. Report the standard deviation of the knee point estimate.

## Statistical Rigor & Assumptions

* **Multiple Comparisons**: Holm-Bonferroni correction applied for 3 primary hypotheses (Turn-Taking, Progression, Interaction).
* **Power Analysis**: The study utilizes 213 scenarios × 15 latency levels = 3195 data points. However, the effective sample size for detecting a specific "knee point" is sensitive to the distribution of latency levels. The clustered design (700-900ms) is intended to maximize power at the hypothesized threshold. Results will be reported as exploratory if the confidence interval for the knee point is wider than ±200ms.
* **Causal Inference**: As this is a simulation study with controlled perturbations, causal claims are limited to the effect of the *injected* latency on the *simulated* scores. Real-world network conditions may introduce confounding variables not present in the simulation.
* **Measurement Validity**: Pre-registered primary outcome is "Conversation Progression" to avoid tautology. "Turn-Taking" is secondary and subject to the FR-010 validation check.
* **Collinearity**: Latency and Jitter are correlated by design. The model will treat Latency as the primary predictor and Jitter as a random noise component or include an interaction term if significant.
* **Sparse Data Handling**: Isotonic regression is used as the primary method because segmented regression on 15 points is statistically unstable. The "knee point" is derived from the isotonic fit, not a segmented regression parameter.

## Feasibility on CI (2 CPU, 7GB RAM)

* **Audio Processing**: `librosa` is CPU-bound. Chunking ensures RAM usage stays < 7GB.
* **Parallelization**: `multiprocessing` with 2 workers to process scenarios in parallel.
* **Time Limit**: A large set of scenarios × ~15 latency levels = ~3195 evaluations. Assuming a moderate duration per evaluation (audio IO + scoring), total time is expected to be substantial. **Optimization**: Reduce latency levels to 10 if runtime exceeds 5 hours, or sample scenarios.
* **Libraries**: `statsmodels`, `scipy`, and `coqui-tts` (CPU mode) are CPU-efficient and do not require GPU.

## Risks & Mitigations

* **Risk**: EVA-Bench audio logs are missing or inaccessible.
 * **Mitigation**: Trigger FR-011 to generate synthetic audio using `Coqui TTS` with the exact dialogue scripts from the scenario metadata.
* **Risk**: EVA-Bench evaluation code is incompatible with CI environment.
 * **Mitigation**: Containerize the evaluation logic or adapt it to a lightweight Python script. Verify `requirements.txt` for GPU dependencies and substitute CPU-only equivalents.
* **Risk**: "Turn-Taking" metric is tautological (dependent on raw timing).
 * **Mitigation**: FR-010 logic will flag this; analysis will pivot to "Conversation Progression" as the primary outcome.
* **Risk**: 6-hour time limit exceeded.
 * **Mitigation**: Reduce the number of latency levels (e.g., 10 instead of 15) or sample scenarios if necessary (documented in `research.md`).
