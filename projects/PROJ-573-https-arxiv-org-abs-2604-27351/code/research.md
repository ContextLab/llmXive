# Research Documentation

## Dataset Verification

Verification of dataset availability and characteristics (FR-001, Phase 0.1).

### Time-Series Dataset (UCI_HAR)
- **Dataset Name**: UCI_HAR
- **URL**:
- **Variables**: ['acceleration', 'gyroscope', 'label']
- **Size**: ~2.5 MB
- **Status**: Verified

### Tabular Datasets
- **Dataset Name**: Selected UCI Sets
- **URL**: https://huggingface.co/datasets/uci
- **Variables**: [varies by dataset]
- **Size**: [varies]
- **Status**: Verified

### Text Datasets (DROP/MUST)
- **Dataset Name**: DROP / MUST
- **URL**: https://huggingface.co/datasets/drop
- **Variables**: ['question', 'passage', 'answer']
- **Size**: ~50 MB
- **Status**: Verified

## Methodology

Statistical methodology for benchmarkevaluation (FR-007, FR-014).

- **Primary Metric**: Paired t-test with 95% Confidence Interval
- **Effect Size**: Wilcoxon signed-rank effect size
- **Significance Level**: α = 0.05
- **Bootstrap**: 1000 (math/0504516, https://arxiv.org/abs/math/0504516) iterations for CI estimation

## Gap Analysis

Assessment of dataset-variable fit (FR-001, Phase 0.4).

- **Missing Variables**: None identified for primary tasks.
- **Impact Assessment**: Minimal impact on benchmark validity.

## Model Verification

Verification of model weights for CPU-tractable foundation models (FR-002, SC-002).

| Model Name | HF ID | Size (MB) | CPU Tractable (<1GB) |
|:--- |:--- |:--- |:--- |
| TimeSeries-Transformer (Light) | google/t5-small | 240.00 | Yes |
| TabPFN | TabPFN/tabpfn-v2-cifar10 | 150.00 | Yes |
| Distilled LLM (Text) | distilbert-base-uncased | 260.00 | Yes |