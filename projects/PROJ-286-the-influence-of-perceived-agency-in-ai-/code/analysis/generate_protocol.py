import os
import sys
import yaml
from pathlib import Path

def load_yaml_file(file_path: Path) -> dict:
    """Load a YAML file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    defaults_path = project_root / "code" / "analysis" / "config_defaults.yaml"
    user_config_path = project_root / "code" / "analysis" / "config_user.yaml"
    protocol_path = project_root / "docs" / "protocol.md"

    # Ensure docs directory exists
    protocol_path.parent.mkdir(parents=True, exist_ok=True)

    # Load defaults
    try:
        defaults = load_yaml_file(defaults_path)
    except FileNotFoundError as e:
        print(f"Error: {e}. Please ensure config_defaults.yaml exists.", file=sys.stderr)
        sys.exit(1)

    # Load user overrides if they exist, otherwise use empty dict
    user_overrides = {}
    if user_config_path.exists():
        try:
            user_overrides = load_yaml_file(user_config_path)
        except Exception as e:
            print(f"Warning: Could not load user config {user_config_path}: {e}. Using defaults.", file=sys.stderr)

    # Determine effective sensitivity ranges (User overrides take precedence)
    # We merge manually to ensure we have the sweep ranges
    sensitivity_config = defaults.get("sensitivity_config", {})
    if user_overrides.get("sensitivity_config"):
        for key, value in user_overrides["sensitivity_config"].items():
            sensitivity_config[key] = value

    # Construct the protocol content
    protocol_content = f"""# Pre-Registered Analysis Plan

**Project**: The Influence of Perceived Agency in AI Interactions on Trust (PROJ-286)
**Reference**: FR-006, US-3
**Generated**: Pre-study protocol for sensitivity analysis and primary hypothesis testing.

## 1. Primary Hypotheses

1. **H1**: Perceived Agency scores will differ significantly across conditions (High, Low, Control).
2. **H2**: Trust scores will be significantly higher in the High Agency condition compared to Low and Control conditions.

## 2. Sensitivity Analysis Parameters

The following sensitivity sweep parameters are defined in `code/analysis/config_defaults.yaml` and can be overridden by users via `code/analysis/config_user.yaml` or CLI arguments (`--attention-thresholds`, `--adherence-cutoffs`).

### 2.1 Attention Thresholds
- **Description**: Minimum percentage of correct attention check answers required for inclusion.
- **Sweep Values**: {sensitivity_config.get('attention_thresholds', [70, 80, 90, 95])}
- **Logic**: Participants scoring below the threshold are excluded, and the primary analysis is re-run.

### 2.2 Adherence Cutoffs
- **Description**: Minimum percentage of AI recommendations followed.
- **Sweep Values**: {sensitivity_config.get('adherence_cutoffs', [70, 80, 90])}
- **Logic**: Participants with adherence below the cutoff are excluded.

### 2.3 Straight-lining Detection
- **Description**: Maximum allowed consecutive identical responses on Likert scales.
- **Sweep Values**: {sensitivity_config.get('straightlining_thresholds', [3, 4, 5])}
- **Logic**: Participants exceeding the threshold are excluded.

### 2.4 Trust Outlier Removal
- **Description**: Z-score threshold for removing extreme trust scores.
- **Sweep Values**: {sensitivity_config.get('outlier_z_thresholds', [2.5, 3.0, 3.5])}
- **Logic**: Participants with trust scores outside the Z-score range are excluded.

## 3. Primary Analysis Plan

1. **Manipulation Check**: One-way ANOVA on `Perceived_Agency_Score` by Condition.
   - **Halt Condition**: If p > 0.05, the manipulation is considered failed, and the pipeline stops.
2. **Primary Test**: One-way ANOVA on `Trust_Score` by Condition.
   - **Contrasts**: Planned directional contrasts (High vs. Low; High+Low vs. Control) will be executed unconditionally.
3. **Post-hoc**: Tukey HSD for all pairwise comparisons, executed unconditionally.
4. **Effect Sizes**: Cohen's d calculated for all pairwise comparisons.

## 4. Configuration Note

This protocol reflects the sensitivity ranges defined in `code/analysis/config_defaults.yaml`.
Users may override these ranges via `code/analysis/config_user.yaml` or CLI arguments.
The analysis script (`code/analysis/sensitivity.py`) will validate that the active configuration matches this protocol or is a valid user override.

## 5. Data Integrity

- Raw data is stored in `data/raw/`.
- Processed data is stored in `data/processed/`.
- No in-place modifications of raw data are permitted.
"""

    # Write the protocol file
    with open(protocol_path, 'w') as f:
        f.write(protocol_content)

    print(f"Protocol successfully generated at: {protocol_path}")

if __name__ == "__main__":
    main()