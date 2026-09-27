# llmXive Code Examples

This document provides practical examples of how to use the llmXive API modules.

## 1. Running the Full Pipeline

To run the entire data pipeline from scratch:

```python
import os
import sys

# Ensure code/ is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.fetch_github import main as fetch_main
from data.classify_prs import main as classify_main
from data.save_labeled_dataset import main as save_labeled_main
from analysis.complexity import main as complexity_main
from analysis.save_complexity_scores import main as save_complexity_main
from data.extract_metrics import main as extract_metrics_main
from analysis.statistical_tests import main as stats_main
from analysis.generate_results_report import main as results_main
from audit.manual_validation import main as audit_main
from analysis.generate_final_report import main as final_report_main
from analysis.visualizations import main as viz_main
from analysis.generate_final_report_pdf import main as pdf_main

if __name__ == "__main__":
 print("1. Fetching GitHub PRs...")
 fetch_main()
 print("2. Classifying PRs...")
 classify_main()
 print("3. Saving labeled dataset...")
 save_labeled_main()
 print("4. Running Manual Validation (Audit)...")
 audit_main()
 print("5. Computing Complexity...")
 complexity_main()
 print("6. Saving Complexity Scores...")
 save_complexity_main()
 print("7. Extracting Metrics...")
 extract_metrics_main()
 print("8. Running Statistical Tests...")
 stats_main()
 print("9. Generating Results Report...")
 results_main()
 print("10. Generating Visualizations...")
 viz_main()
 print("11. Generating Final Report (Text)...")
 final_report_main()
 print("12. Generating Final Report (PDF)...")
 pdf_main()
 print("Pipeline complete.")
```

## 2. Manual Data Loading and Processing

If you need to manually process data step-by-step:

```python
from data.classify_prs import load_prs_from_raw, classify_prs, save_classified_prs
from utils.config import get_path

# Load raw data
raw_dir = get_path("raw_data")
prs = load_prs_from_raw(raw_dir)

# Classify
classified = classify_prs(prs)

# Save
output_path = get_path("classified_prs")
save_classified_prs(classified, output_path)
```

## 3. Running Statistical Tests on Custom Data

```python
from analysis.statistical_tests import load_metrics_data, run_statistical_tests

# Load your metrics CSV
metrics = load_metrics_data("data/processed/prs_metrics.csv")

# Run tests
results = run_statistical_tests(metrics)

# Inspect results
print(f"Comment Density P-value: {results['comment_density']['p_value']}")
print(f"Time to Merge P-value: {results['time_to_merge']['p_value']}")
```

## 4. Using the Seed Manager for Reproducibility

```python
from utils.seeds import set_global_seed, sample_with_seed

# Set global seed
set_global_seed(12345)

# Sample data reproducibly
data = list(range(1000))
sample = sample_with_seed(data, n=10, seed=12345)
print(sample)
```

## 5. Logging with PII Filtering

```python
from utils.logging import get_logger, setup_logging

# Setup logging
logger = setup_logging("my_analysis_script")

# Log with PII
logger.info("Processing user email: user@example.com")
# Output will mask the email
```

## 6. Batch Processing with Memory Monitoring

```python
from utils.batch_processor import process_in_batches, memory_monitor

def my_processor(item):
 return item * 2

data = list(range(10000))

# Process in batches with memory monitoring
with memory_monitor():
 results = process_in_batches(data, batch_size=100, processor=my_processor)
```

## 7. Calculating Complexity Scores

```python
from analysis.complexity import calculate_cyclomatic_complexity, calculate_loc

code_snippet = """
def example():
 if x > 0:
 return True
 else:
 return False
"""

cc = calculate_cyclomatic_complexity(code_snippet)
loc = calculate_loc(code_snippet)

print(f"Cyclomatic Complexity: {cc}")
print(f"Lines of Code: {loc}")
```

## 8. Generating Visualizations

```python
from analysis.visualizations import load_metrics_for_viz, generate_boxplots

# Load metrics
metrics = load_metrics_for_viz("data/processed/prs_metrics.csv")

# Generate boxplots
generate_boxplots(metrics, "reports/figures/boxplots.pdf")
```

## 9. Audit and Error Rate Calculation

```python
from audit.manual_validation import load_labeled_prs, calculate_sample_size, calculate_error_rate

# Load labeled data
prs = load_labeled_prs("data/processed/prs_labeled.csv")

# Calculate sample size
sample_size = calculate_sample_size(total_n=len(prs), min_threshold=30)

# (In real usage, you would select and execute human judgment here)
# For this example, assume we have manual results
manual_results = [...] # List of dicts with manual judgments
automated_labels = [p['source_type'] for p in prs]

# Calculate error rate
error_rate = calculate_error_rate(manual_results, automated_labels)
print(f"Error Rate: {error_rate:.4f}")
```

## 10. Saving Complexity Scores to CSV

```python
from analysis.save_complexity_scores import save_complexity_scores

# Assume scores is a list of dicts with pr_id and complexity_score
scores = [
 {"pr_id": 1, "complexity_score": 1.5},
 {"pr_id": 2, "complexity_score": 2.0}
]

save_complexity_scores(scores, "data/processed/complexity_scores.csv")
```
