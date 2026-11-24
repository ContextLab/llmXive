# Neural Narrative Networks: Brain-Inspired Architecture for Story Generation

## Summary

This project implements a brain-inspired neural network architecture for narrative generation,
combining hippocampal-like pattern separation with prefrontal planning mechanisms. The system
processes real fMRI data from OpenNeuro dataset **ds001495** (matching spec FR-001) and the
ROCStories corpus to train and validate models that mimic human narrative processing.

The architecture consists of:
1. A Sparse Autoencoder (SAE) implementing hippocampal pattern separation
2. A Prefrontal Gating Module distinguishing plot coherence from episodic memory traces
3. A baseline **TinyLSTM (quantized transformer)** for comparison

All models are trained and evaluated on CPU-only hardware with strict memory constraints (<7GB RAM).

## Baseline Definition (FR-004)

The baseline model is a **TinyLSTM (quantized transformer)**. It is a compact
transformer-style sequence model whose recurrent/sequential core is sized to stay within the
CPU-only memory budget (≤ 2M trainable parameters), and it is dynamically quantized via
`torch.quantization.quantize_dynamic` (8-bit weights) so that it runs entirely on CPU within
the 7GB RAM limit. This baseline provides the comparison point against "standard transformer
architectures" under constrained memory, as required by FR-004 and the spec's assumption that
the baseline requires quantization techniques to meet the RAM limit. The implementation lives
in `code/models/baseline_lstm.py` (task T034), and the model exposes a `quantized` attribute
that must be `True` after quantization.

## Technical Context

### Data Sources

**Primary fMRI Dataset**: OpenNeuro ds001495
- A naturalistic fMRI study where subjects listen to stories
- Provides hippocampal and prefrontal timecourse data for RSA validation
- Downloaded via datalad to `data/raw/`
- Preprocessed to extract ROI timecourses for Left Hippocampus, Right Hippocampus, and DLPFC

**Text Corpus**: ROCStories (5-Word Stories)
- Available via HuggingFace datasets
- Used for training narrative generation models
- Sampled to `data/text/rocstories_sample.jsonl` for efficiency

### Biological Fidelity

The architecture implements a sparse autoencoder and gating module as defined in spec FR-002 and FR-003.
Specific biological sub-modules (DG, CA3, CA1) are not implemented as they are not defined in the spec.
The SAE achieves pattern separation through sparsity constraints (<20% activation).
The gating module distinguishes between:
- **Plot**: Coherence and narrative structure (prefrontal function)
- **Memory**: Episodic trace and semantic content (hippocampal function)

### Constraints

- CPU-only execution (no CUDA)
- Maximum RAM: 7GB
- Python 3.11+
- All data must be real; no synthetic placeholders

### Pipeline Stages

1. **Data Ingestion**: Download and preprocess fMRI and text data
2. **Model Training**: Train SAE with sparsity constraints and baseline TinyLSTM (quantized transformer)
3. **Generation**: Produce 1,000+ unique stories from both models
4. **RSA Analysis**: Compute representational similarity against fMRI data
5. **Validation**: Permutation testing and schema validation

## File Structure

```
code/
 ├── config.py # Global configuration
 ├── utils/
 │ ├── logging_config.py # Logging setup
 │ ├── schema_validation.py # Schema validators
 │ └── checksums.py # Integrity checks
 ├── 01_data_ingestion.py # Data download and preprocessing
 ├── 02_chunked_loader.py # Memory-efficient fMRI loading
 ├── 03_compute_event_averages.py
 ├── 05_validation.py
 ├── 06_update_checksums.py
 ├── models/
 │ ├── sparse_autoencoder.py
 │ ├── gating_module.py
 │ └── baseline.py # TinyLSTM (quantized transformer) baseline
 ├── train_sae.py # Training loop with retry logic
 └── verify_sparsity.py # Sparsity constraint verification

data/
 ├── raw/ # Raw downloaded data
 ├── processed/ # Preprocessed ROI timecourses
 ├── text/ # ROCStories corpus
 └── results/ # Model outputs and RSA matrices

specs/
 └── 001-neural-narrative-networks/
 ├── contracts/ # JSON schemas
 ├── data-model.md
 └── spec.md
```

## Execution Order

1. Run `code/00_setup_data_dirs.py` to initialize directories
2. Run `code/01_data_ingestion.py` to download and preprocess data
3. Run `code/train_sae.py` to train the sparse autoencoder
4. Run `code/verify_sparsity.py` to validate sparsity constraints
5. Run generation scripts to produce stories (brain-inspired model and TinyLSTM quantized baseline)
6. Run `code/03_rsa_analysis.py` for representational similarity analysis
7. Run `code/06_update_checksums.py` to finalize state

## Dependencies

See `code/requirements.txt` for pinned versions. Key packages:
- torch (CPU-only)
- nibabel, nilearn (fMRI processing)
- datasets (HuggingFace)
- sentence-transformers (semantic alignment)
- scikit-learn, numpy, pandas

## Verification

All outputs are validated against schemas in `specs/001-neural-narrative-networks-brain-inspired/contracts/`.
Checksums are computed and stored in `state/checksums.json` after each major stage.