import json
import logging
import os
import pickle
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import networkx as nx
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold
from sklearn.inspection import permutation_importance

from config import get_data_processed, get_results_root, ensure_directories_exist
from utils.logger import get_logger
from model_training import load_feature_matrix, load_model

logger = get_logger(__name__)

def load_ecosystem_ids(feature_df: pd.DataFrame) -> List[str]:
    """
    Extract unique ecosystem IDs from the feature matrix.
    Assumes the feature matrix has a column 'ecosystem_id' added during preprocessing.
    """
    if 'ecosystem_id' not in feature_df.columns:
        raise ValueError("Feature matrix must contain 'ecosystem_id' column for LOEO.")
    return feature_df['ecosystem_id'].unique().tolist()

def run_loeo_cv(
    feature_df: pd.DataFrame,
    model_class: type = RandomForestClassifier,
    model_params: Optional[Dict[str, Any]] = None
) -> Dict[str, List[float]]:
    """
    Run Leave-One-Ecosystem-Out cross-validation.
    Trains on N-1 ecosystems, tests on the held-out one.
    """
    if model_params is None:
        model_params = {'n_estimators': 100, 'random_state': 42}

    ecosystem_ids = load_ecosystem_ids(feature_df)
    metrics = {'auc': [], 'precision': [], 'recall': []}

    logger.info(f"Starting LOEO CV with {len(ecosystem_ids)} ecosystems.")

    for holdout_id in ecosystem_ids:
        logger.info(f"Training on all except {holdout_id}, testing on {holdout_id}")

        # Split data
        train_df = feature_df[feature_df['ecosystem_id'] != holdout_id].copy()
        test_df = feature_df[feature_df['ecosystem_id'] == holdout_id].copy()

        if train_df.empty or test_df.empty:
            logger.warning(f"Skipping {holdout_id} due to empty train/test split.")
            continue

        X_train = train_df.drop(columns=['link_label', 'ecosystem_id'])
        y_train = train_df['link_label']
        X_test = test_df.drop(columns=['link_label', 'ecosystem_id'])
        y_test = test_df['link_label']

        # Train
        model = model_class(**model_params)
        model.fit(X_train, y_train)

        # Predict
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)

        # Metrics
        try:
            auc = roc_auc_score(y_test, y_pred_proba)
            metrics['auc'].append(auc)
        except ValueError:
            logger.warning(f"Could not compute AUC for {holdout_id} (single class).")

        try:
            prec = precision_score(y_test, y_pred, zero_division=0)
            metrics['precision'].append(prec)
        except Exception as e:
            logger.warning(f"Precision error for {holdout_id}: {e}")

        try:
            rec = recall_score(y_test, y_pred, zero_division=0)
            metrics['recall'].append(rec)
        except Exception as e:
            logger.warning(f"Recall error for {holdout_id}: {e}")

    return metrics

def compare_loeo_to_cv(loeo_metrics: Dict[str, List[float]], cv_baseline: float) -> Dict[str, Any]:
    """
    Compare LOEO results to the internal 5-fold CV baseline.
    """
    loeo_auc_mean = np.mean(loeo_metrics['auc']) if loeo_metrics['auc'] else 0.0
    diff = loeo_auc_mean - cv_baseline

    return {
        'loeo_auc_mean': loeo_auc_mean,
        'cv_baseline_auc': cv_baseline,
        'difference': diff,
        'generalization_status': 'Pass' if diff > -0.05 else 'Warning: Generalization drop > 5%'
    }

def trait_shuffled_null(
    feature_df: pd.DataFrame,
    model: RandomForestClassifier,
    n_iterations: int = 100
) -> float:
    """
    Compute AUC under a Trait-Shuffled Null Model.
    Shuffles trait values across rows while keeping labels and structure intact.
    """
    logger.info(f"Running Trait-Shuffled Null Model ({n_iterations} iterations).")

    # Separate features and labels
    X = feature_df.drop(columns=['link_label', 'ecosystem_id'])
    y = feature_df['link_label']

    # Fit model on original data first to get baseline structure (optional, but standard)
    # However, the null hypothesis is that traits have no predictive power.
    # We shuffle X columns and re-evaluate the SAME trained model structure or retrain?
    # Standard practice: Retrain on shuffled data to see if model learns anything from noise.
    # Or: Apply shuffled features to the existing model?
    # Task T036b implies comparing against the main model's efficacy.
    # Let's retrain on shuffled data to see if AUC drops to chance.

    auc_scores = []
    trait_cols = X.columns.tolist()

    for i in range(n_iterations):
        X_shuffled = X.copy()
        for col in trait_cols:
            X_shuffled[col] = np.random.permutation(X_shuffled[col].values)

        # Simple train/test split for speed in null model (or use full CV if time permits)
        # Using a single holdout for speed in null model loop
        split_idx = int(len(X_shuffled) * 0.8)
        X_train, X_test = X_shuffled.iloc[:split_idx], X_shuffled.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        if y_train.nunique() < 2 or y_test.nunique() < 2:
            continue

        model_null = RandomForestClassifier(n_estimators=10, random_state=i) # Small model for speed
        model_null.fit(X_train, y_train)
        y_pred_proba = model_null.predict_proba(X_test)[:, 1]

        try:
            auc = roc_auc_score(y_test, y_pred_proba)
            auc_scores.append(auc)
        except ValueError:
            continue

    if not auc_scores:
        logger.warning("No valid iterations for trait-shuffled null.")
        return 0.5

    return np.mean(auc_scores)

def degree_preserving_null(
    feature_df: pd.DataFrame,
    interaction_matrix: Optional[pd.DataFrame] = None,
    n_iterations: int = 100
) -> float:
    """
    Implement Degree-Preserving Null Model for network topology comparison.
    
    This function constructs a null network by rewiring the interaction edges
    while preserving the degree distribution of both plant and pollinator nodes.
    It then calculates the AUC of a model trained on this null topology 
    (assuming traits are mapped to the new edges randomly or the model fails to learn).
    
    Since the model predicts links based on traits, and the null model scrambles the 
    link existence (Y) while keeping the node set (and thus trait availability) the same,
    we evaluate if the model can distinguish the real topology from the null topology.
    
    However, the standard interpretation in this context (T039) is:
    "Compare the observed network structure against a degree-preserving null model."
    This usually involves calculating a network metric (like modularity or clustering) 
    or training a link predictor on the null graph.
    
    Here, we interpret it as: Generate a null set of links (Y_null) that preserves
    the degree sequence of the observed bipartite graph. Then, evaluate the model's
    ability to predict these null links (which should be low) or compute a metric
    of the discrepancy.
    
    Given the pipeline context (AUC focus), we will:
    1. Reconstruct the bipartite graph from the feature matrix (positive links).
    2. Generate a degree-preserving randomized graph (Marsaglia/switching algorithm).
    3. Create a 'null' feature matrix where positive links are replaced by the 
       randomized edges (and negative samples adjusted accordingly).
    4. Evaluate the model on this null topology (expecting AUC ~ 0.5 or lower if traits 
       don't explain the null structure).
    """
    logger.info(f"Running Degree-Preserving Null Model ({n_iterations} iterations).")

    # 1. Reconstruct Bipartite Graph
    # We need the raw interactions to build the graph. 
    # Assuming feature_df has 'plant_id', 'pollinator_id', 'ecosystem_id', 'link_label'
    if 'plant_id' not in feature_df.columns or 'pollinator_id' not in feature_df.columns:
        logger.error("Feature matrix missing 'plant_id' or 'pollinator_id' for graph construction.")
        return 0.0

    # Filter for positive links to build the graph
    pos_links = feature_df[feature_df['link_label'] == 1]
    
    if pos_links.empty:
        logger.warning("No positive links found for degree-preserving null.")
        return 0.0

    # Group by ecosystem if multiple exist, but LOEO usually handles one at a time.
    # We'll process the first ecosystem found or aggregate if necessary.
    # For simplicity in this null model, we aggregate all positive links or pick one.
    # Let's pick the first ecosystem to avoid complexity of multi-ecosystem graph merging.
    ecosystems = pos_links['ecosystem_id'].unique()
    if len(ecosystems) > 1:
        logger.warning("Multiple ecosystems found. Using first one for null model graph.")
    
    target_eco = ecosystems[0]
    eco_links = pos_links[pos_links['ecosystem_id'] == target_eco]

    # Create bipartite graph
    G = nx.Graph()
    plants = eco_links['plant_id'].unique()
    pollinators = eco_links['pollinator_id'].unique()
    
    # Add nodes with bipartite attribute
    G.add_nodes_from(plants, bipartite=0)
    G.add_nodes_from(pollinators, bipartite=1)
    G.add_edges_from(eco_links[['plant_id', 'pollinator_id']].itertuples(index=False, name=None))

    # 2. Generate Degree-Preserving Null Graphs
    # Using nx.bipartite.random_graph is not degree preserving.
    # We use the configuration model or edge switching.
    # For bipartite graphs, we can use the "switching" method on the adjacency matrix
    # or use the `bipartite` module if available, but standard `nx` has limited direct support.
    # We will implement a simple edge-switching algorithm for bipartite graphs.
    # Switch two edges (u, v) and (x, y) to (u, y) and (x, v) if they don't exist.
    
    null_auc_scores = []
    
    # Pre-compute trait features for the nodes to map to edges later
    # We need to map node traits to the new edges.
    # In a real scenario, the traits are properties of the species.
    # When we create a new edge (u, y), we use traits of u and y.
    
    # Get trait dataframe for this ecosystem
    eco_features = feature_df[feature_df['ecosystem_id'] == target_eco].copy()
    # We need a mapping from node ID to its trait vector (averaged if multiple interactions)
    # But traits are usually species-level. Let's assume unique per species.
    # We'll create a node-trait map.
    node_traits = {}
    trait_cols = [c for c in eco_features.columns if c not in ['link_label', 'ecosystem_id', 'plant_id', 'pollinator_id']]
    
    for _, row in eco_features.iterrows():
        # Plant traits
        if row['plant_id'] not in node_traits:
            node_traits[row['plant_id']] = {c: row[c] for c in trait_cols}
        # Pollinator traits
        if row['pollinator_id'] not in node_traits:
            node_traits[row['pollinator_id']] = {c: row[c] for c in trait_cols}

    for i in range(n_iterations):
        # Clone graph
        G_null = G.copy()
        
        # Perform edge switching
        # We need to perform enough switches to randomize. 
        # Number of edges * 10 is a common heuristic.
        num_edges = G_null.number_of_edges()
        n_switches = num_edges * 10
        
        edges_list = list(G_null.edges())
        if len(edges_list) < 2:
            continue
        
        for _ in range(n_switches):
            # Pick two random edges
            e1 = random.choice(edges_list)
            e2 = random.choice(edges_list)
            
            u, v = e1
            x, y = e2
            
            # Ensure they are not sharing a node and the swap is valid (bipartite constraint)
            # In bipartite: u, x are plants; v, y are pollinators (or vice versa)
            # We assume the graph is bipartite and edges are (plant, pollinator)
            if u == x or v == y:
                continue
            
            # Check if new edges exist
            if G_null.has_edge(u, y) or G_null.has_edge(x, v):
                continue
            
            # Swap
            G_null.remove_edge(u, v)
            G_null.remove_edge(x, y)
            G_null.add_edge(u, y)
            G_null.add_edge(x, v)
            
            # Update edges_list for next iteration (simplified: rebuild occasionally or just use set)
            # For strict correctness, we should update the list, but for speed in null model, 
            # we just rely on random.choice from the current state if we re-evaluate edges_list.
            # Actually, `edges_list` is stale. Let's just use the graph's edges iterator.
            edges_list = list(G_null.edges())

        # 3. Construct Null Feature Matrix
        # Create a dataframe with the new edges as positive labels
        null_edges = list(G_null.edges())
        null_df_list = []
        
        for u, v in null_edges:
            # u is plant, v is pollinator (based on construction)
            # Check bipartite sets to be sure
            if G.nodes[u]['bipartite'] == 0:
                plant, pollinator = u, v
            else:
                plant, pollinator = v, u
            
            # Fetch traits
            plant_traits = node_traits.get(plant, {})
            pollinator_traits = node_traits.get(pollinator, {})
            
            # Combine traits (simple concatenation logic - assuming symmetric or specific order)
            # In the real matrix, traits are columns. We need to construct the row.
            # We assume the model expects a flat vector of [plant_traits, pollinator_traits, effort]
            # Since we don't have the exact schema here, we assume the feature_df columns 
            # are consistent and we can reconstruct the row by looking up values.
            # This is a simplification: we need to map the trait columns to the node traits.
            # We'll just create a row with 0s and fill known traits.
            
            row_data = {'ecosystem_id': target_eco, 'plant_id': plant, 'pollinator_id': pollinator, 'link_label': 1}
            for col in trait_cols:
                # Try to get value from plant or pollinator. 
                # If the trait is plant-specific, it's in plant_traits.
                # If pollinator-specific, in pollinator_traits.
                # If shared (e.g. 'color' might be flower color), we need to know.
                # Heuristic: If plant has it, use it. Else pollinator.
                val = plant_traits.get(col, pollinator_traits.get(col, 0))
                row_data[col] = val
            
            null_df_list.append(row_data)
        
        if not null_df_list:
            continue

        null_df = pd.DataFrame(null_df_list)
        
        # We need to compare the model's performance on this null topology.
        # But the model was trained on REAL topology.
        # The null hypothesis: The model's predictions are based on traits.
        # If we scramble the topology but keep traits, the model should still predict 
        # based on traits. The "Degree-Preserving Null" usually tests if the network 
        # structure itself (beyond traits) explains the links.
        # Here, we calculate the AUC of the model on the NULL edges vs random negatives.
        # But the model expects a specific feature space.
        
        # Let's simplify: Calculate the AUC of the model on the null graph edges (as positives)
        # and a set of random non-edges (negatives) from the null graph.
        
        # Generate negatives for null graph
        all_nodes_plants = [n for n, d in G_null.nodes(data=True) if d.get('bipartite') == 0]
        all_nodes_pollinators = [n for n, d in G_null.nodes(data=True) if d.get('bipartite') == 1]
        
        # Create a set of existing null edges for fast lookup
        null_edges_set = set(null_edges)
        
        # Sample negatives
        negatives = []
        attempts = 0
        while len(negatives) < len(null_df_list) and attempts < 10000:
            p1 = random.choice(all_nodes_plants)
            p2 = random.choice(all_nodes_pollinators)
            if (p1, p2) not in null_edges_set and (p2, p1) not in null_edges_set:
                negatives.append((p1, p2))
            attempts += 1
        
        if len(negatives) < len(null_df_list):
            # Pad with duplicates or skip
            pass
        
        # Construct full null dataset (Positives + Negatives)
        # We need to generate feature rows for negatives too
        null_dataset_list = []
        
        for p, q in null_edges:
             # Add positive
             if G.nodes[p]['bipartite'] == 0:
                 plant, pollinator = p, q
             else:
                 plant, pollinator = q, p
             
             row_data = {'ecosystem_id': target_eco, 'plant_id': plant, 'pollinator_id': pollinator, 'link_label': 1}
             for col in trait_cols:
                 val = node_traits.get(plant, {}).get(col, node_traits.get(pollinator, {}).get(col, 0))
                 row_data[col] = val
             null_dataset_list.append(row_data)
        
        for p, q in negatives[:len(null_edges)]:
             row_data = {'ecosystem_id': target_eco, 'plant_id': p, 'pollinator_id': q, 'link_label': 0}
             for col in trait_cols:
                 val = node_traits.get(p, {}).get(col, node_traits.get(q, {}).get(col, 0))
                 row_data[col] = val
             null_dataset_list.append(row_data)
         
        null_full_df = pd.DataFrame(null_dataset_list)
        
        # Prepare X, y
        X_null = null_full_df.drop(columns=['link_label', 'ecosystem_id', 'plant_id', 'pollinator_id'])
        y_null = null_full_df['link_label']
        
        if y_null.nunique() < 2:
            continue
        
        # Evaluate the ORIGINAL model on this null data
        # The model was trained on real data. We test if it predicts the null edges.
        # If the null edges are random (degree preserving), the model should not predict them well.
        # This tests if the model learned specific topology or just traits.
        
        try:
            y_pred_proba = model.predict_proba(X_null)[:, 1]
            auc = roc_auc_score(y_null, y_pred_proba)
            null_auc_scores.append(auc)
        except ValueError:
            continue

    if not null_auc_scores:
        logger.warning("No valid iterations for degree-preserving null.")
        return 0.5

    return np.mean(null_auc_scores)

def calculate_cv_baseline(feature_df: pd.DataFrame, model: RandomForestClassifier) -> float:
    """
    Calculate the baseline AUC from the internal 5-fold CV.
    """
    # Re-run a simple 5-fold CV on the full data to get the baseline
    # (Assuming model is already trained, but we need the CV score from training)
    # If the model was trained with CV, the score should be available.
    # Here we just compute it fresh for consistency.
    X = feature_df.drop(columns=['link_label', 'ecosystem_id'])
    y = feature_df['link_label']
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = []
    
    for train_idx, test_idx in skf.split(X, y):
        X_tr, X_te = X.iloc[train_idx], X.iloc[test_idx]
        y_tr, y_te = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train a fresh model for CV
        m = RandomForestClassifier(n_estimators=100, random_state=42)
        m.fit(X_tr, y_tr)
        y_pred = m.predict_proba(X_te)[:, 1]
        
        try:
            scores.append(roc_auc_score(y_te, y_pred))
        except ValueError:
            continue
    
    return np.mean(scores) if scores else 0.0

def run_full_validation_pipeline(
    feature_matrix_path: str,
    model_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Orchestrates the full validation pipeline: LOEO, Null Models, Baseline.
    """
    ensure_directories_exist()
    logger.info("Starting full validation pipeline.")
    
    # Load data
    feature_df = load_feature_matrix(feature_matrix_path)
    model = load_model(model_path)
    
    # 1. LOEO
    loeo_metrics = run_loeo_cv(feature_df, model)
    
    # 2. Baseline
    cv_baseline = calculate_cv_baseline(feature_df, model)
    
    # 3. Compare
    comparison = compare_loeo_to_cv(loeo_metrics, cv_baseline)
    
    # 4. Null Models
    # Trait Shuffled
    trait_shuffled_auc = trait_shuffled_null(feature_df, model, n_iterations=100)
    
    # Degree Preserving
    degree_preserving_auc = degree_preserving_null(feature_df, n_iterations=100)
    
    # 5. Compile Results
    results = {
        'loeo_metrics': loeo_metrics,
        'cv_baseline': cv_baseline,
        'comparison': comparison,
        'trait_shuffled_null_auc': trait_shuffled_auc,
        'degree_preserving_null_auc': degree_preserving_auc,
        'trait_gap': trait_shuffled_auc - cv_baseline # Example metric
    }
    
    # Save
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation results saved to {output_path}")
    return results

def main():
    """Entry point for validation script."""
    data_root = get_data_processed()
    results_root = get_results_root()
    
    feature_path = os.path.join(data_root, 'feature_matrix.csv')
    model_path = os.path.join(data_root, 'model.pkl')
    output_path = os.path.join(results_root, 'validation_results.json')
    
    if not os.path.exists(feature_path):
        logger.error(f"Feature matrix not found at {feature_path}")
        return
    if not os.path.exists(model_path):
        logger.error(f"Model not found at {model_path}")
        return
    
    run_full_validation_pipeline(feature_path, model_path, output_path)

if __name__ == "__main__":
    main()
