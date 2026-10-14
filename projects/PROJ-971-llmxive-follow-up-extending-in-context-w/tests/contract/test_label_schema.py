import pandas as pd
import yaml
from pathlib import Path
from llmxive_toolkit import paths

def test_labels_schema():
    """Validate that ``data/labels.csv`` conforms to ``label.schema.yaml``."""
    schema_path = Path(__file__).parents[2] / "specs" / "001-auto-icwm-latent-dynamics" / "contracts" / "label.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    csv_path = paths.data("labels.csv")
    df = pd.read_csv(csv_path)

    # Basic column existence
    assert set(df.columns) == {"clip_id", "tau", "k", "success_rate"}

    # Validate each row against the JSON schema
    from jsonschema import validate, ValidationError

    for _, row in df.iterrows():
        try:
            validate(instance=row.to_dict(), schema=schema)
        except ValidationError as e:
            raise AssertionError(f"Row validation failed: {e.message}")