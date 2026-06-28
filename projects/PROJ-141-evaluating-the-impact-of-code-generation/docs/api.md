# API Documentation

This document provides API reference for the main modules in the project.

## Table of Contents

1. [Experiment Module](#experiment-module)
2. [Quality Assessment Module](#quality-assessment-module)
3. [Analysis Module](#analysis-module)
4. [Data Module](#data-module)
5. [Models Module](#models-module)

---

## Experiment Module

### code/experiment/app.py

Flask application for experiment interface.

**Endpoints:**

```python
GET / # Home page with experiment info
POST /consent # Submit informed consent
GET /problem/<problem_id> # Get problem details
POST /submit # Submit code solution
POST /condition # Switch condition (LLM/baseline)
GET /log # Get experiment log
POST /complete # Mark session complete
```

**Configuration:**
```python
from code.config.settings import get_settings
settings = get_settings()
```

### code/experiment/problem_loader.py

Loads problems from HumanEval and Codeforces datasets.

```python
from code.experiment.problem_loader import ProblemLoader

loader = ProblemLoader(
 humaneval_path=settings.humaneval_path,
 codeforces_path=settings.codeforces_path
)

# Load all problems
problems = loader.load_all()

# Verify load rate (FR-001: ≥95%)
load_rate = loader.verify_load_rate(sample_size=100)
```

**Methods:**
- `load_all() -> List[Problem]` - Load all problems
- `get_problem(problem_id: str) -> Problem` - Get specific problem
- `verify_load_rate(sample_size: int = 100) -> float` - Verify ≥95% load rate

### code/experiment/condition_manager.py

Manages condition switching between LLM-assisted and baseline.

```python
from code.experiment.condition_manager import ConditionManager

manager = ConditionManager(
 initial_condition="llm_assisted",
 llm_enabled=True
)

# Get current condition
condition = manager.get_current_condition()

# Switch condition
manager.switch_condition()
```

### code/experiment/randomization.py

Handles participant randomization and seed management (Constitution Principle I).

```python
from code.experiment.randomization import RandomizationManager

manager = RandomizationManager(
 participant_id="P001",
 seed=42
)

# Get condition assignment
assignment = manager.assign_condition()

# Get random seed for reproducibility
seed = manager.get_seed()
```

### code/experiment/counterbalance.py

Implements counterbalancing to mitigate carryover effects.

```python
from code.experiment.counterbalance import CounterbalanceStrategy

# Latin square strategy
strategy = CounterbalanceStrategy.latin_square(conditions=["llm", "baseline"])

# Random order swap
strategy = CounterbalanceStrategy.random_swap(conditions=["llm", "baseline"])
```

---

## Quality Assessment Module

### code/quality/metric_aggregator.py

Aggregates all quality metrics per submission.

```python
from code.quality.metric_aggregator import MetricAggregator

aggregator = MetricAggregator()

# Compute all metrics for a submission
metrics = aggregator.compute_all(
 submission_id="sub_001",
 code="def hello(): pass",
 language="python"
)

# Metrics include:
# - pass_rate
# - cyclomatic_complexity
# - test_coverage
# - static_warnings
```

### code/quality/pass_rate.py

Computes HumanEval pass rate.

```python
from code.quality.pass_rate import PassRateCalculator

calculator = PassRateCalculator()
pass_rate = calculator.compute(code, test_cases)
# Returns float with ≥0.01 precision
```

### code/quality/complexity.py

Computes cyclomatic complexity using radon.

```python
from code.quality.complexity import ComplexityCalculator

calculator = ComplexityCalculator()
complexity = calculator.compute(code)
# Returns integer ≥1
```

### code/quality/coverage.py

Measures test coverage via coverage.py.

```python
from code.quality.coverage import CoverageCalculator

calculator = CoverageCalculator()
coverage = calculator.compute(code, test_cases)
# Returns percentage 0-100%
```

### code/quality/static_analysis.py

Runs static analysis using pylint (Python) or checkstyle (Java).

```python
from code.quality.static_analysis import StaticAnalyzer

analyzer = StaticAnalyzer()
warnings = analyzer.analyze(code, language="python")
# Returns warning count
```

---

## Analysis Module

### code/analysis/data_loader.py

Loads paired participant data from CSV.

```python
from code.analysis.data_loader import DataLoader

loader = DataLoader()
data = loader.load_paired_data("data/experiment_results.csv")

# Returns DataFrame with paired (llm, baseline) values
```

### code/analysis/statistical_tests.py

Implements statistical tests for paired data.

```python
from code.analysis.statistical_tests import StatisticalTests

tests = StatisticalTests()

# Paired t-test
t_stat, p_value = tests.paired_ttest(
 group_a=data["llm_time"],
 group_b=data["baseline_time"]
)

# Wilcoxon signed-rank test
w_stat, p_value = tests.wilcoxon(
 group_a=data["llm_time"],
 group_b=data["baseline_time"]
)

# Cohen's d effect size with 95% CI
cohens_d, ci = tests.cohens_d(
 group_a=data["llm_time"],
 group_b=data["baseline_time"]
)
```

### code/analysis/correction.py

Implements multiple-comparison correction.

```python
from code.analysis.correction import CorrectionMethods

# Bonferroni correction
corrected = CorrectionMethods.bonferroni(p_values, alpha=0.05)

# Holm correction
corrected = CorrectionMethods.holm(p_values, alpha=0.05)

# Verify family-wise error rate ≤0.05 (SC-004)
verified = CorrectionMethods.verify_error_rate(corrected, alpha=0.05)
```

### code/analysis/sensitivity.py

Implements sensitivity analysis for time reduction thresholds.

```python
from code.analysis.sensitivity import SensitivityAnalyzer

analyzer = SensitivityAnalyzer()
results = analyzer.sweep(
 thresholds=[0.01, 0.05, 0.1],
 data=data
)
# Returns coefficient of variation for each threshold
```

### code/analysis/export.py

Exports results with trace IDs (Constitution Principle IV).

```python
from code.analysis.export import ResultsExporter

exporter = ResultsExporter()
exporter.export(
 results=analysis_results,
 output_path="data/analysis_results.csv"
)
# Each statistic includes trace_id = hash(data_row_id + code_block_file:line + timestamp)
```

---

## Data Module

### code/data/models.py

Base models/entities for database.

```python
from code.data.models import Participant, Session, Problem, Submission, Metric

participant = Participant(
 id="P001",
 experience_years=2,
 consent_given=True
)
```

### code/data/db_schema.py

SQLite database schema setup.

```python
from code.data.db_schema import DatabaseSchema

schema = DatabaseSchema()
schema.create_all() # Create tables
```

---

## Models Module

### code/models/starcoder_cpu.py

CPU-only StarCoder integration for Python code generation.

```python
from code.models.starcoder_cpu import StarCoderCPU

model = StarCoderCPU()
response = model.generate(prompt="def fibonacci(n):")
```

### code/models/jacotext_cpu.py

CPU-only JaCoText integration for Java code generation.

```python
from code.models.jacotext_cpu import JaCoTextCPU

model = JaCoTextCPU()
response = model.generate(prompt="public class Hello {")
```

### code/models/model_selector.py

Conditional model selection with fallback.

```python
from code.models.model_selector import ModelSelector

selector = ModelSelector(
 fallback_enabled=True,
 fallback_model="starcoder"
)

# Select model for language
model = selector.select_model(language="python")
```

---

## Configuration

### code/config/settings.py

Environment configuration management.

```python
from code.config.settings import get_settings

settings = get_settings()

# Access configuration
print(settings.humaneval_path)
print(settings.encryption_key)
print(settings.model_fallback_enabled)
```

---

## Error Handling

All modules implement proper error handling:

```python
try:
 result = some_function()
except TimeoutExpired:
 # Handle timeout (T033)
 logger.error(f"Timeout: {submission_id}")
except SyntaxError:
 # Handle syntax errors (T034)
 return 400, "Syntax error in submission"
except Exception as e:
 # Log and handle unexpected errors
 logger.exception("Unexpected error")
 raise
```

---

## Changelog

- **v0.1.0**: Initial API (T048)
- **v0.2.0**: Added quality assessment endpoints (T028-T032)
- **v0.3.0**: Added statistical analysis (T038-T045)
