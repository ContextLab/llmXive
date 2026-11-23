import os
import json
import csv
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.model_selection import StratifiedShuffleSplit

from src.models.code_snippet import CodeSnippet, CodeSnippetLanguageEnum, create_codesnippet
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.config import get_data_processed_path, get_data_logs_path, get_project_root

logger = get_logger(__name__)

# Constants for sampling
MAX_SAMPLES = 5000
RANDOM_STATE = 42

def detect_language_from_extension(filename: str) -> Optional[str]:
    """Detect language based on file extension."""
    ext_map = {
        '.c': 'C',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.h': 'C',
        '.hpp': 'C++',
        '.py': 'Python',
        '.js': 'JavaScript',
        '.java': 'Java',
        '.go': 'Go',
        '.rs': 'Rust'
    }
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext)

def normalize_label(label: Any) -> Optional[int]:
    """Normalize ground truth label to 0 or 1."""
    if label is None:
        return None
    if isinstance(label, bool):
        return 1 if label else 0
    if isinstance(label, (int, float)):
        val = int(label)
        if val in (0, 1):
            return val
    # Try string mapping
    if isinstance(label, str):
        l = label.lower().strip()
        if l in ('vulnerable', 'true', '1', 'yes'):
            return 1
        if l in ('safe', 'false', '0', 'no'):
            return 0
    return None

def extract_category_from_context(category_input: Any) -> Optional[str]:
    """Extract CWE ID or vulnerability category string."""
    if category_input is None:
        return None
    if isinstance(category_input, (int, float)):
        return f"CWE-{int(category_input)}"
    if isinstance(category_input, str):
        # If it's already a CWE string, return as is
        if re.match(r'CWE-\d+', category_input, re.IGNORECASE):
            return category_input.upper()
        # If it's a number string
        if category_input.isdigit():
            return f"CWE-{category_input}"
        # Otherwise return as is (could be a name like 'buffer-overflow')
        return category_input
    return None

def parse_raw_directory(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse raw dataset directory (BigVul or Juliet structure) into a list of dicts.
    Expected columns in raw data: code, language/lang, vulnerability_type/cwe_id, label/ground_truth_label
    """
    snippets = []
    
    # Try to find CSV or JSON files
    for ext in ['csv', 'json', 'parquet']:
        files = list(raw_dir.glob(f'*.{ext}'))
        if files:
            logger.info(f"Found {ext} files in {raw_dir}")
            break
    
    # Handle BigVul specific structure (often CSV with specific columns)
    csv_files = list(raw_dir.glob('*.csv'))
    if csv_files:
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                # Normalize column names
                # Map various possible column names to standard ones
                col_map = {}
                if 'code' in df.columns:
                    col_map['code'] = 'code'
                elif 'snippet' in df.columns:
                    col_map['snippet'] = 'code'
                elif 'content' in df.columns:
                    col_map['content'] = 'code'
                
                if 'language' in df.columns or 'lang' in df.columns:
                    lang_col = 'language' if 'language' in df.columns else 'lang'
                    col_map[lang_col] = 'language'
                
                if 'vulnerability_type' in df.columns or 'cwe_id' in df.columns:
                    cat_col = 'vulnerability_type' if 'vulnerability_type' in df.columns else 'cwe_id'
                    col_map[cat_col] = 'ground_truth_category'
                
                if 'label' in df.columns or 'ground_truth_label' in df.columns or 'is_vulnerable' in df.columns:
                    label_col = None
                    for c in ['label', 'ground_truth_label', 'is_vulnerable', 'vulnerable']:
                        if c in df.columns:
                            label_col = c
                            break
                    if label_col:
                        col_map[label_col] = 'ground_truth_label'
                
                # Rename columns
                df_renamed = df.rename(columns=col_map)
                
                # Required columns
                required = ['code', 'language', 'ground_truth_category', 'ground_truth_label']
                missing = [c for c in required if c not in df_renamed.columns]
                
                if missing:
                    logger.warning(f"Missing columns in {csv_file}: {missing}")
                    continue
                
                for _, row in df_renamed.iterrows():
                    snippets.append({
                        'code': row['code'],
                        'language': row['language'],
                        'ground_truth_category': row['ground_truth_category'],
                        'ground_truth_label': row['ground_truth_label'],
                        'source_file': str(csv_file)
                    })
            except Exception as e:
                logger.error(f"Error reading {csv_file}: {e}")
    
    # Handle JSON lines or directory of files (Juliet style)
    json_files = list(raw_dir.glob('*.jsonl')) + list(raw_dir.glob('*.json'))
    if not csv_files and json_files:
        for json_file in json_files:
            try:
                if json_file.suffix == '.jsonl':
                    with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f):
                            try:
                                data = json.loads(line)
                                snippets.append({
                                    'code': data.get('code', data.get('snippet', '')),
                                    'language': data.get('language', data.get('lang', 'Unknown')),
                                    'ground_truth_category': data.get('cwe_id', data.get('vulnerability_type', 'Unknown')),
                                    'ground_truth_label': data.get('label', data.get('ground_truth_label', data.get('is_vulnerable'))),
                                    'source_file': f"{json_file}:{line_num}"
                                })
                            except json.JSONDecodeError:
                                continue
                else:
                    with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for i, item in enumerate(data):
                                snippets.append({
                                    'code': item.get('code', item.get('snippet', '')),
                                    'language': item.get('language', item.get('lang', 'Unknown')),
                                    'ground_truth_category': item.get('cwe_id', item.get('vulnerability_type', 'Unknown')),
                                    'ground_truth_label': item.get('label', item.get('ground_truth_label', item.get('is_vulnerable'))),
                                    'source_file': f"{json_file}:{i}"
                                })
            except Exception as e:
                logger.error(f"Error reading {json_file}: {e}")
    
    return snippets

def create_code_snippets(raw_data: List[Dict[str, Any]], dropped_log: List[Dict]) -> List[CodeSnippet]:
    """
    Convert raw dicts to CodeSnippet entities.
    Log samples missing ground_truth_label to dropped_log.
    """
    snippets = []
    
    for i, raw in enumerate(raw_data):
        code = raw.get('code', '').strip()
        if not code:
            continue
        
        lang_raw = raw.get('language')
        category_raw = raw.get('ground_truth_category')
        label_raw = raw.get('ground_truth_label')
        
        # Normalize language
        lang = detect_language_from_extension(lang_raw) if lang_raw and lang_raw.startswith('.') else lang_raw
        if lang is None:
            # Try to infer from content if available (simple heuristic)
            lang = 'Unknown'
        
        # Normalize category
        category = extract_category_from_context(category_raw)
        if category is None:
            category = 'Unknown'
        
        # Normalize label
        label = normalize_label(label_raw)
        
        snippet_id = f"snippet_{i:06d}"
        
        # Check if label is missing (for accuracy calculation exclusion)
        if label is None:
            dropped_log.append({
                'snippet_id': snippet_id,
                'reason': 'missing_label',
                'source': raw.get('source_file', 'unknown'),
                'language': lang,
                'category': category
            })
            # We still keep the snippet for inference, but note it for accuracy calc later
            # However, task says "Exclude samples missing ground_truth_label from accuracy calculation"
            # We will filter them out when creating labels.csv, but keep in parquet for inference
        
        try:
            # Try to create valid CodeSnippet
            snippet = create_codesnippet(
                snippet_id=snippet_id,
                code=code,
                language=lang,
                ground_truth_category=category,
                ground_truth_label=label
            )
            snippets.append(snippet)
        except Exception as e:
            logger.warning(f"Failed to create snippet {snippet_id}: {e}")
            dropped_log.append({
                'snippet_id': snippet_id,
                'reason': f'validation_error: {str(e)}',
                'source': raw.get('source_file', 'unknown')
            })
    
    return snippets

def stratified_sample(snippets: List[CodeSnippet], max_samples: int = MAX_SAMPLES) -> Tuple[List[CodeSnippet], Dict]:
    """
    Perform stratified sampling by language and ground_truth_category.
    Returns sampled snippets and distribution stats.
    """
    if not snippets:
        return [], {}
    
    # Create DataFrame for sampling
    data = []
    for s in snippets:
        data.append({
            'snippet_id': s.snippet_id,
            'language': s.language,
            'ground_truth_category': s.ground_truth_category,
            'ground_truth_label': s.ground_truth_label,
            'code': s.code
        })
    
    df = pd.DataFrame(data)
    
    # Create stratification key: language + category
    df['strat_key'] = df['language'].astype(str) + '__' + df['ground_truth_category'].astype(str)
    
    # Filter to samples with valid labels for stratification (to ensure meaningful stratification)
    # But we want to keep all samples for inference, so we stratify on available labels
    valid_labels_mask = df['ground_truth_label'].notna()
    
    if valid_labels_mask.sum() < 2:
        logger.warning("Insufficient samples with valid labels for stratification. Using random sample.")
        sampled_df = df.sample(n=min(max_samples, len(df)), random_state=RANDOM_STATE)
        stats = {'method': 'random', 'total': len(df), 'sampled': len(sampled_df)}
        return [CodeSnippet(**row.drop('strat_key')) for _, row in sampled_df.iterrows()], stats
    
    # Stratified split
    # We want to sample from the full dataset, but stratify by the distribution of labels
    # Since we have multiple categories, we use the strat_key
    split = StratifiedShuffleSplit(n_splits=1, test_size=1 - min(max_samples, len(df)) / len(df), random_state=RANDOM_STATE)
    
    # Get indices for training (sampled) set
    # If dataset is small, take all
    if len(df) <= max_samples:
        sampled_df = df
    else:
        try:
            for train_idx, test_idx in split.split(df, df['strat_key']):
                sampled_df = df.iloc[train_idx]
                break
        except ValueError as e:
            logger.warning(f"Stratified split failed: {e}. Using random sample.")
            sampled_df = df.sample(n=max_samples, random_state=RANDOM_STATE)
    
    # Calculate stats
    stats = {
        'method': 'stratified',
        'total': len(df),
        'sampled': len(sampled_df),
        'language_distribution': sampled_df['language'].value_counts().to_dict(),
        'category_distribution': sampled_df['ground_truth_category'].value_counts().to_dict()
    }
    
    # Convert back to CodeSnippet objects
    sampled_snippets = []
    for _, row in sampled_df.iterrows():
        # Remove strat_key before creating snippet
        row_dict = row.to_dict()
        row_dict.pop('strat_key', None)
        try:
            snippet = CodeSnippet(**row_dict)
            sampled_snippets.append(snippet)
        except Exception as e:
            logger.warning(f"Failed to create snippet from sampled row: {e}")
    
    return sampled_snippets, stats

def save_snippets_to_parquet(snippets: List[CodeSnippet], output_path: Path):
    """Save snippets to parquet file."""
    data = []
    for s in snippets:
        data.append({
            'snippet_id': s.snippet_id,
            'code': s.code,
            'language': s.language,
            'ground_truth_category': s.ground_truth_category,
            'ground_truth_label': s.ground_truth_label
        })
    
    df = pd.DataFrame(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

def save_labels_csv(snippets: List[CodeSnippet], output_path: Path):
    """
    Save labels.csv with snippet_id, ground_truth_label, ground_truth_category.
    Exclude samples with missing labels from this file (as per task constraint).
    """
    rows = []
    for s in snippets:
        if s.ground_truth_label is not None:
            rows.append({
                'snippet_id': s.snippet_id,
                'ground_truth_label': s.ground_truth_label,
                'ground_truth_category': s.ground_truth_category
            })
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['snippet_id', 'ground_truth_label', 'ground_truth_category'])
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Saved {len(rows)} labeled samples to {output_path}")

def log_edge_cases(dropped_log: List[Dict], output_path: Path):
    """Log dropped samples to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dropped_log, f, indent=2, default=str)
    logger.info(f"Logged {len(dropped_log)} dropped samples to {output_path}")

def main():
    """Main entry point for preprocessing."""
    log_stage_start("T012", "Preprocess & Sampling")
    
    try:
        project_root = get_project_root()
        raw_dir = project_root / "data" / "raw"
        processed_dir = get_data_processed_path()
        logs_dir = get_data_logs_path()
        
        # Parse raw datasets
        raw_snippets = parse_raw_directory(raw_dir)
        logger.info(f"Parsed {len(raw_snippets)} raw snippets from {raw_dir}")
        
        # Create CodeSnippet entities and track dropped samples
        dropped_log = []
        snippets = create_code_snippets(raw_snippets, dropped_log)
        logger.info(f"Created {len(snippets)} CodeSnippet entities")
        
        # Perform stratified sampling
        sampled_snippets, stats = stratified_sample(snippets, MAX_SAMPLES)
        logger.info(f"Stratified sample: {stats}")
        
        # Save outputs
        parquet_path = processed_dir / "raw_snippets.parquet"
        labels_path = processed_dir / "labels.csv"
        dropped_path = logs_dir / "dropped_samples.json"
        
        save_snippets_to_parquet(sampled_snippets, parquet_path)
        save_labels_csv(sampled_snippets, labels_path)
        log_edge_cases(dropped_log, dropped_path)
        
        log_stage_complete("T012", {
            'total_raw': len(raw_snippets),
            'total_created': len(snippets),
            'total_sampled': len(sampled_snippets),
            'dropped_count': len(dropped_log),
            'stats': stats
        })
        
    except Exception as e:
        log_stage_failure("T012", str(e))
        raise

if __name__ == "__main__":
    main()
