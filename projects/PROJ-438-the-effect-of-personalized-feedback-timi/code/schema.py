import os
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import logging utilities to ensure consistent audit trails
from logging_config import get_logger, info, error, warning, debug

logger = get_logger(__name__)


def load_schema_from_file(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema definition from a file.

    Args:
        schema_path: Path to the YAML schema file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML is malformed.
    """
    path = Path(schema_path)
    if not path.exists():
        error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(path, 'r', encoding='utf-8') as f:
        try:
            schema = yaml.safe_load(f)
            info(f"Successfully loaded schema from {schema_path}")
            return schema
        except yaml.YAMLError as e:
            error(f"Error parsing YAML schema: {e}")
            raise


def validate_column_presence(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that all required columns are present in the DataFrame.

    Args:
        df: The DataFrame to validate.
        required_columns: List of column names that must be present.

    Returns:
        Tuple of (is_valid, list_of_missing_columns).
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        error(f"Missing required columns: {missing}")
        return False, missing
    info(f"All required columns present: {required_columns}")
    return True, []


def validate_column_types(df: pd.DataFrame, type_map: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate that columns match expected types.

    Supported type strings: 'integer', 'float', 'string', 'boolean', 'datetime'

    Args:
        df: The DataFrame to validate.
        type_map: Dictionary mapping column names to expected type strings.

    Returns:
        Tuple of (is_valid, list_of_type_errors).
    """
    errors = []
    for col, expected_type in type_map.items():
        if col not in df.columns:
            continue  # Handled by presence check

        series = df[col]
        valid = True

        if expected_type == 'integer':
            # Check if all non-null values are integers or can be safely cast
            if not pd.api.types.is_integer_dtype(series):
                # Allow float if it has no fractional part
                if pd.api.types.is_float_dtype(series):
                    if not series.dropna().apply(lambda x: x.is_integer() if isinstance(x, float) else True).all():
                        valid = False
                else:
                    valid = False

        elif expected_type == 'float':
            if not (pd.api.types.is_float_dtype(series) or pd.api.types.is_integer_dtype(series)):
                valid = False

        elif expected_type == 'string':
            if not pd.api.types.is_string_dtype(series) and not pd.api.types.is_object_dtype(series):
                valid = False

        elif expected_type == 'boolean':
            if not pd.api.types.is_bool_dtype(series):
                # Check if it's object dtype but contains only True/False/1/0
                if series.dtype == 'object':
                    unique_vals = series.dropna().unique()
                    allowed = {True, False, 1, 0, 'True', 'False', '1', '0'}
                    if not all(v in allowed for v in unique_vals):
                        valid = False
                else:
                    valid = False

        elif expected_type == 'datetime':
            if not pd.api.types.is_datetime64_any_dtype(series):
                # Try to parse to see if it's a valid date string
                try:
                    pd.to_datetime(series, errors='raise')
                except (ValueError, TypeError):
                    valid = False

        if not valid:
            errors.append(f"Column '{col}' is not {expected_type} (actual: {series.dtype})")

    if errors:
        error(f"Type validation errors: {errors}")
        return False, errors

    info("Column type validation passed")
    return True, []


def validate_null_values(df: pd.DataFrame, nullable_map: Dict[str, bool]) -> Tuple[bool, List[str]]:
    """
    Validate nullability constraints.

    Args:
        df: The DataFrame to validate.
        nullable_map: Dictionary mapping column names to True (nullable) or False (required).

    Returns:
        Tuple of (is_valid, list_of_null_errors).
    """
    errors = []
    for col, is_nullable in nullable_map.items():
        if col not in df.columns:
            continue

        if not is_nullable:
            null_count = df[col].isna().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} non-nullable null values")

    if errors:
        error(f"Null constraint violations: {errors}")
        return False, errors

    info("Null constraint validation passed")
    return True, []


def validate_value_ranges(
    df: pd.DataFrame,
    range_map: Dict[str, Tuple[Optional[float], Optional[float]]]
) -> Tuple[bool, List[str]]:
    """
    Validate that numeric columns fall within specified ranges.

    Args:
        df: The DataFrame to validate.
        range_map: Dictionary mapping column names to (min, max) tuples.
                   Use None for unbounded sides.

    Returns:
        Tuple of (is_valid, list_of_range_errors).
    """
    errors = []
    for col, (min_val, max_val) in range_map.items():
        if col not in df.columns:
            continue

        series = df[col]
        if not (pd.api.types.is_float_dtype(series) or pd.api.types.is_integer_dtype(series)):
            continue

        out_of_range = []

        if min_val is not None:
            below = series[series < min_val].count()
            if below > 0:
                out_of_range.append(f"< {min_val} ({below} rows)")

        if max_val is not None:
            above = series[series > max_val].count()
            if above > 0:
                out_of_range.append(f"> {max_val} ({above} rows)")

        if out_of_range:
            errors.append(f"Column '{col}' out of range: {out_of_range}")

    if errors:
        error(f"Range validation errors: {errors}")
        return False, errors

    info("Range validation passed")
    return True, []


def validate_categorical_values(
    df: pd.DataFrame,
    categorical_map: Dict[str, List[Any]]
) -> Tuple[bool, List[str]]:
    """
    Validate that categorical columns only contain allowed values.

    Args:
        df: The DataFrame to validate.
        categorical_map: Dictionary mapping column names to list of allowed values.

    Returns:
        Tuple of (is_valid, list_of_categorical_errors).
    """
    errors = []
    for col, allowed_values in categorical_map.items():
        if col not in df.columns:
            continue

        series = df[col]
        unique_vals = set(series.dropna().unique())
        allowed_set = set(allowed_values)

        invalid = unique_vals - allowed_set
        if invalid:
            errors.append(f"Column '{col}' has invalid values: {invalid}")

    if errors:
        error(f"Categorical validation errors: {errors}")
        return False, errors

    info("Categorical validation passed")
    return True, []


def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Run a full schema validation against a DataFrame.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary (loaded from YAML).

    Returns:
        Tuple of (is_valid, list_of_all_errors).
    """
    all_errors = []
    is_valid = True

    # 1. Column Presence
    required_columns = schema.get('required_columns', [])
    valid, missing = validate_column_presence(df, required_columns)
    if not valid:
        is_valid = False
        all_errors.extend(missing)

    # 2. Column Types
    type_map = schema.get('column_types', {})
    valid, type_errors = validate_column_types(df, type_map)
    if not valid:
        is_valid = False
        all_errors.extend(type_errors)

    # 3. Null Constraints
    nullable_map = schema.get('nullable', {})
    valid, null_errors = validate_null_values(df, nullable_map)
    if not valid:
        is_valid = False
        all_errors.extend(null_errors)

    # 4. Value Ranges
    range_map = schema.get('value_ranges', {})
    valid, range_errors = validate_value_ranges(df, range_map)
    if not valid:
        is_valid = False
        all_errors.extend(range_errors)

    # 5. Categorical Values
    categorical_map = schema.get('categorical_values', {})
    valid, cat_errors = validate_categorical_values(df, categorical_map)
    if not valid:
        is_valid = False
        all_errors.extend(cat_errors)

    if is_valid:
        info("Full schema validation PASSED")
    else:
        error(f"Full schema validation FAILED with {len(all_errors)} errors")

    return is_valid, all_errors


def assert_valid_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    """
    Assert that the DataFrame matches the schema, raising an exception if not.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.

    Raises:
        ValueError: If validation fails.
    """
    is_valid, errors = validate_schema(df, schema)
    if not is_valid:
        raise ValueError(f"Schema validation failed:\n" + "\n".join(errors))


def filter_valid_records(
    df: pd.DataFrame,
    schema: Dict[str, Any],
    strict: bool = True
) -> pd.DataFrame:
    """
    Filter a DataFrame to keep only records that pass all schema checks.

    If strict=True, drop rows with ANY invalid value.
    If strict=False, only drop rows where required fields are missing or null.

    Args:
        df: Input DataFrame.
        schema: Schema dictionary.
        strict: If True, drop rows with any type/range/categorical violation.

    Returns:
        Filtered DataFrame.
    """
    mask = pd.Series(True, index=df.index)

    # 1. Required columns must not be null
    required = schema.get('required_columns', [])
    nullable_map = schema.get('nullable', {})
    for col in required:
        if col in df.columns:
            # If it's in required, it's implicitly non-nullable unless overridden
            is_nullable = nullable_map.get(col, False)
            if not is_nullable:
                mask &= df[col].notna()

    if strict:
        # 2. Type checks
        type_map = schema.get('column_types', {})
        for col, expected_type in type_map.items():
            if col not in df.columns:
                continue
            series = df[col]

            if expected_type == 'boolean' and not pd.api.types.is_bool_dtype(series):
                if series.dtype == 'object':
                    allowed = {True, False, 1, 0, 'True', 'False', '1', '0'}
                    mask &= series.isin(allowed)
                else:
                    mask &= pd.Series(False, index=df.index) # Drop all if type is wrong and not object

            elif expected_type == 'integer' and not pd.api.types.is_integer_dtype(series):
                if pd.api.types.is_float_dtype(series):
                    mask &= series.dropna().apply(lambda x: x.is_integer() if isinstance(x, float) else True)
                else:
                    mask &= pd.Series(False, index=df.index)

        # 3. Range checks
        range_map = schema.get('value_ranges', {})
        for col, (min_val, max_val) in range_map.items():
            if col not in df.columns:
                continue
            series = df[col]
            if not (pd.api.types.is_float_dtype(series) or pd.api.types.is_integer_dtype(series)):
                continue

            if min_val is not None:
                mask &= (series >= min_val)
            if max_val is not None:
                mask &= (series <= max_val)

        # 4. Categorical checks
        categorical_map = schema.get('categorical_values', {})
        for col, allowed in categorical_map.items():
            if col not in df.columns:
                continue
            mask &= df[col].isin(allowed)

    return df[mask].reset_index(drop=True)


def load_schema_and_validate(
    df: pd.DataFrame,
    schema_path: str,
    raise_on_error: bool = True
) -> Tuple[pd.DataFrame, bool, List[str]]:
    """
    Convenience function to load a schema from file and validate a DataFrame.

    Args:
        df: DataFrame to validate.
        schema_path: Path to the YAML schema file.
        raise_on_error: If True, raise ValueError on validation failure.

    Returns:
        Tuple of (filtered_df, is_valid, list_of_errors).
    """
    schema = load_schema_from_file(schema_path)
    is_valid, errors = validate_schema(df, schema)

    if not is_valid:
        if raise_on_error:
            raise ValueError(f"Schema validation failed:\n" + "\n".join(errors))
        else:
            warning(f"Schema validation failed. Returning unfiltered data.")
            return df, False, errors

    return df, True, []