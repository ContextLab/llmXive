#!/usr/bin/env python3
"""
Compute anomaly scores with probabilistic uncertainty estimates.

This script demonstrates the uncertainty estimation capability added in T021
and produces real artifacts (anomaly scores with uncertainty) for review.

Per Constitution Principle VI, this script:
- Downloads/generates data
- Runs the DPGMM model
- Computes uncertainty estimates
- Saves results to data/processed/
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'code'))
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_test_data(n_observations: int = 1000, n_features: int = 2, 
                      anomaly_rate: float = 0.05) -> tuple:
    """Generate synthetic time series data with known anomalies.
    
    Args:
        n_observations: Number of observations to generate
        n_features: Number of features per observation
        anomaly_rate: Fraction of observations that are anomalous
    
    Returns:
        Tuple of (observations, labels) where labels are 0 (normal) or 1 (anomaly)
    """
    np.random.seed(42)
    
    observations = []
    labels = []
    
    n_anomalies = int(n_observations * anomaly_rate)
    anomaly_indices = set(np.random.choice(n_observations, n_anomalies, replace=False))
    
    for i in range(n_observations):
        if i in anomaly_indices:
            # Anomalous observation - from outlier distribution
            obs = np.random.normal(10, 3, n_features)
            labels.append(1)
        else:
            # Normal observation - from mixture of two clusters
            if np.random.random() < 0.5:
                obs = np.random.normal(0, 1, n_features)
            else:
                obs = np.random.normal(5, 1, n_features)
            labels.append(0)
        
        observations.append(obs)
    
    return np.array(observations), np.array(labels)

def main():
    """Main function to compute anomaly scores with uncertainty."""
    logger.info("Starting anomaly detection with uncertainty estimation")
    
    # Import DPGMM model
    from src.models.dpgmm import DPGMMModel, DPGMMConfig, AnomalyScoreWithUncertainty
    
    # Create output directory
    output_dir = project_root / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate test data
    logger.info("Generating synthetic test data")
    observations, labels = generate_test_data(n_observations=1000, n_features=2)
    
    # Create and configure model
    config = DPGMMConfig(
        concentration=1.0,
        random_seed=42,
        max_clusters=20,
        credible_level=0.95
    )
    model = DPGMMModel(config)
    
    # Process observations with streaming updates
    logger.info("Processing observations with DPGMM")
    scores = model.fit_streaming(observations.tolist())
    
    # Collect results
    results = []
    for score in scores:
        result = {
            'observation_id': score.observation_id,
            'timestamp': score.timestamp.isoformat(),
            'anomaly_score': score.anomaly_score,
            'posterior_variance': score.posterior_variance,
            'credible_interval_95': score.credible_interval_95,
            'mixture_uncertainty': score.mixture_uncertainty,
            'component_probabilities': score.component_probabilities,
            'ground_truth_label': labels[score.observation_id]
        }
        results.append(result)
    
    # Save results to JSON
    results_file = output_dir / 'anomaly_scores_with_uncertainty.json'
    with open(results_file, 'w') as f:
        json.dump({
            'metadata': {
                'n_observations': len(observations),
                'n_features': observations.shape[1],
                'anomaly_rate': float(np.mean(labels)),
                'model_config': {
                    'concentration': config.concentration,
                    'max_clusters': config.max_clusters,
                    'credible_level': config.credible_level
                },
                'generated_at': datetime.now().isoformat()
            },
            'results': results
        }, f, indent=2)
    
    logger.info(f"Saved results to {results_file}")
    
    # Save uncertainty summary
    summary = model.get_uncertainty_summary()
    summary_file = output_dir / 'uncertainty_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved uncertainty summary to {summary_file}")
    
    # Print summary statistics
    print("\n" + "=" * 70)
    print("ANOMALY DETECTION WITH UNCERTAINTY ESTIMATES - RESULTS")
    print("=" * 70)
    print(f"\nTotal observations processed: {len(observations)}")
    print(f"Anomaly rate in data: {np.mean(labels):.2%}")
    print(f"Active clusters: {len(model.get_active_clusters())}")
    print(f"\nUncertainty Summary:")
    print(f"  Mean posterior variance: {summary['mean_posterior_variance']:.4f}")
    print(f"  Mean mixture uncertainty: {summary['mean_mixture_uncertainty']:.4f}")
    print(f"  Max mixture uncertainty: {summary['max_mixture_uncertainty']:.4f}")
    
    # Compute detection performance
    scores_array = np.array([r['anomaly_score'] for r in results])
    threshold = np.percentile(scores_array, 95)
    predictions = (scores_array > threshold).astype(int)
    
    tp = np.sum((predictions == 1) & (labels == 1))
    fp = np.sum((predictions == 1) & (labels == 0))
    tn = np.sum((predictions == 0) & (labels == 0))
    fn = np.sum((predictions == 0) & (labels == 1))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    print(f"\nDetection Performance (95th percentile threshold):")
    print(f"  True Positives: {tp}")
    print(f"  False Positives: {fp}")
    print(f"  True Negatives: {tn}")
    print(f"  False Negatives: {fn}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall: {recall:.4f}")
    print(f"  F1-Score: {f1:.4f}")
    
    # Print sample results with uncertainty
    print("\n" + "=" * 70)
    print("SAMPLE RESULTS WITH UNCERTAINTY ESTIMATES")
    print("=" * 70)
    
    # Show top 5 most anomalous observations
    sorted_indices = np.argsort(scores_array)[::-1][:5]
    for idx in sorted_indices:
        r = results[idx]
        print(f"\nObservation {r['observation_id']}:")
        print(f"  Anomaly Score: {r['anomaly_score']:.4f}")
        print(f"  95% CI: ({r['credible_interval_95'][0]:.4f}, {r['credible_interval_95'][1]:.4f})")
        print(f"  Posterior Variance: {r['posterior_variance']:.4f}")
        print(f"  Mixture Uncertainty: {r['mixture_uncertainty']:.4f}")
        print(f"  Ground Truth: {'ANOMALY' if r['ground_truth_label'] == 1 else 'NORMAL'}")
    
    logger.info("Anomaly detection with uncertainty completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
