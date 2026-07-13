# Research: Neural Narrative Networks

## Research Question
Do computational models incorporating hippocampal-like pattern separation and prefrontal-like executive control produce narrative structures that better match human fMRI activation patterns during story comprehension compared to standard architectures with the same complexity?

## Dataset Strategy

### Verified Datasets
The following datasets are used, strictly adhering to the verified URLs provided in the specification.

| Dataset | Purpose | Verified Source (URL) | Loading Strategy |
|:--- |:--- |:--- |:--- |
| **OpenNeuro ds000208** | fMRI BOLD timecourses (Hippocampus, DLPFC) during naturalistic story listening. | `https://openneuro.org/datasets/ds000208` | Load via `datalad` or `huggingface-datasets` (if mirrored). Extract ROIs using **Harvard-Oxford Atlas** (via `nilearn`). |
| **ROCStories** | Narrative text corpus for generation. | ` | Load via `datasets.load_dataset`. Sample a large corpus of stories for generation. |
| **Harvard-Oxford Atlas** | Anatomical definitions (Hippocampus/DLPFC). | Native to `nilearn` (no external URL). | Use `nilearn.datasets.fetch_atlas_harvard_oxford` for standard, versioned coordinates. |

**Note on Dataset Variable Fit**:
- **Stimulus Mismatch**: OpenNeuro ds000208 uses naturalistic stories (e.g., "The Man Who Mistook His Wife for a Hat") which differ from ROCStories.
- **Alignment Strategy**: To ensure a valid RSA comparison, we will **not** compare across different stories. Instead, we will:
 1. Identify a subset of events in ds000208 that share semantic themes with ROCStories (or use a common subset if available).
 2. Implement a **Cross-Corpus Alignment** using `sentence-transformers` to map event boundaries in ROCStories to the continuous timecourse in ds000208 based on semantic similarity of event summaries.
 3. **Restrict RSA Analysis** *only* to the aligned events where the semantic match exceeds a threshold, ensuring the "stimulus-driven" similarity is controlled for.

## Model Architecture Strategy

### Brain-Inspired Model (Experimental)
1. **Pattern Separation Layer (Hippocampal)**: Implemented as a Sparse Autoencoder (SAE).
 * **Mechanism**: Encoder maps input narrative embeddings to a high-dimensional latent space; a sparsity penalty (L1 or KL divergence) enforces activation density ≤ 0.20.
 * **Biological Map**: Mimics the dentate gyrus/CA3 pattern separation function.
 * **Constraint**: Must run on CPU; uses `torch.nn.Linear` with custom sparsity loss.
2. **Executive Control Module (Prefrontal)**: Implemented as a Gating Mechanism.
 * **Mechanism**: A lightweight MLP evaluates the coherence of the latent representation against a "plot" constraint vector. It modulates the flow of information to the output decoder.
 * **Biological Map**: Mimics DLPFC role in working memory and coherence maintenance.
 * **Distinction**: Unlike standard attention, this gate explicitly separates "episodic trace" (memory) from "narrative structure" (plot).

### Baseline Model (Control)
* **Architecture**: **Standard Sparse Autoencoder (No Gating)**.
* **Rationale**: To isolate the effect of the "hippocampal-like" sparsity and "prefrontal" gating, the baseline must match the experimental model's architectural class (Autoencoder) but lack the specific biological mechanisms (Gating).
 * **Mechanism**: Same SAE architecture as the experimental model but *without* the sparsity constraint (or with relaxed sparsity) and *without* the gating module.
 * **Constraint**: Must run on CPU; matches memory footprint of the experimental model.
* **Correction**: The previous "TinyLSTM" baseline was rejected as it introduced a confound between architecture class (RNN vs. Autoencoder) and the mechanism of interest.

## Statistical Analysis Strategy

### Representational Similarity Analysis (RSA)
1. **Input**:
 * **Neural**: BOLD timecourses averaged per story event for Hippocampus and DLPFC (aligned via semantic similarity).
 * **Model**: Hidden state vectors from the SAE and Baseline SAE at corresponding aligned story events.
2. **Metric**: Pearson correlation distance (1 - r) between pairwise event representations.
3. **Matrix Construction**: Symmetric matrices for (Model vs. Human) and (Baseline vs. Human).

### Permutation Test
* **Null Hypothesis**: The RSA distance between the brain-inspired model and human data is not significantly different from the baseline.
* **Procedure (Label Shuffling)**:
 1. Compute observed difference in RSA distances ($\Delta_{obs}$).
 2. **Permute Condition Labels**: Randomly shuffle the *labels* (event indices) of the Model RDM relative to the Human RDM *before* computing the correlation distance. This preserves the internal structure of the RDMs while breaking the specific alignment.
 3. Compute $\Delta_{perm}$ for each permutation.
 4. Calculate p-value: $P(\Delta_{perm} \geq \Delta_{obs})$.
* **Convergence Check**: Variance of p-value over the final 1,000 permutations must be < 0.001. If not, flag as "borderline".
* **Correction**: The previous "Row/Column Permutation" of the final matrix was invalid as it destroys metric structure. Label shuffling is the standard, valid method for RSA.

## Statistical Rigor & Limitations

* **Multiple Comparisons**: RSA is computed for two ROIs (Hippocampus, DLPFC). A Bonferroni correction or False Discovery Rate (FDR) will be applied to the final p-values to control family-wise error rate.
* **Power Analysis**: The sample size is limited by the verified dataset availability. This is acknowledged as a power limitation. Results will be interpreted as "associational" rather than definitive causal proof of mechanism. The permutation test assesses the significance of the *observed difference* but cannot fully overcome the low degrees of freedom inherent in small-N fMRI studies.
* **Causal Inference**: The study is observational regarding the model's fit to human data. No randomization of human subjects occurs; claims are limited to "better alignment" rather than "causal mechanism validation".
* **Collinearity**: The SAE latent space and the gating output are definitionally related (gating operates on SAE output). Independent effects will not be claimed; the system is treated as a unified "brain-inspired" module.
* **Measurement Validity**: The RSA metric assumes that representational geometry is preserved between fMRI BOLD signals and model hidden states. This is a standard assumption in computational neuroscience but acknowledged as a limitation.
* **Stimulus Control**: To avoid tautological results (model trained on X matches brain responding to X), RSA is restricted to the **Common Stimulus Subset** where the semantic alignment between ROCStories and ds000208 is verified.

## Compute Feasibility & Rationale

* **CPU-Only**: All models use standard `torch` CPU operations. No CUDA, no 8-bit quantization libraries requiring GPU drivers.
* **Memory Management**:
 * fMRI data is loaded in chunks (subject-by-subject) to avoid memory overflow.
 * Story generation is batched with a configurable maximum batch size.
 * RSA matrices are computed incrementally to avoid storing full $N \times N$ float64 matrices in RAM if $N$ is large (though $N=1000$ is manageable).
* **Runtime**: Estimated several hours for generation + 1.5 hours for RSA/Permutation. Total < 6 hours.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use Standard SAE Baseline** | To isolate the effect of "Gating" and "Sparsity", the baseline must match the experimental architecture class (Autoencoder) rather than using an LSTM. |
| **Permutation Test (Label Shuffling)** | Row/column permutation of RDMs is invalid. Label shuffling preserves metric structure while breaking alignment. |
| **Cross-Corpus Alignment** | ds000208 and ROCStories are different stories. Semantic alignment is required to establish a 1:1 mapping for RSA. |
| **Harvard-Oxford Atlas** | Standard, versioned atlas via `nilearn` is more reproducible than user-uploaded parquet files. |
| **OpenNeuro ds000208** | ds001495 (object recognition) lacks story comprehension conditions. ds000208 is the correct dataset for narrative RSA. |
