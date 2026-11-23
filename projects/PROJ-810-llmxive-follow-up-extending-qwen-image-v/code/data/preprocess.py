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

# Constants for heuristic thresholds (kept for API compatibility)
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
                return parts
        except Exception:
            return [0, 0, 0, 0]
    elif isinstance(bbox_val, (list, tuple)):
        if len(bbox_val) == 4:
            return list(bbox_val)
    return [0, 0, 0, 0]

def load_raw_dataset(raw_path: Path) -> pd.DataFrame:
    """
    Load a parquet dataset from ``raw_path``.
    """
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

    # Identify the column that groups crops belonging to the same document/image.
    id_col = None
    for possible in ('image_id', 'doc_id', 'document_id'):
        if possible in df.columns:
            id_col = possible
            break

    if id_col is None:
        log.warning("No image identifier column found. Overlap ratio will be 0 for all rows.")
        return df

    for img_id, group in df.groupby(id_col):
        indices = group.index
        bboxes = [parse_bbox(b) for b in group['bbox']]
        modalities = group['modality'].tolist()

        for i, idx_i in enumerate(indices):
            bbox_i = bboxes[i]
            mod_i = modalities[i]

            # Area of the current crop
            area_i = (bbox_i[2] - bbox_i[0]) * (bbox_i[3] - bbox_i[1])
            if area_i <= 0:
                continue

            max_overlap = 0.0
            for j, idx_j in enumerate(indices):
                if i == j:
                    continue
                mod_j = modalities[j]
                # Only compare against different modalities (purity filter)
                if mod_i == mod_j:
                    continue

                bbox_j = bboxes[j]
                # Intersection coordinates
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
    Returns only rows where ``modality`` is either ``text`` or ``image`` and
    ``overlap_ratio`` does not exceed 0.1.
    """
    if 'modality' not in df.columns:
        log.error("Dataset missing 'modality' column.")
        return pd.DataFrame(columns=df.columns)

    # 1. Keep only rows with the required modalities.
    df_filtered = df[df['modality'].isin(['text', 'image'])].copy()

    # 2. Compute overlap ratios (if not already present).
    if 'overlap_ratio' not in df_filtered.columns:
        df_filtered = compute_overlap_ratio(df_filtered)

    # 3. Discard rows where overlap_ratio > 0.1.
    df_pure = df_filtered[df_filtered['overlap_ratio'] <= 0.1].copy()
    return df_pure

def derive_heuristic_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Kept for API compatibility.
    """
    if df.empty:
        return pd.DataFrame(columns=['region_id', 'heuristic_label', 'bbox', 'density', 'aspect_ratio'])

    bboxes = df['bbox'].apply(parse_bbox)
    df_expanded = df.copy()
    df_expanded['bbox_w'] = bboxes.apply(lambda b: b[2] - b[0])
    df_expanded['bbox_h'] = bboxes.apply(lambda b: b[3] - b[1])
    df_expanded['area'] = df_expanded['bbox_w'] * df_expanded['bbox_h']
    df_expanded['aspect_ratio'] = np.where(df_expanded['bbox_h'] > 0,
                                         df_expanded['bbox_w'] / df_expanded['bbox_h'], 0)

    text_col = 'text' if 'text' in df.columns else ('content' if 'content' in df.columns else None)
    if text_col:
        df_expanded['char_count'] = df_expanded[text_col].astype(str).str.len()
    else:
        df_expanded['char_count'] = 0

    df_expanded['density'] = np.where(df_expanded['area'] > 0,
                                    df_expanded['char_count'] / df_expanded['area'], 0)
    is_text = (df_expanded['density'] > OCR_DENSITY_THRESHOLD) | \
              (df_expanded['aspect_ratio'] > ASPECT_RATIO_THRESHOLD)
    df_expanded['heuristic_label'] = np.where(is_text, 'text', 'image')

    return df_expanded[['region_id', 'heuristic_label', 'bbox', 'density', 'aspect_ratio']].copy()

def run_extraction(raw_path: Path, output_path: Path, mode: str = 'heuristic') -> Path:
    """
    Generic entry point used by the CLI for non‑T009 modes.
    """
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

def _write_checksum(file_path: Path, checksum_path: Path) -> None:
    """
    Compute SHA‑256 checksum of ``file_path`` and write a JSON record to ``checksum_path``.
    """
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    with open(checksum_path, "w") as f:
        json.dump({"file": str(file_path), "sha256": file_hash}, f, indent=2)
    log.info(f"Checksum written to {checksum_path}")

def main():
    """
    CLI entry point. When ``--task T009`` is supplied the script reads the
    deterministic sample (``data/interim/sample.parquet``), extracts the
    ground‑truth region annotations, writes ``ground_truth.parquet`` and a
    checksum JSON file.
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, help="Task ID to execute (e.g., T009)")
    parser.add_argument("--mode", type=str, default="heuristic",
                        choices=["ground_truth", "heuristic"])
    parser.add_argument("--input", type=str,
                        default="data/raw/omnidoc_tokenbench.parquet")
    parser.add_argument("--output", type=str,
                        default="data/interim/heuristic_labels.csv")
    args = parser.parse_args()

    if args.task == "T009":
        # Preferred input is the deterministic sample produced by T007.
        input_path = paths.data("interim", "sample.parquet")
        output_path = paths.data("interim", "ground_truth.parquet")
        checksum_path = paths.results("ground_truth_checksum.json")

        log.info(f"Executing T009: processing {input_path}")
        if not input_path.exists():
            # Fallback to the raw dataset if the sample is unavailable.
            log.warning(f"{input_path} not found. Falling back to raw dataset.")
            input_path = paths.raw("omnidoc_tokenbench.parquet")
            if not input_path.exists():
                log.error(f"Fallback raw dataset {input_path} also missing.")
                sys.exit(1)

        # Load, filter, and persist the ground‑truth annotations.
        try:
            df = pd.read_parquet(input_path)
            result_df = extract_ground_truth_labels(df)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result_df.to_parquet(output_path, index=False)
            log.info(f"Saved ground truth to {output_path}. Rows: {len(result_df)}")

            # Write checksum for verification.
            _write_checksum(output_path, checksum_path)
        except Exception as e:
            log.error(f"Failed to process ground truth: {e}")
            sys.exit(1)
    else:
        # Default behavior for other modes (maintains backward compatibility).
        input_path = Path(args.input)
        output_path = Path(args.output)
        run_extraction(input_path, output_path, mode=args.mode)

if __name__ == "__main__":
    main()