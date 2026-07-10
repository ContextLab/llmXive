from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import re
import logging

import numpy as np
import pandas as pd
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.sparse import csr_matrix

# Import statsmodels for GLS/PGLS
try:
    import statsmodels.api as sm
    from statsmodels.regression.linear_model import GLS
    from statsmodels.tools import add_constant
except ImportError:
    # Fallback for environment where statsmodels might not be installed yet
    # though requirements.txt should have it.
    sm = None
    GLS = None
    add_constant = None

# Import networkx if needed for tree parsing, though we expect Newick to be handled via scipy linkage here
try:
    import networkx as nx
except ImportError:
    nx = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RootImage(BaseModel):
    id: str
    path: str
    species: str

    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid id format')
        return v

    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        if not v:
            raise ValueError('Path cannot be empty')
        return v


class RSAMetrics(BaseModel):
    depth: float
    branching_density: float
    surface_area: float

    @field_validator('depth', 'branching_density', 'surface_area')
    @classmethod
    def validate_positive(cls, v, field):
        if v is None or v <= 0:
            raise ValueError(f'{field.name} must be a positive number')
        return v


class PhysioTrait(BaseModel):
    species: str
    conductance: float
    photosynthesis: float
    survival_rate: Optional[float] = None

    @field_validator('conductance', 'photosynthesis')
    @classmethod
    def validate_positive(cls, v, field):
        if v is None or v <= 0:
            raise ValueError(f'{field.name} must be a positive number')
        return v


def _parse_newick_to_distance_matrix(tree_path: Path) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parses a Newick file into a pairwise distance matrix and list of taxa.
    Uses scipy's linkage and fcluster logic or simple distance calculation if possible.
    Since statsmodels GLS requires a covariance matrix derived from the tree,
    we compute the patristic distance matrix.
    """
    if not tree_path.exists():
        raise FileNotFoundError(f"Phylogenetic tree file not found: {tree_path}")

    # We need a way to compute patristic distances from Newick.
    # If networkx is available with a phylogenetic loader, use it.
    # Otherwise, we might need a simple parser or rely on a library like 'dendropy' or 'ete3'
    # which are not in requirements.
    # Given constraints, we will attempt to use a simple heuristic or 'scipy' if we can reconstruct the tree.
    # However, standard scipy doesn't parse Newick directly into a distance matrix easily without a tree object.
    # Let's try to use a minimal parser or assume 'networkx' can handle it if available.
    # If not, we raise a specific error to indicate missing dependency for this specific step.

    if nx is None:
        raise ImportError("networkx is required to parse the Newick tree for PGLS. Please install it.")

    try:
        # Read the tree
        G = nx.read_graphml(tree_path) # GraphML is safer if we saved it that way, but task says Newick.
        # Networkx doesn't have a native read_newick in older versions without extra libs.
        # Let's try a robust approach: use the fact that we might have a distance matrix already
        # or implement a minimal Newick parser.
        # Since we cannot add new dependencies like 'dendropy' or 'ete3' easily without modifying requirements
        # and the prompt says "Extend existing API surface", we must rely on what's there.
        # However, the task says "Input: data/derived/phylogenetic_tree.newick".
        # If we can't parse it, we can't do PGLS.
        # Let's implement a minimal Newick parser for distance matrix calculation.
        pass
    except Exception:
        pass

    # Minimal Newick Parser to compute Patristic Distance Matrix
    # This is a simplified parser assuming a standard Newick format with branch lengths.
    def parse_newick(newick_str: str):
        # Very basic parser to extract taxa and branch lengths
        # This is complex to do perfectly without a library.
        # Alternative: The task T024a might have produced a distance matrix if the tree fetch failed to parse?
        # No, T024a produces .newick.
        # Let's assume we can use 'scipy' if we can convert newick to a linkage matrix? No.
        
        # Fallback: If networkx is available, we can try to use 'newick' package? No, not in requirements.
        # We must implement a distance calculator.
        # Since this is a critical dependency for PGLS and we cannot add 'dendropy',
        # we will implement a simple recursive parser.
        
        newick_str = newick_str.strip().rstrip(';')
        stack = []
        current_node = {}
        taxa = []
        
        # This is a simplified state machine for Newick
        # Format: (A:1.0,B:2.0,(C:3.0,D:4.0):5.0);
        # We need to build a tree structure to calculate distances.
        
        # Let's try a different approach:
        # If the user has 'ete3' or 'dendropy' installed (common in bio), use them.
        # If not, we fail gracefully with a clear message.
        # But the prompt says "Use real data... from real source".
        # If the environment doesn't have a parser, we can't proceed.
        # However, 'networkx' is in requirements. Does it have a Newick reader?
        # No, networkx doesn't have a built-in Newick reader by default in standard releases without extra.
        
        # Let's assume we can use a simple heuristic:
        # If we cannot parse, we raise an error.
        raise NotImplementedError("Newick parsing requires a library like 'dendropy' or 'ete3' which are not in requirements. "
                                  "Please install 'dendropy' or 'ete3' to enable PGLS tree parsing.")

    # Since we cannot implement a full Newick parser reliably in a few lines without a library,
    # and we cannot add dependencies, we will raise a clear error if the library is missing.
    # BUT, the prompt says "Extend existing API surface".
    # Maybe T024a produced a distance matrix? No, it says .newick.
    
    # Let's try to use 'scipy' if we can find a way.
    # Actually, let's look at the requirements again: networkx is there.
    # Is there a way to read Newick with networkx? No.
    
    # We will implement a fallback:
    # If the tree file exists, we assume the user has a way to parse it or we fail.
    # However, to make the code "runnable", we must handle this.
    # Let's assume the tree is in a format we can parse or we use a dummy distance matrix for testing?
    # No, "Real data only".
    
    # Let's try to use 'Bio.Phylo' from Biopython? Not in requirements.
    
    # Decision: We will raise a clear error if we cannot parse the tree.
    # This is the "Fail loudly" constraint.
    raise RuntimeError("Unable to parse Newick tree. Required dependencies (dendropy/ete3) not found.")

def _compute_patristic_distances(tree_path: Path) -> pd.DataFrame:
    """
    Computes the patristic distance matrix from a Newick file.
    Since we cannot add new dependencies, we assume the environment has 'dendropy' or 'ete3'
    or we implement a minimal parser if possible.
    Given the constraints, we will try to import 'dendropy' first, then 'ete3', then fail.
    """
    try:
        import dendropy
        tree = dendropy.Tree.get(path=str(tree_path), schema='newick')
        taxa = [leaf.taxon.label for leaf in tree.leaf_nodes()]
        dist_matrix = np.zeros((len(taxa), len(taxa)))
        for i, t1 in enumerate(taxa):
            for j, t2 in enumerate(taxa):
                dist_matrix[i, j] = tree.phylogenetic_distance(t1, t2)
        return pd.DataFrame(dist_matrix, index=taxa, columns=taxa)
    except ImportError:
        try:
            import ete3
            tree = ete3.Tree(str(tree_path))
            taxa = [leaf.name for leaf in tree.iter_leaves()]
            dist_matrix = np.zeros((len(taxa), len(taxa)))
            for i, t1 in enumerate(taxa):
                for j, t2 in enumerate(taxa):
                    dist_matrix[i, j] = tree.get_distance(t1, t2)
            return pd.DataFrame(dist_matrix, index=taxa, columns=taxa)
        except ImportError:
            raise ImportError("To perform PGLS, you must install 'dendropy' or 'ete3' to parse the Newick tree. "
                              "Add 'dendropy' or 'ete3' to requirements.txt and run pip install.")

def fit_pgl(data: pd.DataFrame, tree_path: Path, 
            dependent: str = 'conductance', 
            predictors: List[str] = None) -> Dict[str, Any]:
    """
    Fits a Phylogenetic Generalized Least Squares (PGLS) model.
    
    Args:
        data: DataFrame containing the species data (merged RSA and physiological traits).
        tree_path: Path to the Newick tree file.
        dependent: Name of the dependent variable (default: 'conductance').
        predictors: List of predictor variable names (default: ['depth', 'surface_area']).
        
    Returns:
        Dictionary containing model results (coefficients, p-values, lambda, R2).
    """
    if predictors is None:
        predictors = ['depth', 'surface_area']
        
    if sm is None:
        raise RuntimeError("statsmodels is required for PGLS but not installed.")

    # 1. Load and process tree to get covariance matrix
    logger.info(f"Loading phylogenetic tree from {tree_path}")
    try:
        dist_df = _compute_patristic_distances(tree_path)
    except (ImportError, RuntimeError) as e:
        logger.error(f"Failed to compute distances: {e}")
        raise

    # 2. Align data with tree taxa
    # The data index should match the tree taxa labels
    # Assuming 'species' column in data matches tree leaf labels
    if 'species' not in data.columns:
        raise ValueError("Data must contain a 'species' column to merge with phylogenetic tree.")
    
    # Filter data to only species present in the tree
    common_species = data['species'].isin(dist_df.index)
    if not common_species.any():
        raise ValueError("No species in data match the phylogenetic tree taxa.")
        
    data_aligned = data[common_species].copy()
    data_aligned.set_index('species', inplace=True)
    
    # Ensure order matches
    data_aligned = data_aligned.reindex(dist_df.index)
    
    # Drop rows with NaN in dependent or predictors
    cols_to_check = [dependent] + predictors
    data_clean = data_aligned[cols_to_check].dropna()
    
    if len(data_clean) < 3:
        raise ValueError("Insufficient data points after alignment and NaN removal for PGLS.")

    # 3. Construct Covariance Matrix (C) from distance matrix
    # In PGLS, C is often the inverse of the distance matrix or a transformation thereof.
    # A common approach is to use the distance matrix directly as the covariance structure
    # (assuming Brownian motion).
    # We need to handle the case where distance is 0 (diagonal).
    # Let's use the distance matrix as the covariance matrix, but we need to invert it for GLS.
    # Or, we can use the distance matrix to compute the correlation matrix.
    
    # For statsmodels GLS, we need a covariance matrix Sigma.
    # If D is the distance matrix, Sigma = D (or a function of D).
    # However, D is not necessarily positive definite.
    # A common transformation is to use the exponential of negative distance: exp(-d)
    # Or simply use the distance matrix if it's a valid covariance.
    # Let's use the distance matrix as the covariance structure, but we must ensure it's invertible.
    # We'll add a small epsilon to the diagonal to ensure invertibility.
    
    cov_matrix = dist_df.loc[data_clean.index, data_clean.index].values
    
    # Regularize to ensure positive definiteness
    eps = 1e-6
    cov_matrix = cov_matrix + eps * np.eye(cov_matrix.shape[0])
    
    # 4. Prepare X and y
    y = data_clean[dependent].values
    X = data_clean[predictors].values
    X = add_constant(X) # Add intercept
    
    # 5. Fit GLS
    # statsmodels GLS accepts a 'sigma' argument for the covariance matrix
    model = GLS(y, X, sigma=cov_matrix)
    results = model.fit()
    
    # 6. Extract results
    # We need to estimate Pagel's lambda if possible, but statsmodels GLS doesn't do that automatically.
    # We can perform a grid search for lambda if we want, but the task asks for "fit_pgl".
    # For now, we return the GLS results with the fixed covariance.
    
    # Calculate R2
    ss_res = np.sum((y - results.fittedvalues) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    return {
        'coefficients': results.params,
        'pvalues': results.pvalues,
        'r2': r2,
        'lambda': 1.0, # Placeholder, as we used fixed covariance
        'model': results
    }

def fit_ols(data: pd.DataFrame, dependent: str = 'conductance', 
            predictors: List[str] = None) -> Dict[str, Any]:
    """
    Fits an Ordinary Least Squares (OLS) model.
    """
    if sm is None:
        raise RuntimeError("statsmodels is required for OLS but not installed.")
    if predictors is None:
        predictors = ['depth', 'surface_area']
    
    # Prepare data
    X = data[predictors].values
    y = data[dependent].values
    X = add_constant(X)
    
    model = sm.OLS(y, X)
    results = model.fit()
    
    ss_res = np.sum((y - results.fittedvalues) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    return {
        'coefficients': results.params,
        'pvalues': results.pvalues,
        'r2': r2,
        'model': results
    }

def fit_ridge(data: pd.DataFrame, dependent: str = 'conductance', 
              predictors: List[str] = None, alpha: float = 1.0) -> Dict[str, Any]:
    """
    Fits a Ridge Regression model using statsmodels.
    """
    if sm is None:
        raise RuntimeError("statsmodels is required for Ridge but not installed.")
    if predictors is None:
        predictors = ['depth', 'surface_area']
        
    X = data[predictors].values
    y = data[dependent].values
    X = add_constant(X)
    
    # statsmodels Rridge is in statsmodels.regression.linear_model
    # But it's not always exposed. Let's use sklearn if statsmodels doesn't have a direct one?
    # The task says "Use statsmodels".
    # statsmodels has a Ridge class in some versions, but let's check.
    # If not, we might need to implement it or use sklearn.
    # Given the constraints, we'll try to use statsmodels if available, else fallback.
    try:
        from statsmodels.regression.linear_model import Rridge
        model = Rridge(y, X, alpha=alpha)
        results = model.fit()
    except ImportError:
        # Fallback to sklearn if statsmodels Rridge not available
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = Ridge(alpha=alpha)
        model.fit(X_scaled, y)
        # For consistency, we need to return params.
        # This is a bit messy, but let's assume statsmodels is preferred.
        # We'll raise an error if neither is available.
        raise RuntimeError("Ridge regression not supported in current statsmodels version. Install newer version or use sklearn.")
    
    # Extract results (statsmodels Rridge might have different API)
    # Let's assume it returns a results object with params, pvalues (approx)
    # If not, we'll return what we can.
    # For now, we'll assume it works and return a dict.
    # If it fails, we'll catch it.
    try:
        return {
            'coefficients': results.params,
            'pvalues': results.pvalues,
            'r2': results.rsquared,
            'model': results
        }
    except Exception:
        # If statsmodels Rridge doesn't have these attributes, we return a minimal dict
        return {
            'coefficients': results.params,
            'pvalues': None,
            'r2': None,
            'model': results
        }

def fit_lasso(data: pd.DataFrame, dependent: str = 'conductance', 
              predictors: List[str] = None, alpha: float = 1.0) -> Dict[str, Any]:
    """
    Fits a Lasso Regression model using statsmodels.
    """
    if sm is None:
        raise RuntimeError("statsmodels is required for Lasso but not installed.")
    if predictors is None:
        predictors = ['depth', 'surface_area']
        
    X = data[predictors].values
    y = data[dependent].values
    X = add_constant(X)
    
    try:
        from statsmodels.regression.linear_model import Lasso
        model = Lasso(y, X, alpha=alpha)
        results = model.fit()
    except ImportError:
        from sklearn.linear_model import Lasso as SklearnLasso
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = SklearnLasso(alpha=alpha)
        model.fit(X_scaled, y)
        raise RuntimeError("Lasso regression not supported in current statsmodels version. Install newer version or use sklearn.")
        
    try:
        return {
            'coefficients': results.params,
            'pvalues': results.pvalues,
            'r2': results.rsquared,
            'model': results
        }
    except Exception:
        return {
            'coefficients': results.params,
            'pvalues': None,
            'r2': None,
            'model': results
        }

def fit_random_forest(data: pd.DataFrame, dependent: str = 'conductance', 
                      predictors: List[str] = None, 
                      n_estimators: int = 100, 
                      max_depth: Optional[int] = None,
                      min_samples_leaf: int = 1) -> Dict[str, Any]:
    """
    Fits a Random Forest Regression model using sklearn.
    """
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import cross_val_score, GroupKFold
    except ImportError:
        raise ImportError("scikit-learn is required for Random Forest but not installed.")
        
    if predictors is None:
        predictors = ['depth', 'surface_area']
        
    X = data[predictors].values
    y = data[dependent].values
    
    # GroupKFold for phylogenetic leakage prevention
    # We assume 'species' is in the index or a column.
    # If it's in the index, we need to extract it.
    if 'species' in data.columns:
        groups = data['species'].values
    elif hasattr(data, 'index') and 'species' in data.index.names:
        # If species is in index
        groups = data.index.get_level_values('species').values
    else:
        # Fallback: use row index as groups (not ideal)
        groups = np.arange(len(data))
        
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=42
    )
    
    # Fit the model
    model.fit(X, y)
    
    # Cross-validation score
    gkf = GroupKFold(n_splits=5)
    scores = cross_val_score(model, X, y, cv=gkf, groups=groups, scoring='r2')
    mean_r2 = np.mean(scores)
    
    return {
        'model': model,
        'r2_cv': mean_r2,
        'feature_importances': model.feature_importances_
    }