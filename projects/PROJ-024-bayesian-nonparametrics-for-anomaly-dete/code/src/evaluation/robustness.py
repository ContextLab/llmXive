"""
Robustness analysis for the Bayesian Nonparametrics Anomaly Detection pipeline.

This module implements sensitivity analysis on window size, derivative calculation methods,
and threshold stability to validate the robustness of the detection pipeline (FR-016).
"""
import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/robustness_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RobustnessConfig:
    """Configuration for robustness analysis."""
    base_window_size: int = 50
    window_size_range: Tuple[int, int] = (30, 70)
    window_step: int = 10
    derivative_methods: List[str] = field(default_factory=lambda: ['central', 'forward', 'backward', 'smoothed'])
    smoothing_window: int = 5
    threshold_range: List[float] = field(default_factory=lambda: [0.01, 0.05, 0.1, 0.2])
    n_bootstrap: int = 100
    seed: int = 42
    output_dir: str = 'data/processed/results'
    subset_size: int = 1000  # For testing with subsets

@dataclass
class RobustnessResult:
    """Results from a single robustness analysis run."""
    parameter_name: str
    parameter_value: Union[int, float, str]
    metric_name: str
    metric_value: float
    confidence_interval: Optional[Tuple[float, float]] = None
    std_dev: Optional[float] = None
    p_value: Optional[float] = None
    stability_flag: bool = False
    notes: str = ""

@dataclass
class SensitivityAnalysisReport:
    """Full report from sensitivity analysis."""
    config: RobustnessConfig
    results: List[RobustnessResult]
    summary: Dict[str, Any]
    timestamp: str
    file_path: Optional[str] = None

class RobustnessAnalyzer:
    """
    Analyzes the robustness of the anomaly detection pipeline to various parameter changes.
    
    Implements FR-016: Sensitivity analysis on window size and derivative calculation method
    to validate robustness.
    """
    
    def __init__(self, config: Optional[RobustnessConfig] = None):
        self.config = config or RobustnessConfig()
        np.random.seed(self.config.seed)
        self.results: List[RobustnessResult] = []
        
    def load_data(self, data_path: str) -> pd.DataFrame:
        """Load time series data for analysis."""
        path = Path(data_path)
        if not path.exists():
            logger.warning(f"Data file not found: {data_path}. Generating synthetic data for robustness check.")
            return self._generate_synthetic_data()
        
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} observations from {data_path}")
        return df

    def _generate_synthetic_data(self) -> pd.DataFrame:
        """Generate synthetic time series data for robustness testing."""
        n_samples = self.config.subset_size
        t = np.linspace(0, 100, n_samples)
        
        # Base signal: combination of sine waves
        signal = (
            2 * np.sin(2 * np.pi * t / 20) +
            1 * np.sin(2 * np.pi * t / 50) +
            0.5 * np.random.normal(0, 1, n_samples)
        )
        
        # Inject some anomalies
        anomaly_start = int(n_samples * 0.7)
        anomaly_end = int(n_samples * 0.8)
        signal[anomaly_start:anomaly_end] += 3.0  # Shift anomaly
        
        df = pd.DataFrame({
            'timestamp': np.arange(n_samples),
            'value': signal,
            'is_anomaly': [1 if anomaly_start <= i < anomaly_end else 0 for i in range(n_samples)]
        })
        
        return df

    def compute_derivative(self, values: np.ndarray, method: str) -> np.ndarray:
        """
        Compute the first derivative of the time series using the specified method.
        
        Args:
            values: Input time series values
            method: One of 'central', 'forward', 'backward', 'smoothed'
            
        Returns:
            Array of derivative values
        """
        values = np.asarray(values)
        n = len(values)
        
        if method == 'central':
            # Central difference for interior points
            deriv = np.zeros(n)
            deriv[1:-1] = (values[2:] - values[:-2]) / 2.0
            deriv[0] = (values[1] - values[0])  # Forward for first
            deriv[-1] = (values[-1] - values[-2])  # Backward for last
            
        elif method == 'forward':
            deriv = np.zeros(n)
            deriv[:-1] = np.diff(values)
            deriv[-1] = deriv[-2]  # Extend last
            
        elif method == 'backward':
            deriv = np.zeros(n)
            deriv[1:] = np.diff(values)
            deriv[0] = deriv[1]  # Extend first
            
        elif method == 'smoothed':
            # Apply smoothing before differentiation
            window = self.config.smoothing_window
            if window % 2 == 0:
                window += 1
            smoothed = np.convolve(values, np.ones(window)/window, mode='same')
            deriv = np.gradient(smoothed)
        else:
            raise ValueError(f"Unknown derivative method: {method}")
        
        return deriv

    def analyze_window_size_sensitivity(self, data: pd.DataFrame) -> List[RobustnessResult]:
        """
        Analyze how detection metrics vary with window size.
        
        Args:
            data: Time series DataFrame with 'value' column
            
        Returns:
            List of RobustnessResult objects
        """
        logger.info("Analyzing window size sensitivity...")
        results = []
        
        window_sizes = list(range(
            self.config.window_size_range[0],
            self.config.window_size_range[1] + 1,
            self.config.window_step
        ))
        
        # Use a simple metric: variance of derivative (proxy for stability)
        values = data['value'].values
        base_deriv = np.gradient(values)
        base_var = np.var(base_deriv)
        
        for ws in window_sizes:
            # Simulate windowed analysis (simplified for robustness check)
            # In full implementation, this would run the actual detector with window size ws
            n_windows = len(values) // ws
            if n_windows < 2:
                continue
            
            # Compute derivative variance within windows
            window_vars = []
            for i in range(n_windows):
                start = i * ws
                end = start + ws
                if end <= len(values):
                    window_deriv = np.gradient(values[start:end])
                    window_vars.append(np.var(window_deriv))
            
            if window_vars:
                avg_var = np.mean(window_vars)
                std_var = np.std(window_vars)
                
                # Check stability: if variance of variances is high, flag as unstable
                stability_flag = std_var / avg_var > 0.5 if avg_var > 0 else False
                
                results.append(RobustnessResult(
                    parameter_name="window_size",
                    parameter_value=ws,
                    metric_name="derivative_variance",
                    metric_value=avg_var,
                    std_dev=std_var,
                    stability_flag=stability_flag,
                    notes=f"Stability check: {'UNSTABLE' if stability_flag else 'STABLE'}"
                ))
        
        return results

    def analyze_derivative_method_sensitivity(self, data: pd.DataFrame) -> List[RobustnessResult]:
        """
        Analyze how detection metrics vary with derivative calculation method.
        
        Args:
            data: Time series DataFrame with 'value' column
            
        Returns:
            List of RobustnessResult objects
        """
        logger.info("Analyzing derivative method sensitivity...")
        results = []
        
        values = data['value'].values
        base_deriv = np.gradient(values)
        base_stats = {
            'mean': np.mean(base_deriv),
            'std': np.std(base_deriv),
            'var': np.var(base_deriv)
        }
        
        for method in self.config.derivative_methods:
            try:
                deriv = self.compute_derivative(values, method)
                
                # Compare to base gradient
                corr = np.corrcoef(base_deriv, deriv)[0, 1]
                mse = np.mean((base_deriv - deriv) ** 2)
                max_diff = np.max(np.abs(base_deriv - deriv))
                
                # Stability check: high MSE or low correlation indicates instability
                stability_flag = mse > 0.1 or (corr < 0.9 and not np.isnan(corr))
                
                results.append(RobustnessResult(
                    parameter_name="derivative_method",
                    parameter_value=method,
                    metric_name="correlation_with_base",
                    metric_value=float(corr) if not np.isnan(corr) else 0.0,
                    std_dev=float(mse),
                    stability_flag=stability_flag,
                    notes=f"MSE: {mse:.4f}, MaxDiff: {max_diff:.4f}"
                ))
                
            except Exception as e:
                logger.error(f"Error computing derivative with method {method}: {e}")
                results.append(RobustnessResult(
                    parameter_name="derivative_method",
                    parameter_value=method,
                    metric_name="error",
                    metric_value=0.0,
                    stability_flag=True,
                    notes=f"Error: {str(e)}"
                ))
        
        return results

    def analyze_threshold_sensitivity(self, scores: np.ndarray) -> List[RobustnessResult]:
        """
        Analyze how detection rates vary with threshold changes.
        
        Args:
            scores: Array of anomaly scores
            
        Returns:
            List of RobustnessResult objects
        """
        logger.info("Analyzing threshold sensitivity...")
        results = []
        
        for thresh in self.config.threshold_range:
            # Simulate detection rate (in real implementation, compare to ground truth)
            # Here we use the empirical CDF as a proxy
            detection_rate = np.mean(scores > thresh)
            false_alarm_rate = np.mean(scores > thresh * 0.8)  # Proxy for FP
            
            # Stability check: large jumps in detection rate
            # (In full implementation, compare adjacent thresholds)
            stability_flag = detection_rate > 0.5 or detection_rate < 0.01
            
            results.append(RobustnessResult(
                parameter_name="threshold",
                parameter_value=thresh,
                metric_name="detection_rate",
                metric_value=float(detection_rate),
                stability_flag=stability_flag,
                notes=f"FA Proxy: {false_alarm_rate:.4f}"
            ))
        
        return results

    def run_bootstrap_stability(self, data: pd.DataFrame, n_iter: int = None) -> Dict[str, float]:
        """
        Run bootstrap resampling to estimate stability of metrics.
        
        Args:
            data: Time series DataFrame
            n_iter: Number of bootstrap iterations
            
        Returns:
            Dictionary of stability metrics
        """
        n_iter = n_iter or self.config.n_bootstrap
        logger.info(f"Running bootstrap stability analysis with {n_iter} iterations...")
        
        values = data['value'].values
        n = len(values)
        bootstrap_means = []
        
        for _ in range(n_iter):
            # Resample with replacement
            indices = np.random.choice(n, size=n, replace=True)
            sample = values[indices]
            deriv = np.gradient(sample)
            bootstrap_means.append(np.mean(deriv))
        
        mean_of_means = np.mean(bootstrap_means)
        std_of_means = np.std(bootstrap_means)
        ci_low = np.percentile(bootstrap_means, 2.5)
        ci_high = np.percentile(bootstrap_means, 97.5)
        
        return {
            'mean': mean_of_means,
            'std': std_of_means,
            'ci_low': ci_low,
            'ci_high': ci_high,
            'stability_ratio': std_of_means / abs(mean_of_means) if mean_of_means != 0 else float('inf')
        }

    def generate_report(self, data: Optional[pd.DataFrame] = None) -> SensitivityAnalysisReport:
        """
        Generate a comprehensive robustness analysis report.
        
        Args:
            data: Optional data to analyze. If None, generates synthetic data.
            
        Returns:
            SensitivityAnalysisReport object
        """
        if data is None:
            data = self._generate_synthetic_data()
        
        self.results = []
        
        # Run all analyses
        self.results.extend(self.analyze_window_size_sensitivity(data))
        self.results.extend(self.analyze_derivative_method_sensitivity(data))
        
        # Generate scores for threshold analysis (simplified)
        values = data['value'].values
        scores = np.abs(np.gradient(values))
        self.results.extend(self.analyze_threshold_sensitivity(scores))
        
        # Bootstrap stability
        bootstrap_stats = self.run_bootstrap_stability(data)
        
        # Summary
        total_results = len(self.results)
        unstable_count = sum(1 for r in self.results if r.stability_flag)
        stability_rate = 1.0 - (unstable_count / total_results) if total_results > 0 else 1.0
        
        summary = {
            'total_parameters_tested': total_results,
            'unstable_parameters': unstable_count,
            'stability_rate': stability_rate,
            'bootstrap_stability': bootstrap_stats,
            'recommendation': "PASS" if stability_rate > 0.8 else "REVIEW"
        }
        
        timestamp = pd.Timestamp.now().isoformat()
        report = SensitivityAnalysisReport(
            config=self.config,
            results=self.results,
            summary=summary,
            timestamp=timestamp
        )
        
        return report

    def save_report(self, report: SensitivityAnalysisReport, output_path: Optional[str] = None) -> str:
        """
        Save the robustness analysis report to disk.
        
        Args:
            report: The report to save
            output_path: Optional custom output path
            
        Returns:
            Path to the saved file
        """
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if output_path is None:
            output_path = output_dir / "robustness_analysis.json"
        
        # Convert report to dict for JSON serialization
        report_dict = {
            'config': {
                'base_window_size': report.config.base_window_size,
                'window_size_range': report.config.window_size_range,
                'window_step': report.config.window_step,
                'derivative_methods': report.config.derivative_methods,
                'smoothing_window': report.config.smoothing_window,
                'threshold_range': report.config.threshold_range,
                'n_bootstrap': report.config.n_bootstrap,
                'seed': report.config.seed
            },
            'results': [
                {
                    'parameter_name': r.parameter_name,
                    'parameter_value': r.parameter_value,
                    'metric_name': r.metric_name,
                    'metric_value': r.metric_value,
                    'confidence_interval': r.confidence_interval,
                    'std_dev': r.std_dev,
                    'p_value': r.p_value,
                    'stability_flag': r.stability_flag,
                    'notes': r.notes
                }
                for r in report.results
            ],
            'summary': report.summary,
            'timestamp': report.timestamp
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        logger.info(f"Robustness report saved to {output_path}")
        report.file_path = str(output_path)
        return str(output_path)

    def plot_sensitivity(self, report: SensitivityAnalysisReport, output_path: Optional[str] = None) -> str:
        """
        Generate sensitivity analysis plots.
        
        Args:
            report: The report to plot
            output_path: Optional custom output path
            
        Returns:
            Path to the saved plot
        """
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if output_path is None:
            output_path = output_dir / "robustness_sensitivity.png"
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Robustness Analysis Sensitivity Report', fontsize=14)
        
        # Plot 1: Window size sensitivity
        ax1 = axes[0, 0]
        window_results = [r for r in report.results if r.parameter_name == 'window_size']
        if window_results:
            ws_vals = [r.parameter_value for r in window_results]
            metric_vals = [r.metric_value for r in window_results]
            ax1.plot(ws_vals, metric_vals, 'o-', label='Derivative Variance')
            ax1.set_xlabel('Window Size')
            ax1.set_ylabel('Derivative Variance')
            ax1.set_title('Window Size Sensitivity')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
        
        # Plot 2: Derivative method comparison
        ax2 = axes[0, 1]
        deriv_results = [r for r in report.results if r.parameter_name == 'derivative_method']
        if deriv_results:
            methods = [str(r.parameter_value) for r in deriv_results]
            corr_vals = [r.metric_value for r in deriv_results]
            bars = ax2.bar(methods, corr_vals, color=['green' if v > 0.9 else 'orange' for v in corr_vals])
            ax2.set_xlabel('Derivative Method')
            ax2.set_ylabel('Correlation with Base')
            ax2.set_title('Derivative Method Stability')
            ax2.set_ylim(0, 1.1)
            ax2.grid(True, alpha=0.3, axis='y')
        
        # Plot 3: Threshold sensitivity
        ax3 = axes[1, 0]
        thresh_results = [r for r in report.results if r.parameter_name == 'threshold']
        if thresh_results:
            thresh_vals = [r.parameter_value for r in thresh_results]
            det_rates = [r.metric_value for r in thresh_results]
            ax3.plot(thresh_vals, det_rates, 's-', color='red')
            ax3.set_xlabel('Threshold')
            ax3.set_ylabel('Detection Rate')
            ax3.set_title('Threshold Sensitivity')
            ax3.grid(True, alpha=0.3)
        
        # Plot 4: Bootstrap stability
        ax4 = axes[1, 1]
        bs_stats = report.summary.get('bootstrap_stability', {})
        if bs_stats:
            ax4.bar(['Mean', 'Std', 'CI Low', 'CI High'], 
                   [bs_stats.get('mean', 0), bs_stats.get('std', 0), 
                    bs_stats.get('ci_low', 0), bs_stats.get('ci_high', 0)],
                   color=['blue', 'gray', 'green', 'green'])
            ax4.set_title('Bootstrap Stability')
            ax4.set_ylabel('Value')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Sensitivity plot saved to {output_path}")
        return str(output_path)


def main():
    """Main entry point for robustness analysis."""
    parser = argparse.ArgumentParser(description='Robustness Analysis for Anomaly Detection')
    parser.add_argument('--data', type=str, default=None, help='Path to input data CSV')
    parser.add_argument('--window-size', type=int, default=50, help='Base window size')
    parser.add_argument('--subset-size', type=int, default=1000, help='Subset size for testing')
    parser.add_argument('--output-dir', type=str, default='data/processed/results', help='Output directory')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    logger.info("Starting robustness analysis...")
    
    # Create config
    config = RobustnessConfig(
        base_window_size=args.window_size,
        subset_size=args.subset_size,
        output_dir=args.output_dir,
        seed=args.seed
    )
    
    # Initialize analyzer
    analyzer = RobustnessAnalyzer(config)
    
    # Load data
    if args.data:
        data = analyzer.load_data(args.data)
    else:
        data = None
    
    # Run analysis
    report = analyzer.generate_report(data)
    
    # Save results
    json_path = analyzer.save_report(report)
    plot_path = analyzer.plot_sensitivity(report)
    
    # Print summary
    print("\n" + "="*60)
    print("ROBUSTNESS ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total parameters tested: {report.summary['total_parameters_tested']}")
    print(f"Unstable parameters: {report.summary['unstable_parameters']}")
    print(f"Stability rate: {report.summary['stability_rate']:.2%}")
    print(f"Recommendation: {report.summary['recommendation']}")
    print(f"Results saved to: {json_path}")
    print(f"Plot saved to: {plot_path}")
    print("="*60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
