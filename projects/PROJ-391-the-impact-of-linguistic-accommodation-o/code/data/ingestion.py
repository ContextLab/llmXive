import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import yaml
from jsonschema import validate, ValidationError

# Import from sibling module
from utils import (
    get_pos_tags,
    get_syntactic_features,
    normalize_text,
    clean_text,
    is_valid_text,
    jaccard_similarity,
    tokenize_simple
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate the dataframe against the schema.
    This is a simplified validation check for the specific schema structure
    expected by T022.
    """
    required_fields = schema.get("properties", {}).keys()
    if not required_fields:
        # Fallback if schema structure is unexpected
        print("Warning: Could not extract required fields from schema.")
        return True

    missing_cols = [col for col in required_fields if col not in df.columns]
    if missing_cols:
        raise ValidationError(f"Missing required columns: {missing_cols}")

    # Check for nulls in metric columns as per task description
    metric_cols = ["lexical_overlap", "syntactic_similarity", "sentence_length_variance"]
    for col in metric_cols:
        if col in df.columns and df[col].isnull().any():
            raise ValidationError(f"Column '{col}' contains null values.")

    return True

def download_daily_dialog_test() -> str:
    """
    Download the DailyDialog test set using streaming to save memory.
    Returns the path to the saved parquet file.
    """
    from datasets import load_dataset

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DATA_DIR / "daily_dialog_test.parquet"

    if output_path.exists():
        print(f"Dataset already exists at {output_path}, skipping download.")
        return str(output_path)

    print("Downloading DailyDialog test set (streaming)...")
    try:
        dataset = load_dataset("daily_dialog", split="test", streaming=True)
        # Convert to list of dicts then to DataFrame to save as parquet
        # Streaming iterator
        data_list = []
        for item in dataset:
            data_list.append(item)
        
        df = pd.DataFrame(data_list)
        df.to_parquet(output_path, index=False)
        print(f"Saved dataset to {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        raise

def load_daily_dialog_test(parquet_path: Optional[str] = None) -> pd.DataFrame:
    """Load the DailyDialog test set from parquet."""
    if parquet_path is None:
        parquet_path = str(RAW_DATA_DIR / "daily_dialog_test.parquet")
    
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Dataset file not found: {parquet_path}")
    
    return pd.read_parquet(parquet_path)

def preprocess_dialogue_pair(turn_a: str, turn_b: str) -> Optional[Dict[str, Any]]:
    """
    Preprocess a pair of turns (Speaker A and Speaker B).
    Applies normalization and cleaning.
    Returns None if either turn is invalid after cleaning.
    """
    norm_a = normalize_text(turn_a)
    norm_b = normalize_text(turn_b)
    
    clean_a = clean_text(norm_a)
    clean_b = clean_text(norm_b)
    
    if not is_valid_text(clean_a) or not is_valid_text(clean_b):
        return None
    
    return {"turn_a": clean_a, "turn_b": clean_b}

def compute_accommodation_metrics(turn_a: str, turn_b: str, conversation_id: str) -> Dict[str, Any]:
    """
    Compute accommodation metrics for a dialogue pair.
    - lexical_overlap: Jaccard similarity on tokens
    - syntactic_similarity: Jaccard similarity on POS tag sets
    - sentence_length_variance: Variance of sentence lengths in the pair
    """
    # Tokenize
    tokens_a = tokenize_simple(turn_a)
    tokens_b = tokenize_simple(turn_b)
    
    # Lexical overlap (Jaccard)
    lexical_overlap = jaccard_similarity(set(tokens_a), set(tokens_b))
    
    # Syntactic similarity (POS tags)
    # Assuming get_pos_tags returns a list of tags
    pos_a = get_pos_tags(turn_a)
    pos_b = get_pos_tags(turn_b)
    syntactic_similarity = jaccard_similarity(set(pos_a), set(pos_b))
    
    # Sentence length variance
    # Simple split by punctuation for sentence detection
    import re
    sentences_a = re.split(r'[.!?]+', turn_a)
    sentences_b = re.split(r'[.!?]+', turn_b)
    
    # Filter empty strings
    sentences_a = [s.strip() for s in sentences_a if s.strip()]
    sentences_b = [s.strip() for s in sentences_b if s.strip()]
    
    all_sentences = sentences_a + sentences_b
    lengths = [len(s.split()) for s in all_sentences]
    
    sentence_length_variance = 0.0
    if len(lengths) > 1:
        sentence_length_variance = pd.Series(lengths).var()
    
    return {
        "conversation_id": conversation_id,
        "lexical_overlap": lexical_overlap,
        "syntactic_similarity": syntactic_similarity,
        "sentence_length_variance": sentence_length_variance,
        "turn_a_length": len(tokens_a),
        "turn_b_length": len(tokens_b)
    }

def main():
    """
    Main pipeline for data ingestion and metric computation.
    1. Downloads (if needed) and loads DailyDialog test set.
    2. Preprocesses pairs.
    3. Computes metrics.
    4. Saves to CSV.
    5. Validates output against schema.
    """
    print("Starting Data Ingestion Pipeline (T022)...")
    
    # Step 1: Download
    parquet_path = download_daily_dialog_test()
    
    # Step 2: Load
    df_raw = load_daily_dialog_test(parquet_path)
    print(f"Loaded {len(df_raw)} records.")
    
    # Expected columns in DailyDialog: 'dialogue' (list of turns), 'topic', 'emotion'
    # The task implies pairs. We will assume the 'dialogue' column contains a list of turns.
    # We need to pair Speaker A (even indices) and Speaker B (odd indices).
    # If the dataset structure is different, this logic adapts.
    # DailyDialog 'dialogue' is a list of strings.
    
    records = []
    skipped = 0
    
    for idx, row in df_raw.iterrows():
        dialogue = row.get('dialogue', [])
        conversation_id = row.get('topic', f"conv_{idx}") # Using topic as ID or generate one
        
        # Pair turns: (0,1), (2,3), etc.
        for i in range(0, len(dialogue) - 1, 2):
            turn_a = dialogue[i]
            turn_b = dialogue[i+1]
            
            processed = preprocess_dialogue_pair(turn_a, turn_b)
            if processed:
                metrics = compute_accommodation_metrics(
                    processed["turn_a"], 
                    processed["turn_b"], 
                    f"{conversation_id}_pair_{i//2}"
                )
                records.append(metrics)
            else:
                skipped += 1
    
    print(f"Processed {len(records)} valid pairs. Skipped {skipped} invalid pairs.")
    
    if not records:
        raise ValueError("No valid records processed. Check data source.")
    
    df_metrics = pd.DataFrame(records)
    
    # Ensure output directory exists
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DATA_DIR / "accommodation_metrics.csv"
    
    # Save to CSV
    df_metrics.to_csv(output_path, index=False)
    print(f"Saved metrics to {output_path}")
    
    # Step 5: Validate against schema (T022 requirement)
    print("Validating output against schema...")
    try:
        schema = load_schema(SCHEMA_PATH)
        validate_dataframe(df_metrics, schema)
        print("Validation PASSED: Output conforms to schema.")
    except FileNotFoundError:
        print(f"Warning: Schema file not found at {SCHEMA_PATH}. Skipping validation.")
    except ValidationError as e:
        print(f"Validation FAILED: {e}")
        raise RuntimeError("Output validation failed against schema.")
    
    return output_path

if __name__ == "__main__":
    main()