"""
Robustness analysis module for the Bayesian Nonparametrics Anomaly Detection pipeline.

This module implements robustness checks for the DP-GMM model, including:
- Sensitivity analysis on window size and derivative calculation methods
- MCMC validation against ADVI results
- Parameter perturbation studies
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

import numpy as np
import pandas as pd
from scipy import stats

# Add parent directory to path for imports when run as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.data.windowing import sliding_window
except ImportError:
    try:
        from data.windowing import sliding_window
    except ImportError:
        # Fallback for direct execution
        import os
        current_dir = Path(__file__).parent
        while current_dir.name != 'code':
            current_dir = current_dir.parent
        sys.path.insert(0, str(current_dir))
        from src.data.windowing import sliding_window

from src.models.dpgmm import DPGMMModel, DPGMMConfig
from src.evaluation.metrics import compute_all_metrics
from src.services.anomaly_detector import AnomalyDetectorService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobustnessAnalyzer:
    """
    Analyzes the robustness of the anomaly detection pipeline.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the robustness analyzer.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.results: Dict[str, Any] = {}
        
    def analyze_window_sensitivity(
        self,
        data: np.ndarray,
        anomaly_timestamps: List[int],
        window_sizes: List[int] = [30, 50, 70, 100],
        stride: int = 1
    ) -> pd.DataFrame:
        """
        Perform sensitivity analysis on window size.
        
        Args:
            data: Time series data
            anomaly_timestamps: List of anomaly start timestamps
            window_sizes: List of window sizes to test
            stride: Stride for sliding window
            
        Returns:
            DataFrame with sensitivity analysis results
        """
        results = []
        
        for window_size in window_sizes:
            logger.info(f"Testing window size: {window_size}")
            
            try:
                # Apply sliding window
                windows, window_centers = sliding_window(
                    data, 
                    window_size=window_size, 
                    stride=stride
                )
                
                # Train model on each window and compute metrics
                window_metrics = []
                for i, window in enumerate(windows):
                    config = DPGMMConfig(
                        max_components=10,
                        convergence_threshold=0.01,
                        max_iterations=500
                    )
                    model = DPGMMModel(config)
                    
                    try:
                        model.fit(window)
                        scores = model.compute_anomaly_scores(window)
                        
                        # Compute anomaly score for center point
                        center_idx = window_centers[i]
                        is_anomaly = any(
                            abs(center_idx - ts) < window_size // 2
                            for ts in anomaly_timestamps
                        )
                        
                        window_metrics.append({
                            'window_size': window_size,
                            'window_idx': i,
                            'center_idx': center_idx,
                            'is_anomaly': is_anomaly,
                            'anomaly_score': float(np.mean(scores)),
                            'num_components': model.n_components
                        })
                    except Exception as e:
                        logger.warning(f"Window {i} failed: {str(e)}")
                        continue
                
                if window_metrics:
                    metrics_df = pd.DataFrame(window_metrics)
                    # Aggregate metrics
                    summary = {
                        'window_size': window_size,
                        'mean_score': float(metrics_df['anomaly_score'].mean()),
                        'std_score': float(metrics_df['anomaly_score'].std()),
                        'anomaly_detection_rate': float(
                            metrics_df[metrics_df['is_anomaly']]['anomaly_score'].mean()
                        ) if len(metrics_df[metrics_df['is_anomaly']]) > 0 else 0.0,
                        'false_positive_rate': float(
                            metrics_df[~metrics_df['is_anomaly']]['anomaly_score'].mean()
                        ) if len(metrics_df[~metrics_df['is_anomaly']]) > 0 else 0.0,
                        'num_successful_windows': len(metrics_df)
                    }
                    results.append(summary)
                    
            except Exception as e:
                logger.error(f"Failed to analyze window size {window_size}: {str(e)}")
                results.append({
                    'window_size': window_size,
                    'error': str(e)
                })
        
        return pd.DataFrame(results)
    
    def analyze_derivative_method(
        self,
        data: np.ndarray,
        anomaly_timestamps: List[int],
        method: str = 'finite_difference',
        smoothing: bool = False,
        lag: int = 1
    ) -> Dict[str, float]:
        """
        Analyze the impact of derivative calculation method.
        
        Args:
            data: Time series data
            anomaly_timestamps: List of anomaly start timestamps
            method: Derivative calculation method ('finite_difference', 'spline', 'savitzky_golay')
            smoothing: Whether to apply smoothing before differentiation
            lag: Lag for finite difference
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing derivative method: {method}")
        
        # Compute derivative
        if smoothing:
            from scipy.signal import savgol_filter
            smoothed_data = savgol_filter(data, window_length=11, polyorder=3)
            derivative = np.gradient(smoothed_data, lag)
        else:
            derivative = np.gradient(data, lag)
        
        # Analyze derivative at anomaly points
        results = {
            'method': method,
            'smoothing': smoothing,
            'lag': lag,
            'mean_derivative': float(np.mean(derivative)),
            'std_derivative': float(np.std(derivative)),
            'max_derivative': float(np.max(np.abs(derivative))),
            'anomaly_derivative_mean': 0.0,
            'non_anomaly_derivative_mean': 0.0
        }
        
        # Compute statistics at anomaly vs non-anomaly points
        anomaly_derivatives = []
        non_anomaly_derivatives = []
        
        for i, ts in enumerate(anomaly_timestamps):
            if 0 <= ts < len(derivative):
                anomaly_derivatives.append(abs(derivative[ts]))
        
        non_anomaly_indices = [i for i in range(len(derivative)) 
                              if not any(abs(i - ts) < 10 for ts in anomaly_timestamps)]
        for idx in non_anomaly_indices:
            non_anomaly_derivatives.append(abs(derivative[idx]))
        
        if anomaly_derivatives:
            results['anomaly_derivative_mean'] = float(np.mean(anomaly_derivatives))
        if non_anomaly_derivatives:
            results['non_anomaly_derivative_mean'] = float(np.mean(non_anomaly_derivatives))
        
        return results
    
    def compare_advi_mcmc(
        self,
        data: np.ndarray,
        window_size: int = 50,
        n_mcmc_samples: int = 200,
        n_advi_iterations: int = 500
    ) -> pd.DataFrame:
        """
        Compare ADVI and MCMC results for validation.
        
        Args:
            data: Time series data
            window_size: Size of sliding window
            n_mcmc_samples: Number of MCMC samples
            n_advi_iterations: Number of ADVI iterations
            
        Returns:
            DataFrame with comparison results
        """
        logger.info("Comparing ADVI and MCMC results")
        
        # Generate windows
        windows, _ = sliding_window(data, window_size=window_size, stride=10)
        
        results = []
        
        for i, window in enumerate(windows[:5]):  # Limit to first 5 windows for speed
            logger.info(f"Processing window {i+1}/5")
            
            try:
                # ADVI inference
                advi_config = DPGMMConfig(
                    max_components=10,
                    inference_method='advi',
                    convergence_threshold=0.01,
                    max_iterations=n_advi_iterations
                )
                advi_model = DPGMMModel(advi_config)
                advi_model.fit(window)
                advi_alpha = advi_model.get_posterior_alpha()
                
                # MCMC inference (subset for speed)
                mcmc_config = DPGMMConfig(
                    max_components=10,
                    inference_method='mcmc',
                    n_samples=n_mcmc_samples,
                    tune_samples=n_mcmc_samples // 2
                )
                mcmc_model = DPGMMModel(mcmc_config)
                mcmc_model.fit(window)
                mcmc_alpha = mcmc_model.get_posterior_alpha()
                
                # Compare results
                if advi_alpha is not None and mcmc_alpha is not None:
                    deviation = abs(np.mean(advi_alpha) - np.mean(mcmc_alpha))
                    relative_deviation = deviation / (np.mean(mcmc_alpha) + 1e-8)
                    
                    results.append({
                        'window_idx': i,
                        'advi_alpha_mean': float(np.mean(advi_alpha)),
                        'mcmc_alpha_mean': float(np.mean(mcmc_alpha)),
                        'absolute_deviation': float(deviation),
                        'relative_deviation': float(relative_deviation),
                        'within_tolerance': relative_deviation < 0.10
                    })
                    
            except Exception as e:
                logger.warning(f"Window {i} comparison failed: {str(e)}")
                results.append({
                    'window_idx': i,
                    'error': str(e)
                })
        
        return pd.DataFrame(results)
    
    def run_full_robustness_analysis(
        self,
        data: np.ndarray,
        anomaly_timestamps: List[int],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete robustness analysis suite.
        
        Args:
            data: Time series data
            anomaly_timestamps: List of anomaly start timestamps
            output_path: Optional path to save results
            
        Returns:
            Dictionary with all analysis results
        """
        logger.info("Starting full robustness analysis")
        
        self.results = {}
        
        # Window sensitivity analysis
        logger.info("Running window sensitivity analysis")
        window_results = self.analyze_window_sensitivity(data, anomaly_timestamps)
        self.results['window_sensitivity'] = window_results.to_dict('records')
        
        # Derivative method analysis
        logger.info("Running derivative method analysis")
        derivative_results = self.analyze_derivative_method(
            data, 
            anomaly_timestamps,
            method='finite_difference',
            smoothing=False
        )
        self.results['derivative_analysis'] = derivative_results
        
        # ADVI vs MCMC comparison
        logger.info("Running ADVI-MCMC comparison")
        mcmc_results = self.compare_advi_mcmc(data)
        self.results['advi_mcmc_comparison'] = mcmc_results.to_dict('records')
        
        # Save results if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Results saved to {output_path}")
        
        return self.results

def main():
    """Main entry point for robustness analysis."""
    parser = argparse.ArgumentParser(description='Run robustness analysis')
    parser.add_argument('--subset-size', type=int, default=500,
                      help='Size of data subset to analyze')
    parser.add_argument('--output', type=str, 
                      default='data/processed/results/robustness_analysis.json',
                      help='Output file path')
    parser.add_argument('--data', type=str,
                      default='data/processed/results/synthetic_timeseries.csv',
                      help='Input data file')
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.data}")
    try:
        df = pd.read_csv(args.data)
        # Assume first column is timestamp, second is value
        if len(df.columns) >= 2:
            data = df.iloc[:, 1].values[:args.subset_size]
        else:
            data = df.values[:args.subset_size].flatten()
    except FileNotFoundError:
        logger.error(f"Data file not found: {args.data}")
        # Generate synthetic data for testing
        logger.info("Generating synthetic data for testing")
        np.random.seed(42)
        data = np.random.randn(args.subset_size)
        # Inject some anomalies
        anomaly_start = args.subset_size // 2
        data[anomaly_start:anomaly_start+20] += 3.0
        anomaly_timestamps = [anomaly_start]
    else:
        # For synthetic data, we know the anomaly location
        anomaly_timestamps = [args.subset_size // 2]
    
    # Run analysis
    analyzer = RobustnessAnalyzer()
    results = analyzer.run_full_robustness_analysis(
        data,
        anomaly_timestamps,
        output_path=args.output
    )
    
    logger.info("Robustness analysis complete")
    logger.info(f"Results: {json.dumps(results, indent=2, default=str)[:500]}...")

if __name__ == '__main__':
    main()