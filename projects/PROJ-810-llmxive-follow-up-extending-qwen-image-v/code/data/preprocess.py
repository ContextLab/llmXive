import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Constants for heuristic thresholds (kept for API compatibility with T008b)
OCR_DENSITY_THRESHOLD = 0.005
ASPECT_RATIO_THRESHOLD = 2.0

def parse_bbox(bbox_val):
    """
    Standardizes bbox format to [x1, y1, x2, y2].
    """
    if isinstance(bbox_val, str):
        try:
            parts = list(map(float, bbox_val.strip('[]()').split(',')))
            if len(parts) == 4:
                # If x2 < x1, it's likely x1, y1, x2, y2 already.
                # If parts[2] > parts[0] and parts[3] > parts[1], it could be [x, y, w, h] or [x1, y1, x2, y2].
                # We assume [x1, y1, x2, y2] for the ground truth extraction based on standard dataset formats.
                return parts
        except:
            return [0, 0, 0, 0]
    elif isinstance(bbox_val, (list, tuple)):
        if len(bbox_val) == 4:
            return list(bbox_val)
    return [0, 0, 0, 0]

def load_raw_dataset(raw_path: Path) -> pd.DataFrame:
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}.")
    return pd.read_parquet(raw_path)

def compute_overlap_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the maximum overlap ratio for each crop against crops of a different modality
    within the same image. Overlap is defined as Intersection / Area of the crop.
    """
    df = df.copy()
    df['overlap_ratio'] = 0.0
    
    # Group by image identifier to only compare crops within the same document
    # Common columns in Omni-Doc-1 are 'image_id' or 'doc_id'
    id_col = 'image_id' if 'image_id' in df.columns else ('doc_id' if 'doc_id' in df.columns else None)
    
    if id_col is None:
        log.warning("No image identifier column found. Overlap ratio will be 0 for all.")
        return df

    for img_id, group in df.groupby(id_col):
        indices = group.index
        bboxes = [parse_bbox(b) for b in group['bbox']]
        modalities = group['modality'].tolist()
        
        for i in range(len(indices)):
            idx_i = indices[i]
            bbox_i = bboxes[i]
            mod_i = modalities[i]
            
            # Area of current crop
            area_i = (bbox_i[2] - bbox_i[0]) * (bbox_i[3] - bbox_i[1])
            if area_i <= 0:
                continue
                
            max_overlap = 0.0
            for j in range(len(indices)):
                if i == j: continue
                mod_j = modalities[j]
                # Only compute overlap with different modalities (Purity check)
                if mod_i == mod_j: continue
                
                bbox_j = bboxes[j]
                # Intersection
                inter_x1 = max(bbox_i[0], bbox_j[0])
                inter_y1 = max(bbox_i[1], bbox_j[1])
                inter_x2 = min(bbox_i[2], bbox_j[2])
                inter_y2 = min(bbox_i[3], bbox_j[3])
                
                inter_w = max(0, inter_x2 - inter_x1)
                inter_h = max(0, inter_y2 - inter_y1)
                inter_area = inter_w * inter_h
                
                overlap = inter_area / area_i
                if overlap > max_overlap:
                    max_overlap = overlap
            
            df.at[idx_i, 'overlap_ratio'] = max_overlap
    return df

def extract_ground_truth_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    T009 Implementation: Filters for modality and overlap ratio.
    """
    # 1. Filter crops with modality 'text' or 'image'
    df_filtered = df[df['modality'].isin(['text', 'image'])].copy()
    
    # 2. Compute overlap ratio
    df_with_overlap = compute_overlap_ratio(df_filtered)
    
    # 3. Discard any with overlap_ratio > 0.1
    df_pure = df_with_overlap[df_with_overlap['overlap_ratio'] <= 0.1].copy()
    
    return df_pure

def derive_heuristic_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Kept for API compatibility with existing surface.
    """
    if df.empty:
        return pd.DataFrame(columns=['region_id', 'heuristic_label', 'bbox', 'density', 'aspect_ratio'])
    
    bboxes = df['bbox'].apply(parse_bbox)
    df_expanded = df.copy()
    df_expanded['bbox_w'] = bboxes.apply(lambda b: b[2] - b[0])
    df_expanded['bbox_h'] = bboxes.apply(lambda b: b[3] - b[1])
    df_expanded['area'] = df_expanded['bbox_w'] * df_expanded['bbox_h']
    df_expanded['aspect_ratio'] = np.where(df_expanded['bbox_h'] > 0, df_expanded['bbox_w'] / df_expanded['bbox_h'], 0)
    
    text_col = 'text' if 'text' in df.columns else ('content' if 'content' in df.columns else None)
    if text_col:
        df_expanded['char_count'] = df_expanded[text_col].astype(str).str.len()
    else:
        df_expanded['char_count'] = 0
    
    df_expanded['density'] = np.where(df_expanded['area'] > 0, df_expanded['char_count'] / df_expanded['area'], 0)
    is_text = (df_expanded['density'] > OCR_DENSITY_THRESHOLD) | (df_expanded['aspect_ratio'] > ASPECT_RATIO_THRESHOLD)
    df_expanded['heuristic_label'] = np.where(is_text, 'text', 'image')
    
    return df_expanded[['region_id', 'heuristic_label', 'bbox', 'density', 'aspect_ratio']].copy()

def run_extraction(raw_path: Path, output_path: Path, mode: str = 'heuristic') -> Path:
    df = load_raw_dataset(raw_path)
    if mode == 'ground_truth':
        result_df = extract_ground_truth_labels(df)
        output_path = output_path.with_suffix('.parquet')
    elif mode == 'heuristic':
        result_df = derive_heuristic_labels(df)
        output_path = output_path.with_suffix('.csv')
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == '.parquet':
        result_df.to_parquet(output_path, index=False)
    else:
        result_df.to_csv(output_path, index=False)
    return output_path

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, help="Task ID to execute (e.g., T009)")
    parser.add_argument("--mode", type=str, default="heuristic", choices=["ground_truth", "heuristic"])
    parser.add_argument("--input", type=str, default="data/raw/omnidoc_tokenbench.parquet")
    parser.add_argument("--output", type=str, default="data/interim/heuristic_labels.csv")
    args = parser.parse_args()

    if args.task == "T009":
        input_path = paths.data("interim", "sample.parquet")
        output_path = paths.data("interim", "ground_truth.parquet")
        
        log.info(f"Executing T009: Processing {input_path}")
        if not input_path.exists():
            log.error(f"Input file {input_path} not found. Ensure T007 is completed.")
            sys.exit(1)
        
        df = pd.read_parquet(input_path)
        result_df = extract_ground_truth_labels(df)
        result_df.to_parquet(output_path, index=False)
        log.info(f"Saved ground truth to {output_path}. Rows: {len(result_df)}")
        
        # Generate checksum
        with open(output_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        checksum_path = paths.results("ground_truth_checksum.json")
        with open(checksum_path, "w") as f:
            json.dump({"file": str(output_path), "sha256": file_hash}, f, indent=2)
        log.info(f"Checksum written to {checksum_path}")
    else:
        # Default behavior for --mode
        input_path = Path(args.input)
        output_path = Path(args.output)
        run_extraction(input_path, output_path, mode=args.mode)

if __name__ == "__main__":
    main()