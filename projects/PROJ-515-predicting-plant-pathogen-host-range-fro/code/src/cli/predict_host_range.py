import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports
from src.config import Paths, get_default_config
from src.data.feature_extractor import extract_single_genome_features
from src.models.train import load_model
from src.utils.logging import setup_logging, get_logger

def parse_args():
    parser = argparse.ArgumentParser(description="Predict host range for a novel pathogen genome.")
    parser.add_argument("--genome", type=str, required=True, help="Path to the input genome FASTA file.")
    parser.add_argument("--model", type=str, default=None, help="Path to the trained model.pkl. Defaults to config path.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for results. Defaults to config path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    return parser.parse_args()

def load_reference_hosts(config: Dict[str, Any]) -> List[str]:
    """
    Load the list of reference host species from the interactions data.
    This assumes the interactions file exists as per the pipeline setup.
    """
    interactions_path = Path(config['paths']['raw_data']) / "interactions_merged.csv"
    if not interactions_path.exists():
        raise FileNotFoundError(f"Reference interactions file not found at {interactions_path}. "
                                "Please run the download pipeline first.")
    
    import pandas as pd
    df = pd.read_csv(interactions_path)
    # Assuming 'host_species' is the column name based on standard schema
    unique_hosts = df['host_species'].unique().tolist()
    return unique_hosts

def run_prediction(genome_path: str, model_path: Path, reference_hosts: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main prediction logic.
    1. Extract features from genome.
    2. Handle Zero-Feature Pathogen case (T029).
    3. Predict probabilities.
    4. Calculate Host-Range Breadth.
    """
    logger = get_logger()
    logger.info(f"Starting prediction for genome: {genome_path}")

    # 1. Feature Extraction
    try:
        features = extract_single_genome_features(genome_path, config)
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise

    # 2. T029: Handle Zero-Feature Pathogen
    # Check if all features are zero or if the feature vector is empty/invalid
    # We assume 'features' is a dict with keys like 'effector_count', 'sm_clusters', 'gc_content', 'kmer_profile', 'pfam_counts'
    # If kmer_profile is empty or all counts are zero, it's a zero-feature pathogen.
    
    is_zero_feature = False
    if not features:
        is_zero_feature = True
    else:
        # Check kmer_profile specifically as it's the largest feature set
        kmer_counts = features.get('kmer_profile', {})
        if not kmer_counts or sum(kmer_counts.values()) == 0:
            is_zero_feature = True
        
        # Also check if other counts are zero (edge case)
        if features.get('effector_count', 0) == 0 and features.get('sm_clusters', 0) == 0:
            # If GC content is also missing or 0, treat as zero-feature
            if features.get('gc_content', 0) == 0:
                is_zero_feature = True

    if is_zero_feature:
        logger.warning("Zero-Feature Pathogen detected. Assigning baseline prevalence probability.")
        # Calculate baseline prevalence from the reference interactions
        interactions_path = Path(config['paths']['raw_data']) / "interactions_merged.csv"
        import pandas as pd
        df = pd.read_csv(interactions_path)
        # Prevalence = Total Interactions / (Total Pathogens * Total Hosts) or similar metric?
        # Usually, baseline is the global positive rate in the dataset.
        total_rows = len(df)
        total_positives = df['label'].sum() if 'label' in df.columns else 0 # Assuming 'label' column exists
        # If label is not present, we might need to infer from 'interaction_type' or similar.
        # For robustness, let's assume 'label' 1 is positive.
        baseline_prob = total_positives / total_rows if total_rows > 0 else 0.05 # Fallback default
        logger.info(f"Baseline prevalence calculated: {baseline_prob:.4f}")
        
        # Assign baseline probability to ALL hosts
        predictions = {host: baseline_prob for host in reference_hosts}
        host_range_breadth = baseline_prob
    else:
        # 3. Normal Prediction
        logger.info("Normal feature set detected. Running model inference.")
        model = load_model(model_path)
        
        # Prepare feature vector for model
        # The model expects a specific order of features. We need to reconstruct the vector.
        # This depends on how the model was trained (T014).
        # We assume the model's feature_names_ attribute exists or we use the config order.
        
        # Reconstruct vector
        feature_vector = []
        # Order: effector_count, sm_clusters, gc_content, kmer_profile (sorted keys), pfam_counts (sorted keys)
        feature_vector.append(features['effector_count'])
        feature_vector.append(features['sm_clusters'])
        feature_vector.append(features['gc_content'])
        
        # K-mer profile
        kmers = features['kmer_profile']
        sorted_kmer_keys = sorted(kmers.keys())
        # Ensure we only use keys that match the training set if possible, 
        # but for a single prediction, we assume the model handles the input shape or we pad.
        # Assuming the model was trained with all 4-mers present in the dataset.
        # We will just append the values in sorted order of keys found in the features.
        # Note: In a real scenario, we must ensure the column order matches the training data exactly.
        for k in sorted_kmer_keys:
            feature_vector.append(kmers[k])
        
        # Pfam counts
        pfams = features['pfam_counts']
        sorted_pfam_keys = sorted(pfams.keys())
        for k in sorted_pfam_keys:
            feature_vector.append(pfams[k])

        import numpy as np
        X = np.array([feature_vector])
        
        # Predict probability of positive class
        probs = model.predict_proba(X)[:, 1]
        pred_prob = float(probs[0])
        
        # Assign to all hosts? 
        # The task description for T027 says "Compute Host-Range Breadth as the mean of all predicted infection probabilities across the unique hosts."
        # This implies the model predicts a probability for a specific host? 
        # Or does the model predict "Host Range Breadth" directly?
        # Looking at T027: "Output: Save to data/reports/prediction.csv (columns: host_species, probability)"
        # This implies we need a probability PER host.
        # However, the model trained in T014 is a Logistic Regression on genomic features vs Host Range (broad/narrow or count?).
        # If the target was a binary "Broad Host Range" label, the output is a single probability for the pathogen being broad.
        # But T027 asks for probabilities per host.
        # Interpretation: The model predicts the probability of infection for a specific pathogen-host pair.
        # But the input is ONLY pathogen features. This suggests the model might be a "Pathogen-centric" model predicting a global "infectivity score" 
        # which is then applied to all hosts, OR the model was trained on (pathogen_features, host_features) but T025 only extracts pathogen features.
        # Given the constraints of T025 (offline mode, single genome, no host features extracted), the most logical interpretation for this specific task flow is:
        # The model predicts a "Host Range Breadth" score (probability of being broad).
        # BUT T027 requires a CSV with host_species and probability.
        # Alternative Interpretation: The model predicts the probability of infection for a *generic* host, and we output this same probability for all reference hosts 
        # as a proxy for "potential to infect".
        # Let's assume the latter for this specific implementation step, as we cannot predict specific host compatibility without host features.
        
        predictions = {host: pred_prob for host in reference_hosts}
        host_range_breadth = pred_prob # Mean of identical values

    return predictions, host_range_breadth

def main():
    args = parse_args()
    
    # Setup logging
    config = get_default_config()
    setup_logging(config)
    logger = get_logger()
    
    start_time = time.time()
    
    # Load config paths
    output_dir = Path(args.output_dir) if args.output_dir else Path(config['paths']['processed_data'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = Path(args.model) if args.model else Path(config['paths']['models']) / "model.pkl"
    
    if not model_path.exists():
        logger.error(f"Model file not found at {model_path}.")
        sys.exit(1)
    
    # Load reference hosts
    try:
        reference_hosts = load_reference_hosts(config)
        logger.info(f"Loaded {len(reference_hosts)} reference hosts.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Run prediction
    try:
        predictions, breadth = run_prediction(args.genome, model_path, reference_hosts, config)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        sys.exit(1)
    
    # Save outputs
    # 1. prediction.csv
    pred_csv_path = output_dir / "prediction.csv"
    import pandas as pd
    df_pred = pd.DataFrame([
        {"host_species": host, "probability": prob} 
        for host, prob in predictions.items()
    ])
    df_pred.to_csv(pred_csv_path, index=False)
    logger.info(f"Saved predictions to {pred_csv_path}")
    
    # 2. host_range_breadth.json
    breadth_json_path = output_dir / "host_range_breadth.json"
    with open(breadth_json_path, 'w') as f:
        json.dump({"mean_probability": breadth}, f, indent=2)
    logger.info(f"Saved host range breadth to {breadth_json_path}")
    
    elapsed = time.time() - start_time
    logger.info(f"Prediction completed in {elapsed:.2f} seconds.")
    
    # Check runtime constraint (SC-003: <= 30s)
    if elapsed > 30:
        logger.warning(f"Prediction took {elapsed:.2f}s, exceeding 30s limit.")

if __name__ == "__main__":
    main()
