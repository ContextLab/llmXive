import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import yaml
from jsonschema import validate, ValidationError
from datasets import load_dataset

# Ensure imports from sibling modules work if run as a script or module
try:
    from utils import normalize_text, clean_text, is_valid_text, jaccard_similarity, tokenize_simple, get_pos_tags
except ImportError:
    # Fallback for direct execution context if PYTHONPATH is not set
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils import normalize_text, clean_text, is_valid_text, jaccard_similarity, tokenize_simple, get_pos_tags

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from a YAML or JSON file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate a DataFrame against a JSON schema.
    Converts the first row to a dict for validation as a representative sample.
    In a real pipeline, one might validate all rows or use a library like pandera.
    """
    if df.empty:
        logger.warning("DataFrame is empty, skipping validation.")
        return True

    # Convert first row to dict for schema validation
    sample_row = df.iloc[0].to_dict()
    
    try:
        validate(instance=sample_row, schema=schema)
        logger.info("Schema validation passed for sample row.")
        return True
    except ValidationError as e:
        logger.error(f"Schema validation failed: {e.message}")
        logger.error(f"Failed instance keys: {list(e.instance.keys())}")
        logger.error(f"Expected schema properties: {list(schema.get('properties', {}).keys())}")
        return False

def download_daily_dialog_test(output_dir: str) -> str:
    """
    Download the DailyDialog test split using streaming to save memory.
    Returns the path to the saved parquet file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / "daily_dialog_test.parquet"

    if file_path.exists():
        logger.info(f"Dataset already exists at {file_path}")
        return str(file_path)

    logger.info("Downloading DailyDialog test split (streaming)...")
    try:
        dataset = load_dataset("daily_dialog", split="test", streaming=True)
        # Convert to pandas and save as parquet to cache locally
        # Since streaming returns an iterator, we collect it.
        # For a full dataset, this might be memory intensive if not chunked,
        # but for the test split it is usually manageable.
        df = dataset.to_pandas()
        df.to_parquet(file_path, index=False)
        logger.info(f"Saved dataset to {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def load_daily_dialog_test(file_path: str) -> pd.DataFrame:
    """Load the saved DailyDialog parquet file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    logger.info(f"Loading dataset from {path}")
    return pd.read_parquet(path)

def preprocess_dialogue_pair(row: pd.Series) -> Optional[Dict[str, Any]]:
    """
    Preprocess a single dialogue pair row.
    Returns None if the record should be skipped (empty text).
    """
    # DailyDialog columns: 'dialogue', 'emotions', 'acts', 'topic'
    # We need to split the dialogue into Speaker A and Speaker B turns.
    # The dialogue is a list of strings.
    dialogue = row.get('dialogue', [])
    
    if not dialogue or len(dialogue) < 2:
        return None

    # Assume alternating speakers: A, B, A, B...
    # We will process the first pair of turns for simplicity, or aggregate if needed.
    # Based on typical DailyDialog structure, we take the first turn as A, second as B.
    turn_a_raw = dialogue[0] if len(dialogue) > 0 else ""
    turn_b_raw = dialogue[1] if len(dialogue) > 1 else ""

    if not turn_a_raw or not turn_b_raw:
        return None

    # Normalize
    norm_a = normalize_text(turn_a_raw)
    norm_b = normalize_text(turn_b_raw)

    if not is_valid_text(norm_a) or not is_valid_text(norm_b):
        return None

    return {
        'conversation_id': row.get('dialogue_id', 'unknown'), # DailyDialog might not have explicit ID, using index or topic
        'turn_index': 0, # Processing first pair
        'speaker_a_text': turn_a_raw,
        'speaker_b_text': turn_b_raw,
        'normalized_speaker_a_text': norm_a,
        'normalized_speaker_b_text': norm_b,
        'topic': row.get('topic', 'unknown')
    }

def compute_accommodation_metrics(preprocessed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute lexical overlap, syntactic similarity, and sentence length variance.
    """
    results = []

    for _, row in preprocessed_df.iterrows():
        norm_a = row['normalized_speaker_a_text']
        norm_b = row['normalized_speaker_b_text']

        # Lexical Overlap (Jaccard on tokens)
        tokens_a = tokenize_simple(norm_a)
        tokens_b = tokenize_simple(norm_b)
        lexical_overlap = jaccard_similarity(set(tokens_a), set(tokens_b))

        # Syntactic Similarity (Jaccard on POS tag sets)
        # Note: get_pos_tags returns a list of tags
        pos_a = get_pos_tags(norm_a)
        pos_b = get_pos_tags(norm_b)
        syntactic_similarity = jaccard_similarity(set(pos_a), set(pos_b))

        # Sentence Length Variance
        # Simple heuristic: split by sentence delimiters
        sentences_a = [s.strip() for s in norm_a.replace('...', '.').split('.') if s.strip()]
        sentences_b = [s.strip() for s in norm_b.replace('...', '.').split('.') if s.strip()]
        
        len_a = len(sentences_a)
        len_b = len(sentences_b)
        
        # Variance of the two lengths
        if len_a > 0 and len_b > 0:
            mean_len = (len_a + len_b) / 2.0
            variance = ((len_a - mean_len) ** 2 + (len_b - mean_len) ** 2) / 2.0
        else:
            variance = 0.0

        results.append({
            'conversation_id': row['conversation_id'],
            'turn_index': row['turn_index'],
            'speaker_a_text': row['speaker_a_text'],
            'speaker_b_text': row['speaker_b_text'],
            'normalized_speaker_a_text': norm_a,
            'normalized_speaker_b_text': norm_b,
            'lexical_overlap': lexical_overlap,
            'syntactic_similarity': syntactic_similarity,
            'sentence_length_variance': variance,
            'topic': row['topic']
        })

    return pd.DataFrame(results)

def main():
    """Main entry point for the ingestion pipeline."""
    project_root = Path(__file__).parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    contracts_dir = project_root / "contracts"

    data_raw_dir.mkdir(parents=True, exist_ok=True)
    data_processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download
    raw_file = download_daily_dialog_test(str(data_raw_dir))
    
    # 2. Load
    df_raw = load_daily_dialog_test(raw_file)
    
    # 3. Preprocess (filter empty, normalize)
    processed_rows = []
    for _, row in df_raw.iterrows():
        res = preprocess_dialogue_pair(row)
        if res:
            processed_rows.append(res)
    
    if not processed_rows:
        logger.error("No valid records found after preprocessing.")
        sys.exit(1)

    df_processed = pd.DataFrame(processed_rows)
    
    # 4. Compute Metrics
    df_metrics = compute_accommodation_metrics(df_processed)
    
    # 5. Save
    output_path = data_processed_dir / "accommodation_metrics.csv"
    df_metrics.to_csv(output_path, index=False)
    logger.info(f"Saved processed metrics to {output_path}")

    # 6. Validate against schema (T022)
    schema_path = contracts_dir / "dataset.schema.yaml"
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        return

    schema = load_schema(str(schema_path))
    is_valid = validate_dataframe(df_metrics, schema)
    
    if not is_valid:
        logger.error("Validation failed. Output does not match schema.")
        sys.exit(1)
    
    logger.info("Validation successful. Output matches schema.")

if __name__ == "__main__":
    main()