import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any, Tuple, List, Optional
import os
import logging

# Ensure we can import from the project root if run as a script
# But rely on the provided API surface imports which assume src is in path
# The existing file already has these imports, we are extending it.

def get_logger(name: str = "data_generator") -> logging.Logger:
    """
    Retrieves a logger instance configured for the data generator module.
    This ensures consistent logging across the pipeline.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # If no handlers are configured yet, add a basic console handler
        # In a full pipeline, configure_logger() from src.logger should be called first.
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def generate_normal_distribution(
    n_samples: int,
    mean: float,
    std: float,
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generates a Normal distribution with specified parameters.

    Args:
        n_samples: Number of samples to generate.
        mean: Mean of the distribution.
        std: Standard deviation of the distribution.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (DataFrame, dict of ground truth parameters)
    """
    logger = get_logger()
    logger.info(f"Generating Normal distribution: n={n_samples}, mean={mean}, std={std}")

    if seed is not None:
        np.random.seed(seed)

    data = np.random.normal(loc=mean, scale=std, size=n_samples)
    df = pd.DataFrame({'value': data})

    params = {
        'distribution': 'Normal',
        'n_samples': n_samples,
        'mean': mean,
        'std': std,
        'variance': std ** 2,
        'seed': seed
    }

    logger.debug(f"Generated {len(df)} rows. Sample variance: {df['value'].var():.4f}")
    return df, params

def generate_lognormal_distribution(
    n_samples: int,
    meanlog: float,
    sdlog: float,
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generates a Log-Normal distribution.

    Args:
        n_samples: Number of samples.
        meanlog: Mean of the underlying normal distribution (log scale).
        sdlog: Standard deviation of the underlying normal distribution.
        seed: Random seed.

    Returns:
        Tuple of (DataFrame, dict of ground truth parameters)
    """
    logger = get_logger()
    logger.info(f"Generating LogNormal distribution: n={n_samples}, meanlog={meanlog}, sdlog={sdlog}")

    if seed is not None:
        np.random.seed(seed)

    data = np.random.lognormal(mean=meanlog, sigma=sdlog, size=n_samples)
    df = pd.DataFrame({'value': data})

    # Lognormal variance formula: (e^(s^2) - 1) * e^(2m + s^2)
    variance = (np.exp(sdlog**2) - 1) * np.exp(2 * meanlog + sdlog**2)

    params = {
        'distribution': 'LogNormal',
        'n_samples': n_samples,
        'meanlog': meanlog,
        'sdlog': sdlog,
        'variance': variance,
        'seed': seed
    }

    logger.debug(f"Generated {len(df)} rows. Theoretical variance: {variance:.4f}")
    return df, params

def generate_exponential_distribution(
    n_samples: int,
    scale: float,
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generates an Exponential distribution.

    Args:
        n_samples: Number of samples.
        scale: Scale parameter (1/lambda).
        seed: Random seed.

    Returns:
        Tuple of (DataFrame, dict of ground truth parameters)
    """
    logger = get_logger()
    logger.info(f"Generating Exponential distribution: n={n_samples}, scale={scale}")

    if seed is not None:
        np.random.seed(seed)

    data = np.random.exponential(scale=scale, size=n_samples)
    df = pd.DataFrame({'value': data})

    # Exponential variance: scale^2
    variance = scale ** 2

    params = {
        'distribution': 'Exponential',
        'n_samples': n_samples,
        'scale': scale,
        'variance': variance,
        'seed': seed
    }

    logger.debug(f"Generated {len(df)} rows. Theoretical variance: {variance:.4f}")
    return df, params

def generate_beta_distribution(
    n_samples: int,
    alpha: float,
    beta: float,
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generates a Beta distribution.

    Args:
        n_samples: Number of samples.
        alpha: First shape parameter.
        beta: Second shape parameter.
        seed: Random seed.

    Returns:
        Tuple of (DataFrame, dict of ground truth parameters)
    """
    logger = get_logger()
    logger.info(f"Generating Beta distribution: n={n_samples}, alpha={alpha}, beta={beta}")

    if seed is not None:
        np.random.seed(seed)

    data = np.random.beta(alpha, beta, size=n_samples)
    df = pd.DataFrame({'value': data})

    # Beta variance: (alpha * beta) / ((alpha + beta)^2 * (alpha + beta + 1))
    variance = (alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1))

    params = {
        'distribution': 'Beta',
        'n_samples': n_samples,
        'alpha': alpha,
        'beta': beta,
        'variance': variance,
        'seed': seed
    }

    logger.debug(f"Generated {len(df)} rows. Theoretical variance: {variance:.6f}")
    return df, params

def generate_gamma_distribution(
    n_samples: int,
    shape: float,
    scale: float,
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generates a Gamma distribution.

    Args:
        n_samples: Number of samples.
        shape: Shape parameter (k).
        scale: Scale parameter (theta).
        seed: Random seed.

    Returns:
        Tuple of (DataFrame, dict of ground truth parameters)
    """
    logger = get_logger()
    logger.info(f"Generating Gamma distribution: n={n_samples}, shape={shape}, scale={scale}")

    if seed is not None:
        np.random.seed(seed)

    data = np.random.gamma(shape, scale, size=n_samples)
    df = pd.DataFrame({'value': data})

    # Gamma variance: k * theta^2
    variance = shape * (scale ** 2)

    params = {
        'distribution': 'Gamma',
        'n_samples': n_samples,
        'shape': shape,
        'scale': scale,
        'variance': variance,
        'seed': seed
    }

    logger.debug(f"Generated {len(df)} rows. Theoretical variance: {variance:.4f}")
    return df, params

def save_ground_truth_params(params_list: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves ground truth parameters to a JSON file.

    Args:
        params_list: List of parameter dictionaries.
        output_path: Path to the output JSON file.
    """
    logger = get_logger()
    logger.info(f"Saving ground truth parameters to {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(params_list, f, indent=2)

    logger.info(f"Successfully saved {len(params_list)} parameter sets.")

def generate_and_save_distribution(
    generator_func,
    n_samples: int,
    output_path: Path,
    params_path: Path,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Helper to generate data, save CSV, and update params list.

    Args:
        generator_func: The generation function (e.g., generate_normal_distribution).
        n_samples: Number of samples.
        output_path: Path to save the CSV.
        params_path: Path to the JSON params file (for appending).
        seed: Random seed.
        **kwargs: Arguments passed to the generator function.

    Returns:
        The parameter dictionary for this run.
    """
    logger = get_logger()
    logger.info(f"Generating and saving distribution to {output_path}")

    df, params = generator_func(n_samples, seed=seed, **kwargs)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

    # Append to existing params file or create new
    all_params = []
    if params_path.exists():
        with open(params_path, 'r') as f:
            try:
                all_params = json.load(f)
            except json.JSONDecodeError:
                all_params = []

    all_params.append(params)

    with open(params_path, 'w') as f:
        json.dump(all_params, f, indent=2)

    logger.info(f"Updated ground truth parameters in {params_path}")
    return params

def inject_outliers(
    df: pd.DataFrame,
    contamination_rate: float,
    outlier_method: str = 'cauchy',
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Injects outliers into a dataframe.

    Args:
        df: Input dataframe with a 'value' column.
        contamination_rate: Fraction of rows to replace with outliers (0.0 to 1.0).
        outlier_method: Method for generating outliers ('cauchy' or 'extreme').
        seed: Random seed.

    Returns:
        Tuple of (modified DataFrame, injection profile dict)
    """
    logger = get_logger()
    logger.info(f"Injecting outliers at rate {contamination_rate} using method '{outlier_method}'")

    if seed is not None:
        np.random.seed(seed)

    n_samples = len(df)
    n_outliers = int(n_samples * contamination_rate)

    if n_outliers == 0:
        logger.warning("Calculated 0 outliers to inject. Check contamination rate and sample size.")
        return df, {'n_outliers': 0, 'method': outlier_method, 'rate': contamination_rate}

    # Select random indices to replace
    outlier_indices = np.random.choice(n_samples, size=n_outliers, replace=False)

    if outlier_method == 'cauchy':
        # Cauchy distribution has heavy tails
        # Use a scale that ensures values are far from typical data
        # We estimate the range of current data to set a sensible scale
        data_mean = df['value'].mean()
        data_std = df['value'].std()
        scale = data_std * 10  # Scale factor for Cauchy

        logger.debug(f"Using Cauchy distribution with scale={scale} centered near {data_mean}")
        outlier_values = np.random.standard_cauchy(n_outliers) * scale + data_mean

    elif outlier_method == 'extreme':
        # Extreme scaling: multiply existing values by a large factor or add large offset
        max_val = df['value'].max()
        min_val = df['value'].min()
        data_range = max_val - min_val
        
        # Generate values far outside the range
        # Positive outliers: max + (random * range * factor)
        # Negative outliers: min - (random * range * factor)
        factor = 10.0
        signs = np.random.choice([-1, 1], size=n_outliers)
        magnitudes = np.random.rand(n_outliers) * data_range * factor
        outlier_values = (signs * magnitudes) + (data_mean if 'data_mean' in locals() else 0)
        
        # Ensure they are actually extreme
        # If signs are mixed, some might be inside. Force them out.
        for i, idx in enumerate(outlier_indices):
            if signs[i] == 1:
                outlier_values[i] = max_val + magnitudes[i]
            else:
                outlier_values[i] = min_val - magnitudes[i]

    else:
        raise ValueError(f"Unknown outlier method: {outlier_method}")

    df_out = df.copy()
    df_out.loc[outlier_indices, 'value'] = outlier_values

    profile = {
        'n_outliers': n_outliers,
        'contamination_rate': contamination_rate,
        'method': outlier_method,
        'seed': seed,
        'original_mean': df['value'].mean(),
        'original_std': df['value'].std(),
        'new_mean': df_out['value'].mean(),
        'new_std': df_out['value'].std()
    }

    logger.info(f"Injected {n_outliers} outliers. New mean: {profile['new_mean']:.4f}, New std: {profile['new_std']:.4f}")
    
    # Log sample outlier values for debugging
    if len(outlier_values) > 0:
        logger.debug(f"Sample outlier values: {outlier_values[:5]}")

    return df_out, profile

def main():
    """
    Main entry point for data generation tasks.
    This function demonstrates the workflow of generating synthetic data,
    saving ground truth, and injecting outliers with logging.
    """
    logger = get_logger()
    logger.info("Starting data generation pipeline")

    # Define output paths
    base_path = Path("data/raw")
    state_path = Path("state")
    processed_path = Path("data/processed")

    base_path.mkdir(parents=True, exist_ok=True)
    state_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)

    params_file = state_path / "synthetic_params.json"
    
    # Clear previous params if they exist to ensure clean run for this demo
    if params_file.exists():
        logger.info(f"Removing existing params file: {params_file}")
        params_file.unlink()

    distributions = [
        {
            'name': 'normal',
            'func': generate_normal_distribution,
            'args': {'mean': 0.0, 'std': 1.0},
            'file': 'synthetic_clean_normal.csv'
        },
        {
            'name': 'lognormal',
            'func': generate_lognormal_distribution,
            'args': {'meanlog': 0.0, 'sdlog': 0.5},
            'file': 'synthetic_clean_lognormal.csv'
        },
        {
            'name': 'exponential',
            'func': generate_exponential_distribution,
            'args': {'scale': 1.0},
            'file': 'synthetic_clean_exponential.csv'
        },
        {
            'name': 'beta',
            'func': generate_beta_distribution,
            'args': {'alpha': 2.0, 'beta': 5.0},
            'file': 'synthetic_clean_beta.csv'
        },
        {
            'name': 'gamma',
            'func': generate_gamma_distribution,
            'args': {'shape': 2.0, 'scale': 1.0},
            'file': 'synthetic_clean_gamma.csv'
        }
    ]

    for dist in distributions:
        output_path = base_path / dist['file']
        try:
            generate_and_save_distribution(
                generator_func=dist['func'],
                n_samples=1000,
                output_path=output_path,
                params_path=params_file,
                seed=42,
                **dist['args']
            )
            logger.info(f"Successfully generated {dist['name']} distribution")
        except Exception as e:
            logger.error(f"Failed to generate {dist['name']} distribution: {e}", exc_info=True)
            raise

    logger.info("Synthetic clean data generation complete.")

    # Now demonstrate outlier injection
    logger.info("Starting outlier injection demonstration")
    
    # Load one of the generated files to inject outliers
    sample_file = base_path / 'synthetic_clean_normal.csv'
    if sample_file.exists():
        df_clean = pd.read_csv(sample_file)
        
        # Inject outliers
        df_contaminated, profile = inject_outliers(
            df_clean, 
            contamination_rate=0.1, 
            outlier_method='cauchy', 
            seed=42
        )
        
        # Save contaminated data
        contaminated_path = processed_path / 'contaminated_normal.csv'
        df_contaminated.to_csv(contaminated_path, index=False)
        
        # Save injection profile
        profile_path = processed_path / 'injection_profile.json'
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
        
        logger.info(f"Injected outliers saved to {contaminated_path}")
        logger.info(f"Injection profile saved to {profile_path}")
    else:
        logger.error(f"Sample file not found: {sample_file}")

    logger.info("Data generation pipeline finished successfully.")

if __name__ == "__main__":
    main()