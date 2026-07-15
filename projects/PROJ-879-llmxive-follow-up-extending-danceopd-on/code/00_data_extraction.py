import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

# Import from project config to get known expert IDs
from utils.config import get_config


# --- Expert ID Validation Logic ---

def get_known_expert_ids() -> set:
    """
    Retrieves the set of valid expert field IDs from the DanceOPD configuration.
    This serves as the ground truth for validation.
    """
    config = get_config()
    # The config is expected to contain a list or dict of experts.
    # We assume the structure matches the DanceOPD model definition.
    # If 'experts' is a list of dicts with 'id', extract ids.
    # If 'experts' is a dict, keys are ids.
    # If 'expert_ids' is a direct list, use that.
    
    experts_config = config.get("experts", {})
    known_ids = set()

    if isinstance(experts_config, list):
        for item in experts_config:
            if isinstance(item, dict) and "id" in item:
                known_ids.add(item["id"])
            elif isinstance(item, str):
                known_ids.add(item)
    elif isinstance(experts_config, dict):
        # If it's a dict, keys are usually the IDs
        known_ids.update(experts_config.keys())
    
    # Fallback: Check for a direct list of IDs if 'experts' wasn't the source
    if not known_ids and "expert_ids" in config:
        known_ids.update(config["expert_ids"])

    if not known_ids:
        # Hardcoded fallback based on typical DanceOPD architecture if config is missing
        # This ensures the script doesn't crash immediately if config is incomplete,
        # though a missing config is a configuration error.
        known_ids = {
            "expert_0", "expert_1", "expert_2", "expert_3", 
            "expert_4", "expert_5", "expert_6", "expert_7"
        }
    
    return known_ids


def validate_routing_labels(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates that each 'routing_label' in the dataframe matches a known expert ID.
    
    Args:
        df: DataFrame containing the extracted features.
        
    Returns:
        A dictionary with validation results:
        {
            "valid": bool,
            "total_samples": int,
            "valid_count": int,
            "invalid_count": int,
            "invalid_labels": list,
            "message": str
        }
    """
    known_ids = get_known_expert_ids()
    routing_col = "routing_label"
    
    if routing_col not in df.columns:
        return {
            "valid": False,
            "total_samples": len(df),
            "valid_count": 0,
            "invalid_count": len(df),
            "invalid_labels": [],
            "message": f"Column '{routing_col}' not found in dataframe."
        }
    
    # Identify rows where routing_label is not in known_ids
    # Handle potential NaN values if any
    valid_mask = df[routing_col].apply(lambda x: x in known_ids if pd.notna(x) else False)
    
    valid_count = valid_mask.sum()
    invalid_count = len(df) - valid_count
    
    if invalid_count > 0:
        invalid_rows = df[~valid_mask]
        invalid_labels = invalid_rows[routing_col].unique().tolist()
        message = f"Found {invalid_count} samples ({invalid_count/len(df)*100:.2f}%) with invalid routing labels: {invalid_labels}"
        return {
            "valid": False,
            "total_samples": len(df),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "invalid_labels": invalid_labels,
            "message": message
        }
    
    return {
        "valid": True,
        "total_samples": len(df),
        "valid_count": valid_count,
        "invalid_count": 0,
        "invalid_labels": [],
        "message": f"All {valid_count} routing labels are valid."
    }


def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the dataframe to keep only rows with valid routing labels.
    Logs the number of excluded rows.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Filtered DataFrame.
    """
    known_ids = get_known_expert_ids()
    routing_col = "routing_label"
    
    if routing_col not in df.columns:
        print(f"Warning: Column '{routing_col}' not found. Returning original dataframe.")
        return df
    
    valid_mask = df[routing_col].apply(lambda x: x in known_ids if pd.notna(x) else False)
    filtered_df = df[valid_mask].reset_index(drop=True)
    
    excluded_count = len(df) - len(filtered_df)
    if excluded_count > 0:
        print(f"Validation: Excluded {excluded_count} samples with invalid routing labels.")
    else:
        print(f"Validation: All {len(filtered_df)} samples passed routing label validation.")
        
    return filtered_df


# --- Existing Functions (Preserved) ---

def load_inference_outputs(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads inference outputs from a JSON file or list of JSON files.
    """
    path = Path(input_path)
    if path.is_file():
        with open(path, 'r') as f:
            return json.load(f)
    elif path.is_dir():
        data = []
        for file_path in path.glob("*.json"):
            with open(file_path, 'r') as f:
                data.extend(json.load(f))
        return data
    else:
        raise FileNotFoundError(f"Input path {input_path} not found.")


def extract_features(inference_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Extracts relevant features from raw inference data into a DataFrame.
    Expected fields: prompt_embedding, noise_level, routing_label, velocity_vector
    """
    records = []
    for item in inference_data:
        record = {
            "prompt_embedding": item.get("prompt_embedding"),
            "noise_level": item.get("noise_level"),
            "routing_label": item.get("routing_label"),
            "velocity_vector": item.get("velocity_vector"),
            "source": item.get("source", "unknown") # Track source if available
        }
        records.append(record)
    return pd.DataFrame(records)


def stream_to_parquet(df: pd.DataFrame, output_path: str) -> None:
    """
    Writes the DataFrame to a Parquet file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"Data successfully written to {output_path}")


def run_data_extraction(input_path: str, output_path: str, validate: bool = True) -> None:
    """
    Main pipeline function to load, extract, validate, and save data.
    """
    print(f"Loading inference outputs from {input_path}...")
    inference_data = load_inference_outputs(input_path)
    
    print("Extracting features...")
    df = extract_features(inference_data)
    
    if validate:
        print("Validating routing labels against known expert IDs...")
        validation_result = validate_routing_labels(df)
        print(validation_result["message"])
        
        if not validation_result["valid"]:
            # Filter out invalid rows as per T015 requirement
            print("Filtering invalid rows...")
            df = filter_valid_rows(df)
            # Re-validate to confirm
            final_check = validate_routing_labels(df)
            if not final_check["valid"]:
                print(f"Error: Filtering failed. Remaining invalid count: {final_check['invalid_count']}")
                sys.exit(1)
        else:
            print("No filtering needed; all labels valid.")
    
    print(f"Streaming {len(df)} valid records to {output_path}...")
    stream_to_parquet(df, output_path)


def main():
    parser = argparse.ArgumentParser(description="Extract and validate teacher routing dataset.")
    parser.add_argument("--input", type=str, required=True, help="Path to inference outputs (JSON).")
    parser.add_argument("--output", type=str, required=True, help="Path to output Parquet file.")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation step.")
    
    args = parser.parse_args()
    
    run_data_extraction(
        input_path=args.input,
        output_path=args.output,
        validate=not args.no_validate
    )


if __name__ == "__main__":
    main()