import pathlib
import pandas as pd
import yaml

from download_data import validate_columns, load_schema_required_fields, load_schema_all_fields

def test_load_schema_required_fields():
    schema_path = pathlib.Path(__file__).parents[2] / "specs" / "001-evaluating-the-impact-of-code-generation" / "contracts" / "raw_prs.schema.yaml"
    required = load_schema_required_fields(schema_path)
    assert "pr_id" in required
    assert "first_comment_timestamp" in required

def test_validate_columns_all_present():
    # Load a real primary dataset (downloaded by the script)
    data_path = pathlib.Path(__file__).parents[2] / "data" / "raw" / "prs-v2-sample.parquet"
    df = pd.read_parquet(data_path, engine="pyarrow")
    schema_path = pathlib.Path(__file__).parents[2] / "specs" / "001-evaluating-the-impact-of-code-generation" / "contracts" / "raw_prs.schema.yaml"
    all_fields = load_schema_all_fields(schema_path)
    status = validate_columns(df, all_fields)
    # Every field defined in the schema should be either present or missing (no errors)
    assert set(status.keys()) == set(all_fields)
    # At least the mandatory fields must be present
    for fld in ["pr_id", "repo_name", "created_at", "merged_at", "additions", "deletions", "comment_count", "commit_message", "first_comment_timestamp"]:
        assert status[fld] == "present"