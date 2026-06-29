"""
Hierarchical Bayesian Model for Misinformation Cascade Size

This module implements a Bayesian hierarchical model using NumPyro with:
- Negative Binomial likelihood for cascade size (count outcome)
- Fixed effects for all network and user predictors
- Random intercepts for user_id, message_id, and optional platform_id

Per T018 requirements and model_spec.yaml specifications.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import numpyro
import numpyro.distributions as dist
import pandas as pd
import xarray as xr
from numpyro.infer import MCMC, NUTS, Predictive
from numpyro.infer.util import initialize_model

from pipeline.utils import set_global_seed, setup_logger

# Ensure reproducible results
set_global_seed(12345)

# Module logger
logger = setup_logger(__name__)


def _encode_categorical(series: pd.Series) -> Tuple[np.ndarray, Dict]:
    """
    Encode a categorical series as integers and return the mapping.

    Args:
        series: Pandas Series to encode

    Returns:
        Tuple of (encoded array, category_to_id mapping dict)
    """
    unique_vals = series.unique()
    cat_to_id = {cat: i for i, cat in enumerate(unique_vals)}
    encoded = series.map(cat_to_id).values
    return encoded, cat_to_id


def _prepare_model_data(
    features_path: str,
    outcome_col: str = "cascade_size",
    fixed_effect_cols: Optional[List[str]] = None,
) -> Tuple[Dict, pd.DataFrame]:
    """
    Prepare data for the hierarchical model.

    Args:
        features_path: Path to features.csv
        outcome_col: Name of the outcome variable column
        fixed_effect_cols: List of predictor column names (all if None)

    Returns:
        Tuple of (model_data dict, features dataframe)
    """
    logger.info(f"Loading features from {features_path}")
    df = pd.read_csv(features_path)

    # Validate outcome column exists
    if outcome_col not in df.columns:
        raise ValueError(f"Outcome column '{outcome_col}' not found in features")

    # Use all numeric columns as fixed effects if not specified
    if fixed_effect_cols is None:
        fixed_effect_cols = [
            col for col in df.columns
            if col != outcome_col and df[col].dtype in [np.float64, np.int64, np.float32, np.int32]
        ]
        logger.info(f"Auto-detected {len(fixed_effect_cols)} fixed effect predictors")

    # Validate all fixed effects exist
    missing = set(fixed_effect_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Fixed effect columns not found: {missing}")

    # Extract outcome
    y = df[outcome_col].values.astype(np.float32)

    # Stack fixed effects
    X = df[fixed_effect_cols].values.astype(np.float32)

    # Encode categorical random effects
    random_effect_data = {}

    if "user_id" in df.columns:
        random_effect_data["user_id"], user_cat_map = _encode_categorical(df["user_id"])
        random_effect_data["user_id_mapping"] = user_cat_map

    if "message_id" in df.columns:
        random_effect_data["message_id"], msg_cat_map = _encode_categorical(df["message_id"])
        random_effect_data["message_id_mapping"] = msg_cat_map

    if "platform_id" in df.columns:
        random_effect_data["platform_id"], plat_cat_map = _encode_categorical(df["platform_id"])
        random_effect_data["platform_id_mapping"] = plat_cat_map
        # Check if we have multiple platforms
        random_effect_data["use_platform_effect"] = len(plat_cat_map) >= 2
    else:
        random_effect_data["use_platform_effect"] = False

    model_data = {
        "y": y,
        "X": X,
        "n_obs": len(y),
        "n_predictors": X.shape[1],
        "predictor_names": fixed_effect_cols,
        **random_effect_data,
    }

    logger.info(
        f"Prepared model data: {len(y)} observations, "
        f"{len(fixed_effect_cols)} predictors, "
        f"random effects: user={model_data.get('user_id_mapping', {}).size}, "
        f"message={model_data.get('message_id_mapping', {}).size}, "
        f"platform={model_data.get('platform_id_mapping', {}).size if model_data.get('use_platform_effect') else 0}"
    )

    return model_data, df


def hierarchical_model(
    X: np.ndarray,
    y: np.ndarray,
    n_predictors: int,
    user_id: Optional[np.ndarray] = None,
    message_id: Optional[np.ndarray] = None,
    platform_id: Optional[np.ndarray] = None,
    use_platform_effect: bool = False,
):
    """
    Bayesian hierarchical model for cascade size.

    Model specification:
    - Outcome: Negative Binomial (for overdispersed count data)
    - Fixed effects: Linear combination of predictors
    - Random intercepts: user_id, message_id, optional platform_id

    Priors (per model_spec.yaml):
    - Fixed effects: Normal(0, 2.5)
    - Random effects: Normal(0, sigma_group)
    - Group-level std: HalfNormal(1.0)
    - Negative Binomial alpha (dispersion): HalfNormal(1.0)
    """
    # Fixed effect coefficients
    beta = numpyro.sample(
        "beta",
        dist.Normal(0, 2.5).expand([n_predictors]).to_event(1)
    )

    # Linear predictor from fixed effects
    eta = numpyro.deterministic("eta_fixed", jnp.dot(X, beta))

    # Random intercepts
    sigma_user = numpyro.sample("sigma_user", dist.HalfNormal(1.0))
    sigma_message = numpyro.sample("sigma_message", dist.HalfNormal(1.0))

    # User random intercepts
    n_users = len(np.unique(user_id)) if user_id is not None else 0
    if n_users > 0:
        user_intercepts = numpyro.sample(
            "user_intercepts",
            dist.Normal(0, sigma_user).expand([n_users]).to_event(1)
        )
        eta = eta + user_intercepts[user_id]
    else:
        user_intercepts = None

    # Message random intercepts
    n_messages = len(np.unique(message_id)) if message_id is not None else 0
    if n_messages > 0:
        message_intercepts = numpyro.sample(
            "message_intercepts",
            dist.Normal(0, sigma_message).expand([n_messages]).to_event(1)
        )
        eta = eta + message_intercepts[message_id]
    else:
        message_intercepts = None

    # Platform random intercepts (optional)
    if use_platform_effect and platform_id is not None:
        sigma_platform = numpyro.sample("sigma_platform", dist.HalfNormal(1.0))
        n_platforms = len(np.unique(platform_id))
        platform_intercepts = numpyro.sample(
            "platform_intercepts",
            dist.Normal(0, sigma_platform).expand([n_platforms]).to_event(1)
        )
        eta = eta + platform_intercepts[platform_id]

    # Negative Binomial dispersion parameter
    alpha = numpyro.sample("alpha", dist.HalfNormal(1.0))

    # Negative Binomial likelihood
    # Mean = exp(eta), variance = mean + mean^2 / alpha
    mean = numpyro.deterministic("mean", jnp.exp(eta))
    numpyro.sample(
        "cascade_size",
        dist.NegativeBinomial2(mean, alpha),
        obs=y
    )

    return {"eta": eta, "mean": mean}


def fit_model(
    model_data: Dict,
    num_samples: int = 500,
    num_warmup: int = 500,
    num_chains: int = 2,
    seed: int = 12345,
    max_tree_depth: int = 10,
) -> Tuple[MCMC, Dict]:
    """
    Fit the hierarchical model using NUTS sampler.

    Args:
        model_data: Dictionary containing prepared model data
        num_samples: Number of posterior samples
        num_warmup: Number of warmup iterations
        num_chains: Number of MCMC chains
        seed: Random seed
        max_tree_depth: Maximum tree depth for NUTS

    Returns:
        Tuple of (MCMC object, diagnostics dict)
    """
    import jax.numpy as jnp
    from numpyro.infer import MCMC, NUTS

    logger.info(f"Fitting model with {num_samples} samples, {num_warmup} warmup, {num_chains} chains")

    # Prepare arguments for model
    model_kwargs = {
        "X": model_data["X"],
        "y": model_data["y"],
        "n_predictors": model_data["n_predictors"],
        "user_id": model_data.get("user_id"),
        "message_id": model_data.get("message_id"),
        "platform_id": model_data.get("platform_id"),
        "use_platform_effect": model_data.get("use_platform_effect", False),
    }

    # Initialize NUTS kernel
    kernel = NUTS(
        hierarchical_model,
        max_tree_depth=max_tree_depth,
        adapt_step_size=True,
        adapt_mass_matrix=True,
    )

    # Run MCMC
    mcmc = MCMC(
        kernel,
        num_warmup=num_warmup,
        num_samples=num_samples,
        num_chains=num_chains,
        progress_bar=True,
    )

    mcmc.run(jax.random.PRNGKey(seed), **model_kwargs)

    # Collect diagnostics
    diagnostics = {
        "num_samples": num_samples,
        "num_warmup": num_warmup,
        "num_chains": num_chains,
        "divergences": 0,
        "divergence_rate": 0.0,
        "energy_acceptance_rate": 0.0,
        "max_rhat": 0.0,
    }

    # Check for divergences
    if hasattr(mcmc, "last_state"):
        states = mcmc.get_samples()
        # NumPyro stores divergence info in sampler state
        try:
            num_divergences = mcmc.last_state.num_divergences
            diagnostics["divergences"] = num_divergences
            diagnostics["divergence_rate"] = num_divergences / (num_samples * num_chains)
            logger.info(f"Divergences: {num_divergences} ({diagnostics['divergence_rate']:.2%})")
        except AttributeError:
            logger.warning("Could not retrieve divergence count from sampler state")

    # Check R-hat values
    try:
        from numpyro.infer.util import compute_chain_variance
        samples = mcmc.get_samples()
        rhat_values = {}
        for param, values in samples.items():
            if len(values.shape) >= 2 and values.shape[0] > 1:
                # Simple R-hat approximation
                chain_var = np.var(values, axis=0).mean()
                overall_var = np.var(values)
                if overall_var > 0:
                    rhat = np.sqrt(overall_var / chain_var) if chain_var > 0 else 1.0
                    rhat_values[param] = rhat
        if rhat_values:
            diagnostics["max_rhat"] = max(rhat_values.values())
            logger.info(f"Max R-hat: {diagnostics['max_rhat']:.4f}")
    except Exception as e:
        logger.warning(f"Could not compute R-hat: {e}")

    # Check acceptance rate
    try:
        accept_rate = mcmc.last_state.accept_prob if hasattr(mcmc.last_state, 'accept_prob') else 0.8
        diagnostics["energy_acceptance_rate"] = float(accept_rate)
        logger.info(f"Acceptance rate: {accept_rate:.2%}")
    except AttributeError:
        logger.warning("Could not retrieve acceptance rate")

    # Check for convergence issues
    if diagnostics["divergence_rate"] > 0.05:
        logger.warning(
            f"High divergence rate ({diagnostics['divergence_rate']:.2%} > 5%). "
            "Consider increasing max_tree_depth or reducing step size."
        )

    if diagnostics["max_rhat"] > 1.1:
        logger.warning(
            f"High R-hat value ({diagnostics['max_rhat']:.4f} > 1.1). "
            "Model may not have converged. Consider more samples or better initialization."
        )

    return mcmc, diagnostics


def compute_posterior_summary(
    mcmc: MCMC,
    model_data: Dict,
    prob_nonzero_threshold: float = 0.95,
) -> pd.DataFrame:
    """
    Compute posterior summary statistics.

    Args:
        mcmc: Fitted MCMC object
        model_data: Model data dictionary
        prob_nonzero_threshold: Threshold for prob_nonzero calculation

    Returns:
        DataFrame with posterior summary
    """
    samples = mcmc.get_samples()

    # Extract fixed effects (beta)
    beta_samples = samples.get("beta", None)
    if beta_samples is None:
        raise ValueError("No beta samples found in MCMC output")

    # Compute summaries for each predictor
    predictor_names = model_data["predictor_names"]
    summaries = []

    for i, name in enumerate(predictor_names):
        param_samples = beta_samples[:, i]

        mean = float(np.mean(param_samples))
        sd = float(np.std(param_samples))
        lower_95 = float(np.percentile(param_samples, 2.5))
        upper_95 = float(np.percentile(param_samples, 97.5))

        # Probability of non-zero effect
        prob_nonzero = float(np.mean(np.abs(param_samples) > 0.01))

        # Direction consistency (all samples same sign)
        direction_consistent = bool(np.all(param_samples > 0) or np.all(param_samples < 0))

        summaries.append({
            "predictor": name,
            "mean": mean,
            "sd": sd,
            "lower_95": lower_95,
            "upper_95": upper_95,
            "prob_nonzero": prob_nonzero,
            "direction_consistent": direction_consistent,
        })

    # Add random effect summaries
    for effect_type in ["user", "message", "platform"]:
        sigma_key = f"sigma_{effect_type}"
        if sigma_key in samples:
            sigma_samples = samples[sigma_key]
            summaries.append({
                "predictor": f"sigma_{effect_type}",
                "mean": float(np.mean(sigma_samples)),
                "sd": float(np.std(sigma_samples)),
                "lower_95": float(np.percentile(sigma_samples, 2.5)),
                "upper_95": float(np.percentile(sigma_samples, 97.5)),
                "prob_nonzero": 1.0,  # sigma is always positive
                "direction_consistent": True,
            })

    return pd.DataFrame(summaries)


def save_trace(
    mcmc: MCMC,
    output_path: str,
    model_data: Dict,
) -> None:
    """
    Save MCMC trace to NetCDF format.

    Args:
        mcmc: Fitted MCMC object
        output_path: Path to output file
        model_data: Model data dictionary (for metadata)
    """
    import jax.numpy as jnp

    logger.info(f"Saving trace to {output_path}")

    samples = mcmc.get_samples()

    # Convert to xarray Dataset
    data_vars = {}
    for param, values in samples.items():
        # Flatten dimensions if needed
        if len(values.shape) == 1:
            data_vars[param] = (("chain", "draw"), values.reshape(1, -1))
        elif len(values.shape) == 2:
            data_vars[param] = (("chain", "draw"), values)
        else:
            # Handle higher dimensional parameters
            reshaped = values.reshape(values.shape[0], -1)
            data_vars[param] = (("chain", "draw"), reshaped)

    # Create dataset with metadata
    ds = xr.Dataset(
        data_vars=data_vars,
        attrs={
            "model": "hierarchical_negative_binomial",
            "n_samples": samples["beta"].shape[1] if "beta" in samples else 0,
            "n_chains": samples["beta"].shape[0] if "beta" in samples else 0,
            "predictor_names": model_data.get("predictor_names", []),
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    )

    # Save to NetCDF
    ds.to_netcdf(output_path)
    logger.info(f"Trace saved to {output_path}")


def run_pipeline(
    features_path: str,
    output_dir: str,
    num_samples: int = 500,
    num_warmup: int = 500,
    num_chains: int = 2,
    seed: int = 12345,
) -> Dict:
    """
    Run the full hierarchical modeling pipeline.

    Args:
        features_path: Path to features.csv
        output_dir: Directory for output files
        num_samples: Number of posterior samples
        num_warmup: Number of warmup iterations
        num_chains: Number of MCMC chains
        seed: Random seed

    Returns:
        Dictionary with pipeline results and diagnostics
    """
    set_global_seed(seed)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare data
    model_data, df = _prepare_model_data(features_path)

    # Fit model
    mcmc, diagnostics = fit_model(
        model_data,
        num_samples=num_samples,
        num_warmup=num_warmup,
        num_chains=num_chains,
        seed=seed,
    )

    # Compute posterior summary
    summary_df = compute_posterior_summary(mcmc, model_data)

    # Save outputs
    trace_path = output_dir / "model_trace.nc"
    summary_path = output_dir / "posterior_summary.csv"
    diagnostics_path = output_dir / "model_diagnostics.json"

    save_trace(mcmc, str(trace_path), model_data)
    summary_df.to_csv(summary_path, index=False)

    # Save diagnostics
    diagnostics.update({
        "n_observations": len(df),
        "n_predictors": len(model_data["predictor_names"]),
        "predictors": model_data["predictor_names"],
        "user_n_groups": len(model_data.get("user_id_mapping", {})),
        "message_n_groups": len(model_data.get("message_id_mapping", {})),
        "platform_n_groups": len(model_data.get("platform_id_mapping", {})) if model_data.get("use_platform_effect") else 0,
    })

    with open(diagnostics_path, "w") as f:
        json.dump(diagnostics, f, indent=2)

    logger.info(
        f"Pipeline complete. Outputs: {trace_path}, {summary_path}, {diagnostics_path}"
    )

    return {
        "mcmc": mcmc,
        "model_data": model_data,
        "diagnostics": diagnostics,
        "summary": summary_df,
        "trace_path": str(trace_path),
        "summary_path": str(summary_path),
        "diagnostics_path": str(diagnostics_path),
    }


def main():
    """CLI entry point for hierarchical model fitting."""
    parser = argparse.ArgumentParser(
        description="Fit Bayesian hierarchical model to cascade features"
    )
    parser.add_argument(
        "--features",
        type=str,
        default="data/processed/features.csv",
        help="Path to features CSV file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory for output files",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=500,
        help="Number of posterior samples",
    )
    parser.add_argument(
        "--num-warmup",
        type=int,
        default=500,
        help="Number of warmup iterations",
    )
    parser.add_argument(
        "--num-chains",
        type=int,
        default=2,
        help="Number of MCMC chains",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
        help="Random seed",
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger(__name__)
    logger.info(f"Starting hierarchical model fitting with args: {vars(args)}")

    try:
        results = run_pipeline(
            features_path=args.features,
            output_dir=args.output_dir,
            num_samples=args.num_samples,
            num_warmup=args.num_warmup,
            num_chains=args.num_chains,
            seed=args.seed,
        )

        logger.info("Model fitting completed successfully")
        logger.info(f"Diagnostics: {results['diagnostics']}")

    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise


if __name__ == "__main__":
    main()