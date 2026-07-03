# Data Model: Assessing the Impact of Data Augmentation on Statistical Power in Small Samples

## Entities

### Dataset Configuration
- **Attributes**: `dataset_id` (str), `target_size` (int), `ground_truth_type` (str: "null" | "alternative"), `augmentation_type` (str)
- **Description**: Tuple defining a unique simulation configuration. Includes ground truth type to distinguish Type I vs Type II runs.

### Simulation Run
- **Attributes**: `iteration_id` (int), `p_value` (float), `error_type` (str), `config` (Dataset Configuration)
- **Description**: Single Monte Carlo iteration result.

### Error Rate Profile
- **Attributes**: `config` (Dataset Configuration), `type1_error_rate` (float), `type2_error_rate` (float), `ci_lower` (float), `ci_upper` (float), `safety_threshold` (float)
- **Description**: Aggregated error rates for a configuration. Includes the safety threshold for flagging.

## Data Flow

1. **Input**: Raw datasets (CSV) from verified URLs.
2. **Subsample**: Stratified reduction to N=15, 25, 40.
3. **Ground Truth Generation**: 
   - If `ground_truth_type` == "null": Permute labels.
   - If `ground_truth_type` == "alternative": Apply mean shift (Cohen's d=0.5).
4. **Augment**: Apply Gaussian noise, SMOTE, Random Oversampling, or None (Baseline).
5. **Simulate**: Run multiple t-tests; collect p-values.
6. **Aggregate**: Compute error rates and CIs.
7. **Output**: JSON files per configuration.

## Storage Schema

- **Raw Data**: `data/raw/[dataset_name].csv` (checksummed)
- **Derived Data**: `data/derived/[dataset]_[size]_[ground_truth]_[method].csv` (with metadata)
- **Results**: `results/[dataset]_[size]_[ground_truth]_[method].json` (error rates, CIs, disclaimer, safety_threshold)