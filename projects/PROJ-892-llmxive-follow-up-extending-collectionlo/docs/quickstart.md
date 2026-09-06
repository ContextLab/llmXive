# Quickstart Guide

This guide provides instructions for running the llmXive automated science pipeline for the Quantization Robustness of Multi-Effect LoRA Adapters project.

## Prerequisites

- Python 3.9+
- Required dependencies (see `code/requirements.txt`)
- Access to HuggingFace Hub (for model downloads)

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The pipeline is executed in phases. Run the following commands in order:

### Phase 0: Adapter Synthesis & Verification

```bash
# T001a: Load and verify source LoRAs
python code/main.py --phase adapter_synthesis

# T002: Merge collection LoRA
python code/main.py --phase merge
```

### Phase 1: Setup

```bash
# T004a: Create config.yaml
# (Already created in project setup)

# T004b: Map prompts to effects
python code/main.py --phase map_prompts

# T004c: Validate prompt mapping
python code/main.py --phase validate_prompts
```

### Phase 2: Foundational

```bash
# T001e: Compute merged ranks (T009c dependency)
python code/main.py --phase compute_merged_ranks

# T009c: Load and validate subspace ranks
python code/main.py --phase validate_subspace_ranks

# T007b-1: Load verified CollectionLoRA adapter
python code/main.py --phase load_adapter

# T007c: Download base model
python code/main.py --phase download_base_model
```

### Phase 2.5: Reference Generation

```bash
# T035: Generate distractor references
python code/main.py --phase generate_distractors

# T011c: Generate FP16 reference images
python code/main.py --phase generate_fp16_refs
```

### Phase 3: Baseline Fidelity Measurement

```bash
# T010b: Load FP16 adapter
# (Integrated into generation loop)

# T011: Generate baseline images
python code/main.py --phase generate --level FP16

# T014a: Run baseline generation loop
python code/main.py --phase baseline
```

### Phase 4: Quantization Impact Analysis

```bash
# T016a: Quantize LoRA adapters
python code/main.py --phase quantize

# T017: Generate quantized images
python code/main.py --phase generate --level INT8
python code/main.py --phase generate --level INT4

# T020a: Run quantized generation loop
python code/main.py --phase quantized
```

### Phase 5: Bayesian Statistical Analysis

```bash
# T023a: Load Bayesian data
# (Integrated into analysis)

# T024: Run Bayesian Hierarchical Model
python code/main.py --phase analyze

# T027a: Save analysis results
# (Integrated into analyze phase)
```

### Final Validation

```bash
# T055: Final artifact hashing
python code/final_hash_check.py

# T056: Documentation consistency check
# (Manual verification)
```

## Output Artifacts

The pipeline produces the following key artifacts:

- `data/subspace_ranks_merged.json`: Subspace ranks for merged adapter effects
- `data/results.csv`: Comprehensive results with similarity, LPIPS, and CESR scores
- `data/analysis_results.json`: Bayesian analysis results with posterior distributions
- `data/references/other_effect_refs.json`: Other effect reference embeddings
- `state/artifacts.yaml`: SHA-256 hashes of all artifacts

## Troubleshooting

### Common Issues

1. **Missing artifacts**: Ensure all previous phases have completed successfully.
2. **Memory errors**: The pipeline includes handling for OOM errors; quantization levels may be skipped.
3. **Model download failures**: Check network connectivity and HuggingFace credentials.

### Running on CPU-only runners

The pipeline is designed to work on CPU-only runners. Ensure you have sufficient memory (at least 16GB) for the baseline generation phase.

## Next Steps

After completing the pipeline, review the `data/analysis_results.json` file for the final statistical findings and correlation between subspace rank and concept bleeding.
