import os
import json
import csv
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import pyarrow.parquet as pq
from pydantic import ValidationError

# Import existing models and utils from the project API surface
from src.models.code_snippet import CodeSnippet, CodeSnippetLanguageEnum, create_codesnippet
from src.utils.config import get_project_root, get_data_processed_path, get_data_logs_path
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.memory_monitor import get_current_memory_usage_gb, check_memory_constraint, force_gc

logger = get_logger(__name__)

def detect_language_from_extension(filepath: str) -> Optional[CodeSnippetLanguageEnum]:
    """Detect language based on file extension."""
    ext_map = {
        '.c': CodeSnippetLanguageEnum.C,
        '.cpp': CodeSnippetLanguageEnum.CPP,
        '.cc': CodeSnippetLanguageEnum.CPP,
        '.cxx': CodeSnippetLanguageEnum.CPP,
        '.js': CodeSnippetLanguageEnum.JS,
        '.jsx': CodeSnippetLanguageEnum.JS,
        '.ts': CodeSnippetLanguageEnum.TS,
        '.tsx': CodeSnippetLanguageEnum.TS,
        '.py': CodeSnippetLanguageEnum.PYTHON,
    }
    ext = Path(filepath).suffix.lower()
    return ext_map.get(ext)

def normalize_label(label: Any) -> Optional[int]:
    """Normalize ground truth label to 0/1 or None if missing/invalid."""
    if label is None:
        return None
    if isinstance(label, bool):
        return 1 if label else 0
    if isinstance(label, (int, float)):
        # Assume 1 is vulnerable, 0 is safe
        return 1 if int(label) != 0 else 0
    if isinstance(label, str):
        label_lower = label.lower().strip()
        if label_lower in ['vulnerable', '1', 'yes', 'true']:
            return 1
        elif label_lower in ['safe', '0', 'no', 'false']:
            return 0
    return None

def extract_category_from_context(context: str) -> Optional[str]:
    """Extract vulnerability category from context or filename."""
    if not context:
        return None
    # Common patterns in BigVul context
    patterns = [
        r'(buffer_overflow|overflow)',
        r'(sql_injection|injection)',
        r'(use_after_free|uaf)',
        r'(null_pointer|npe)',
        r'(integer_overflow|overflow)',
        r'(race_condition|race)',
    ]
    context_lower = context.lower()
    for pattern in patterns:
        if re.search(pattern, context_lower):
            return pattern.strip('()')
    return 'unknown'

def parse_bigvul_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """Parse BigVul parquet files into raw dictionaries."""
    raw_data = []
    
    # Check for language-specific parquet files
    languages = ['c', 'cpp', 'js']
    for lang in languages:
        file_path = data_dir / f'bigvul_{lang}.parquet'
        if file_path.exists():
            try:
                df = pd.read_parquet(file_path)
                # Normalize column names if necessary
                df.columns = [col.lower() for col in df.columns]
                
                # Determine label column name (varies by source)
                label_col = None
                for col in ['label', 'ground_truth_label', 'vulnerable', 'is_vulnerable']:
                    if col in df.columns:
                        label_col = col
                        break
                
                # Determine code column name
                code_col = 'code'
                if 'code' not in df.columns:
                    for col in ['snippet', 'code_snippet', 'source_code']:
                        if col in df.columns:
                            code_col = col
                            break
                
                # Determine category column name
                category_col = 'category'
                if 'category' not in df.columns:
                    for col in ['vul_type', 'vulnerability_type', 'type']:
                        if col in df.columns:
                            category_col = col
                            break
                
                if label_col is None:
                    logger.warning(f"No label column found in {file_path}")
                    continue

                for idx, row in df.iterrows():
                    raw_data.append({
                        'id': f"{lang}_{idx}",
                        'code': str(row.get(code_col, '')),
                        'ground_truth_label': row.get(label_col),
                        'category': str(row.get(category_col, '')) if category_col in row else None,
                        'language': lang.upper(),
                        'source_file': str(file_path),
                    })
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        else:
            logger.warning(f"File not found: {file_path}")
    
    return raw_data

def parse_raw_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """Generic parser for raw data directory."""
    return parse_bigvul_directory(data_dir)

def create_code_snippets(raw_data: List[Dict[str, Any]], logger: logging.Logger) -> Tuple[List[CodeSnippet], List[Dict[str, Any]]]:
    """Convert raw dictionaries to CodeSnippet entities, filtering invalid ones."""
    valid_snippets = []
    edge_cases = []

    for idx, raw in enumerate(raw_data):
        try:
            # Normalize label
            label = normalize_label(raw.get('ground_truth_label'))
            
            # Skip samples missing ground_truth_label (as per Spec US1 Acceptance 3)
            if label is None:
                edge_cases.append({
                    'id': raw.get('id', f'unknown_{idx}'),
                    'reason': 'missing_ground_truth_label',
                    'raw_data': raw
                })
                continue

            # Detect language if not provided
            lang_str = raw.get('language', 'C')
            try:
                lang_enum = CodeSnippetLanguageEnum(lang_str.upper())
            except ValueError:
                lang_enum = CodeSnippetLanguageEnum.C  # Default fallback

            # Create CodeSnippet
            snippet = create_codesnippet(
                snippet_id=raw.get('id', f'snippet_{idx}'),
                code=raw.get('code', ''),
                language=lang_enum,
                ground_truth_label=label,
                ground_truth_category=raw.get('category', extract_category_from_context(raw.get('context', ''))),
                source_file=raw.get('source_file', ''),
            )
            
            valid_snippets.append(snippet)
            
            # Memory check every 500 snippets
            if idx % 500 == 0:
                check_memory_constraint(allowance_gb=2.0)
                if idx % 1000 == 0:
                    logger.info(f"Processed {idx} snippets, {len(valid_snippets)} valid, {len(edge_cases)} excluded")

        except ValidationError as ve:
            edge_cases.append({
                'id': raw.get('id', f'unknown_{idx}'),
                'reason': f'validation_error: {ve}',
                'raw_data': raw
            })
        except Exception as e:
            edge_cases.append({
                'id': raw.get('id', f'unknown_{idx}'),
                'reason': f'processing_error: {e}',
                'raw_data': raw
            })

    return valid_snippets, edge_cases

def stratified_sample(
    snippets: List[CodeSnippet], 
    max_samples: int = 5000, 
    seed: int = 42
) -> List[CodeSnippet]:
    """Perform stratified sampling by language and vulnerability category."""
    import random
    random.seed(seed)

    # Group by language and category
    groups = {}
    for snippet in snippets:
        key = (snippet.language.value, snippet.ground_truth_category or 'unknown')
        if key not in groups:
            groups[key] = []
        groups[key].append(snippet)

    # Calculate sample size per group
    total_groups = len(groups)
    if total_groups == 0:
        return []

    samples_per_group = max_samples // total_groups
    remainder = max_samples % total_groups

    sampled_snippets = []
    group_keys = list(groups.keys())
    
    for i, key in enumerate(group_keys):
        group_snippets = groups[key]
        # Distribute remainder to first groups
        current_sample_size = samples_per_group + (1 if i < remainder else 0)
        current_sample_size = min(current_sample_size, len(group_snippets))
        
        sampled = random.sample(group_snippets, current_sample_size)
        sampled_snippets.extend(sampled)

    logger.info(f"Stratified sampling: {len(snippets)} total -> {len(sampled_snippets)} sampled across {total_groups} groups")
    return sampled_snippets

def save_snippets_to_parquet(snippets: List[CodeSnippet], output_path: Path) -> None:
    """Save CodeSnippet list to Parquet file."""
    data = []
    for s in snippets:
        data.append({
            'snippet_id': s.snippet_id,
            'code': s.code,
            'language': s.language.value,
            'ground_truth_label': s.ground_truth_label,
            'ground_truth_category': s.ground_truth_category,
            'source_file': s.source_file,
        })
    
    df = pd.DataFrame(data)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

def save_labels_csv(snippets: List[CodeSnippet], output_path: Path) -> None:
    """Save labels.csv with snippet_id, ground_truth_label, ground_truth_category."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['snippet_id', 'ground_truth_label', 'ground_truth_category'])
        for s in snippets:
            writer.writerow([s.snippet_id, s.ground_truth_label, s.ground_truth_category or 'unknown'])
    logger.info(f"Saved labels for {len(snippets)} snippets to {output_path}")

def log_edge_cases(edge_cases: List[Dict[str, Any]], log_path: Path) -> None:
    """Log edge cases (excluded samples) to JSON."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(edge_cases, f, indent=2, default=str)
    logger.info(f"Logged {len(edge_cases)} edge cases to {log_path}")

def main():
    """Main entry point for preprocessing task T012."""
    log_stage_start("T012_Preprocess_Sampling")
    project_root = get_project_root()
    
    # Paths
    raw_data_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    logs_dir = project_root / "data" / "logs"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    output_snippets_path = processed_dir / "raw_snippets.parquet"
    output_labels_path = processed_dir / "labels.csv"
    edge_cases_log_path = logs_dir / "preprocess_edge_cases.json"

    try:
        # 1. Parse raw datasets (BigVul)
        logger.info("Parsing raw BigVul datasets...")
        raw_data = parse_raw_directory(raw_data_dir)
        logger.info(f"Parsed {len(raw_data)} raw records")

        # 2. Create CodeSnippet entities (filtering missing labels)
        logger.info("Creating CodeSnippet entities...")
        snippets, edge_cases = create_code_snippets(raw_data, logger)
        log_edge_cases(edge_cases, edge_cases_log_path)
        logger.info(f"Created {len(snippets)} valid snippets, excluded {len(edge_cases)}")

        if not snippets:
            raise ValueError("No valid snippets found after filtering. Check raw data.")

        # 3. Stratified sampling
        logger.info("Performing stratified sampling...")
        sampled_snippets = stratified_sample(snippets, max_samples=5000, seed=42)
        
        # 4. Save outputs
        logger.info("Saving outputs...")
        save_snippets_to_parquet(sampled_snippets, output_snippets_path)
        save_labels_csv(sampled_snippets, output_labels_path)

        log_stage_complete("T012_Preprocess_Sampling", {
            "total_raw": len(raw_data),
            "valid_snippets": len(snippets),
            "excluded": len(edge_cases),
            "sampled": len(sampled_snippets),
            "output_snippets": str(output_snippets_path),
            "output_labels": str(output_labels_path)
        })

    except Exception as e:
        log_stage_failure("T012_Preprocess_Sampling", str(e))
        raise

if __name__ == "__main__":
    main()
