# API Documentation

This document details the public API surface for the llmXive pipeline.

## Core Entities

### `TrainingSample`
Located in `src/models/entities.py`.

```python
@dataclass
class TrainingSample:
 input_id: str
 gradient_norms: float
 local_curvature: float
 quantized_logits: List[float]
 calculated_kl_divergence: float
 quantization_level: str
```

### `GapPredictionResult`
Located in `src/models/entities.py`.

```python
@dataclass
class GapPredictionResult:
 predicted_gap: float
 actual_gap: float
 error: float
```

## Services

### `FeatureExtractor` (`src/services/feature_extractor.py`)

- `extract_features_for_sample(sample: dict, model, tokenizer) -> FeatureResult`
 Extracts gradient norms and local curvature for a single sample.
- `load_dataset_streaming(dataset_id: str, split: str = "train") -> Iterable[dict]`
 Loads dataset in streaming mode to prevent OOM.
- `run_feature_extraction(batch: List[dict]) -> List[FeatureResult]`

### `QuantizedInference` (`src/services/quantized_inference.py`)

- `load_quantized_model(model_path: str, n_bits: int) -> llama_cpp.Llama`
 Loads a quantized model using llama-cpp-python.
- `run_quantized_inference(model, prompt: str) -> InferenceResult`
 Runs inference and returns logits.
- `process_sample(sample: dict, model, quantization_level: str) -> Optional[InferenceResult]`
 Handles errors gracefully; returns None on failure.

### `GapCalculator` (`src/services/gap_calculator.py`)

- `compute_kl_divergence(logits_fp: torch.Tensor, logits_q: torch.Tensor, epsilon: float = 1e-8) -> float`
 Computes KL divergence between full-precision and quantized logits.
- `calculate_gap(sample: TrainingSample) -> float`

### `VIFChecker` (`src/services/vif_checker.py`)

- `calculate_vif_for_feature(df: pd.DataFrame, feature: str) -> float`
- `run_vif_diagnostic(df: pd.DataFrame) -> Dict[str, float]`

### `StatisticalTester` (`src/services/statistical_tester.py`)

- `perform_paired_ttest(group_a: List[float], group_b: List[float]) -> TTestResult`
 Performs a paired t-test with Bonferroni correction.

### `LatencyMeter` (`src/services/latency_meter.py`)

- `measure_proxy_policy_evaluation_time(model, inputs: List[dict]) -> float`
- `measure_baseline_policy_evaluation_time(model, inputs: List[dict]) -> float`
- `calculate_latency_reduction(proxy_time: float, baseline_time: float) -> float`

## CLI Entry Points

All CLI scripts are located in `code/src/cli/`.

- `generate_dataset.py`: Orchestrates the full data generation pipeline.
- `validate_features_diagnostic.py`: Runs VIF checks on generated data.
- `prepare_data_split.py`: Stratifies and splits the dataset.
- `train_predictor.py`: Trains the Kernel Ridge Regression model.
- `evaluate_on_test.py`: Evaluates the predictor on the test set.
- `synchronize_inputs.py`: Generates fixed seed inputs for reproducible comparison.
- `run_baseline_sync.py`: Runs the baseline hardware-sync loop.
- `run_proxy_loop.py`: Runs the proxy policy loop.
- `verify_bound_consistency.py`: Verifies theoretical bounds per quantization level.
- `aggregate_bound_results.py`: Aggregates consistency reports.
- `run_latency_analysis.py`: Measures and reports latency reduction.
