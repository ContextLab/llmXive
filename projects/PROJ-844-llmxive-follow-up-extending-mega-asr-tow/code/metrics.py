"""
metrics.py - Semantic Similarity Score (SSS) and WER calculations.

Implements FR-003 (SSS via all-MiniLM-L6-v2) and FR-009 (WER via jiwer).
Also implements T030b (HVCM) and T020b/c (baseline calculations) as required by downstream tasks.
"""
import os
import json
import logging
import math
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import jiwer
from datasets import load_dataset

from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DEVICE = "cpu"  # Enforce CPU as per constraints

class MetricsCalculator:
    """
    Calculator for Semantic Similarity Score (SSS) and Word Error Rate (WER).
    Handles loading of the embedding model and computation of metrics.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.embedding_model = None
        self._model_loaded = False

    def _load_embedding_model(self):
        """Lazy load the sentence transformer model."""
        if not self._model_loaded:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME} on {DEVICE}...")
            try:
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=DEVICE)
                self._model_loaded = True
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def compute_sss(self, reference_text: str, hypothesis_text: str) -> float:
        """
        Compute Semantic Similarity Score (SSS) using cosine similarity of embeddings.
        
        Args:
            reference_text: The ground truth transcript.
            hypothesis_text: The ASR hypothesis.
            
        Returns:
            float: Cosine similarity score between -1 and 1 (typically 0 to 1 for valid text).
        """
        if not self._model_loaded:
            self._load_embedding_model()

        if not reference_text or not hypothesis_text:
            # Handle empty strings gracefully; return 0 or NaN? 
            # Per FR-003, we need a score. If one is empty, semantic overlap is 0.
            return 0.0

        try:
            embeddings = self.embedding_model.encode([reference_text, hypothesis_text], convert_to_numpy=True)
            # embeddings shape: (2, dimension)
            # Compute cosine similarity between the two vectors
            sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(sim)
        except Exception as e:
            logger.error(f"Error computing SSS for texts: {e}")
            raise

    def compute_wer(self, reference_text: str, hypothesis_text: str) -> float:
        """
        Compute Word Error Rate (WER) using jiwer.
        
        Args:
            reference_text: The ground truth transcript.
            hypothesis_text: The ASR hypothesis.
            
        Returns:
            float: WER score between 0 and infinity (0 is perfect).
        """
        if not reference_text or not hypothesis_text:
            # If hypothesis is empty but reference is not, WER is 1.0 (100% error)
            # If both empty, WER is 0.0
            if not reference_text and not hypothesis_text:
                return 0.0
            return 1.0

        try:
            # jiwer expects strings
            transform = jiwer.Compose([
                jiwer.ToLowerCase(),
                jiwer.RemoveMultipleSpaces(),
                jiwer.Strip(),
                jiwer.ReduceToListOfListOfWords()
            ])
            wer_score = jiwer.wer(reference_text, hypothesis_text, transform=transform)
            return float(wer_score)
        except Exception as e:
            logger.error(f"Error computing WER for texts: {e}")
            raise

    def compute_batch_sss(self, references: List[str], hypotheses: List[str]) -> List[float]:
        """Compute SSS for a batch of pairs."""
        if not self._model_loaded:
            self._load_embedding_model()
        
        if not references or not hypotheses:
            return []
        
        if len(references) != len(hypotheses):
            raise ValueError("References and hypotheses must have the same length.")

        # Encode all at once for efficiency
        try:
            # Flatten for encoding if needed, but list of strings is fine
            all_texts = references + hypotheses
            embeddings = self.embedding_model.encode(all_texts, convert_to_numpy=True)
            
            ref_embeds = embeddings[:len(references)]
            hyp_embeds = embeddings[len(references):]
            
            # Compute pairwise cosine similarity
            sims = cosine_similarity(ref_embeds, hyp_embeds)
            # Diagonal is the similarity for each pair
            return sims.diagonal().tolist()
        except Exception as e:
            logger.error(f"Batch SSS computation failed: {e}")
            raise

    def compute_batch_wer(self, references: List[str], hypotheses: List[str]) -> List[float]:
        """Compute WER for a batch of pairs."""
        if not references or not hypotheses:
            return []
        
        if len(references) != len(hypotheses):
            raise ValueError("References and hypotheses must have the same length.")

        results = []
        for ref, hyp in zip(references, hypotheses):
            results.append(self.compute_wer(ref, hyp))
        return results

def compute_baseline_sss_and_wer(
    stress_curves_path: Path, 
    output_path: Path
) -> Dict[str, Any]:
    """
    T020b/c: Compute baseline SSS and WER for each model/scenario (distortion intensity 0).
    Reads stress_curves.parquet, filters for intensity=0, computes metrics, and saves JSON.
    
    Args:
        stress_curves_path: Path to the stress curves parquet file.
        output_path: Path to save the baseline JSON.
        
    Returns:
        Dict containing baseline SSS and WER keyed by (model, scenario_id).
    """
    logger.info(f"Loading stress curves from {stress_curves_path}...")
    if not stress_curves_path.exists():
        raise FileNotFoundError(f"Stress curves file not found: {stress_curves_path}")
    
    df = pd.read_parquet(stress_curves_path)
    
    # Filter for baseline (intensity = 0)
    # Assuming 'distortion_intensity' or similar column exists. 
    # Based on T012/T010 context, we expect a column indicating intensity level.
    # If the column is named 'intensity' or 'distortion_level', adjust. 
    # Let's assume 'distortion_intensity' based on common naming in such tasks.
    # If the dataframe has a 'step' or 'level' column representing intensity, we use that.
    # For safety, we look for a column that might represent 0 intensity.
    # Common convention: 'intensity' or 'distortion_intensity'.
    
    intensity_col = None
    candidates = ['distortion_intensity', 'intensity', 'level', 'step']
    for cand in candidates:
        if cand in df.columns:
            intensity_col = cand
            break
    
    if intensity_col is None:
        raise ValueError("Could not find an intensity column in stress_curves.parquet. Expected one of: 'distortion_intensity', 'intensity', 'level', 'step'.")

    baseline_df = df[df[intensity_col] == 0].copy()
    
    if baseline_df.empty:
        logger.warning("No baseline (intensity=0) rows found in stress curves.")
        return {}

    calculator = MetricsCalculator()
    
    baselines = {}
    
    # Group by model and scenario (if applicable)
    # Assuming columns: 'model_id', 'scenario_id', 'reference_text', 'hypothesis_text'
    required_cols = ['model_id', 'reference_text', 'hypothesis_text']
    if not all(col in baseline_df.columns for col in required_cols):
        # Try to infer scenario if not present, or just group by model
        if 'scenario_id' not in baseline_df.columns:
            baseline_df['scenario_id'] = 'default'
    
    for (model_id, scenario_id), group in baseline_df.groupby(['model_id', 'scenario_id']):
        refs = group['reference_text'].tolist()
        hypers = group['hypothesis_text'].tolist()
        
        sss_scores = calculator.compute_batch_sss(refs, hypers)
        wer_scores = calculator.compute_batch_wer(refs, hypers)
        
        avg_sss = np.mean(sss_scores)
        avg_wer = np.mean(wer_scores)
        
        key = f"{model_id}_{scenario_id}"
        baselines[key] = {
            "avg_sss": avg_sss,
            "avg_wer": avg_wer,
            "count": len(group)
        }
        logger.info(f"Baseline for {key}: SSS={avg_sss:.4f}, WER={avg_wer:.4f}")
    
    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(baselines, f, indent=2)
        
    logger.info(f"Baselines saved to {output_path}")
    return baselines

def compute_hvcm_target(
    human_annotations_path: Path,
    stress_curves_path: Path,
    output_path: Path
) -> pd.DataFrame:
    """
    T030b: Compute Human-Validated Collapse Margin (HVCM) target.
    Merges human annotations with stress curves to derive the regression target.
    
    Logic:
    1. Load human_annotations.csv (contains intelligibility scores 0-1).
    2. Load stress_curves.parquet.
    3. Match by audio_id (or similar).
    4. For each audio clip, find the distortion intensity where SSS drops below the human-validated threshold.
    5. The HVCM is the margin between the predicted collapse and the human-validated collapse.
    
    Note: This is a simplified implementation of the HVCM logic. The exact definition depends on
    the specific formula in the spec. Here we assume HVCM = (Human_Collapse_Intensity - Model_Collapse_Intensity).
    
    Args:
        human_annotations_path: Path to human_annotations.csv.
        stress_curves_path: Path to stress_curves.parquet.
        output_path: Path to save the HVCM results.
        
    Returns:
        DataFrame with HVCM targets.
    """
    logger.info(f"Loading human annotations from {human_annotations_path}...")
    if not human_annotations_path.exists():
        raise FileNotFoundError(f"Human annotations file not found: {human_annotations_path}")
    
    human_df = pd.read_csv(human_annotations_path)
    
    logger.info(f"Loading stress curves from {stress_curves_path}...")
    if not stress_curves_path.exists():
        raise FileNotFoundError(f"Stress curves file not found: {stress_curves_path}")
    
    stress_df = pd.read_parquet(stress_curves_path)
    
    # Identify the audio ID column
    audio_id_col = None
    candidates = ['audio_id', 'clip_id', 'id']
    for cand in candidates:
        if cand in human_df.columns and cand in stress_df.columns:
            audio_id_col = cand
            break
    
    if audio_id_col is None:
        # Fallback to a common name if not found
        if 'audio_id' in human_df.columns:
            audio_id_col = 'audio_id'
        else:
            raise ValueError("Could not find a common audio ID column between human annotations and stress curves.")
    
    # Merge
    merged = pd.merge(human_df, stress_df, on=audio_id_col, how='inner')
    
    if merged.empty:
        raise ValueError("No matching records found between human annotations and stress curves.")
    
    # Determine human collapse threshold (e.g., 0.5 intelligibility)
    # This might be configurable, but we assume 0.5 for now.
    human_threshold = 0.5
    
    # Identify intensity column
    intensity_col = None
    candidates = ['distortion_intensity', 'intensity', 'level', 'step']
    for cand in candidates:
        if cand in merged.columns:
            intensity_col = cand
            break
    
    if intensity_col is None:
        raise ValueError("Could not find an intensity column in merged data.")
    
    # Calculate HVCM for each clip
    # Simplified: Find the intensity where human score drops below threshold.
    # Then find the intensity where SSS drops below threshold.
    # HVCM = Human_Collapse - Model_Collapse
    
    results = []
    
    # Group by audio_id to process each clip
    for audio_id, group in merged.groupby(audio_id_col):
        # Sort by intensity
        group = group.sort_values(intensity_col)
        
        # Find human collapse point
        human_scores = group['intelligibility_score'].values # Assuming column name
        intensities = group[intensity_col].values
        
        human_collapse = None
        for i, score in enumerate(human_scores):
            if score < human_threshold:
                human_collapse = intensities[i]
                break
        
        if human_collapse is None:
            # If no collapse found, use max intensity
            human_collapse = intensities[-1]
        
        # Find model collapse point (SSS < 0.5)
        # Assuming SSS column is 'sss' or 'semantic_similarity_score'
        sss_col = None
        for cand in ['sss', 'semantic_similarity_score']:
            if cand in group.columns:
                sss_col = cand
                break
        
        if sss_col is None:
            # Fallback: compute on the fly? No, assume it's in the dataframe from T013/T015
            # If not present, we cannot compute HVCM.
            logger.warning(f"SSS column not found for {audio_id}. Skipping HVCM calculation.")
            continue
            
        model_collapse = None
        sss_scores = group[sss_col].values
        
        for i, score in enumerate(sss_scores):
            if score < human_threshold: # Using same threshold for model collapse
                model_collapse = intensities[i]
                break
        
        if model_collapse is None:
            model_collapse = intensities[-1]
        
        hvcm = human_collapse - model_collapse
        
        results.append({
            audio_id_col: audio_id,
            'human_collapse_intensity': human_collapse,
            'model_collapse_intensity': model_collapse,
            'hvcm': hvcm
        })
    
    hvcm_df = pd.DataFrame(results)
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    hvcm_df.to_parquet(output_path, index=False)
    logger.info(f"HVCM targets saved to {output_path}")
    
    return hvcm_df

def main():
    """
    Main entry point for running metrics calculations.
    Can be configured via command line or environment variables.
    """
    config = get_config()
    
    # Example usage: Compute baselines and HVCM
    # Note: This assumes stress_curves.parquet and human_annotations.csv exist.
    # In a real run, these would be passed as arguments or loaded from config.
    
    stress_curves_path = Path(config['paths']['derived']) / 'stress_curves.parquet'
    human_annotations_path = Path(config['paths']['validation']) / 'human_annotations.csv'
    baseline_output = Path(config['paths']['derived']) / 'baseline_sss_wer.json'
    hvcm_output = Path(config['paths']['derived']) / 'hvcm_targets.parquet'
    
    if stress_curves_path.exists() and human_annotations_path.exists():
        logger.info("Running baseline calculations...")
        compute_baseline_sss_and_wer(stress_curves_path, baseline_output)
        
        logger.info("Running HVCM calculation...")
        compute_hvcm_target(human_annotations_path, stress_curves_path, hvcm_output)
    else:
        logger.warning("Required input files not found. Skipping full metrics run.")
        logger.info(f"Expected stress curves: {stress_curves_path}")
        logger.info(f"Expected human annotations: {human_annotations_path}")

if __name__ == "__main__":
    main()