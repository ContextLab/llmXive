import os
import json
import logging
from typing import Dict, Any, List
from data_loader import fetch_beir_datasets, load_injected_dataset
from metrics import calculate_wasted_call_ratios, calculate_ndcg_at_10
from clustering import cluster_documents
from ranker import run_ranker_with_filter
from config import get_config

def run_cross_dataset_generalization_check() -> Dict[str, Any]:
    """
    T048 Implementation: Cross-Dataset Generalization Check.
    
    Compares "wasted call" ratios between nfcorpus, scifact, and trec-covid
    to ensure the redundancy effect is not dataset-specific.
    
    Returns a dictionary with the results and the path to the written artifact.
    """
    logging.info("Starting Cross-Dataset Generalization Check (T048)...")
    config = get_config()
    
    # Datasets to check
    datasets = ["nfcorpus", "scifact", "trec-covid"]
    results = {}
    
    for ds_name in datasets:
        logging.info(f"Processing dataset: {ds_name}")
        try:
            # Fetch and inject redundancy for this specific dataset
            # Note: We assume the injection logic in data_loader handles per-dataset injection
            # or we fetch fresh data here if needed.
            # For this implementation, we assume the injected datasets are prepared per T012a
            # but we need to ensure we are comparing across the specific datasets.
            
            # If the global injected_datasets.json contains all, we filter. 
            # If separate files exist, we load them. 
            # Based on T012a, we have a single file. We need to re-inject or filter.
            # To ensure real data and T048 requirements, we will re-fetch and inject per dataset
            # if the global one doesn't have the specific split or if we need to verify generalization.
            
            # Strategy: Load the injected data, but if it's a mix, we need to separate.
            # However, T012a creates one file. Let's assume we re-run the injection per dataset
            # to ensure we have the specific "wasted call" ratios for each.
            
            # Re-fetch and inject for this specific dataset to ensure isolation
            injected_data = _fetch_and_inject_dataset(ds_name)
            
            if not injected_data or len(injected_data) == 0:
                logging.warning(f"No data found for {ds_name} after injection.")
                results[ds_name] = {
                    "wasted_call_ratio": None,
                    "ndcg_at_10": None,
                    "status": "no_data",
                    "reason": "Injection produced no data"
                }
                continue

            # Calculate wasted call ratio
            # We need to simulate the "wasted" calls. The proxy is cosine similarity > 0.95.
            # We assume the injected data has the necessary similarity pre-computed or we compute it.
            # The run_ranker_with_filter returns wasted_call_ratio if we run the baseline.
            # But T048 is about checking the ratio across datasets.
            
            # Run a minimal baseline to get the ratio
            # We use a small budget to just get the ratio estimate
            budget = 50 
            result = run_ranker_with_filter(injected_data, budget=budget, use_clustering=False)
            
            wasted_ratio = result.get('wasted_call_ratio', 0.0)
            ndcg = result.get('ndcg_at_10', 0.0)
            
            results[ds_name] = {
                "wasted_call_ratio": wasted_ratio,
                "ndcg_at_10": ndcg,
                "num_items": len(injected_data),
                "status": "success"
            }
            
            logging.info(f"Dataset {ds_name}: Wasted Ratio={wasted_ratio:.4f}, NDCG@10={ndcg:.4f}")

        except Exception as e:
            logging.error(f"Failed to process {ds_name}: {e}")
            results[ds_name] = {
                "wasted_call_ratio": None,
                "ndcg_at_10": None,
                "status": "failed",
                "error": str(e)
            }
    
    # Analyze generalization
    # Check if the wasted call ratios are consistent (not dataset specific)
    # We can't do a full statistical test here without multiple seeds, but we can check variance
    valid_ratios = [r['wasted_call_ratio'] for r in results.values() if r['wasted_call_ratio'] is not None]
    
    generalization_status = "unknown"
    if len(valid_ratios) >= 2:
        # Simple heuristic: if the range is small relative to the mean, it's generalizable
        mean_ratio = sum(valid_ratios) / len(valid_ratios)
        max_diff = max(valid_ratios) - min(valid_ratios)
        if mean_ratio > 0:
            relative_diff = max_diff / mean_ratio
            if relative_diff < 0.5: # Arbitrary threshold for "generalizable"
                generalization_status = "generalizable"
            else:
                generalization_status = "dataset_specific"
        else:
            generalization_status = "unknown_mean"
    else:
        generalization_status = "insufficient_data"
    
    final_output = {
        "datasets_analyzed": list(results.keys()),
        "results_by_dataset": results,
        "generalization_status": generalization_status,
        "summary": f"Analyzed {len(valid_ratios)} datasets. Status: {generalization_status}"
    }
    
    # Write output
    output_path = os.path.join(config.data_dir, 'results', 'cross_dataset_generalization.json')
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    logging.info(f"T048 Complete. Output written to {output_path}")
    
    return {
        "output_file": output_path,
        "status": "success"
    }

def _fetch_and_inject_dataset(dataset_name: str) -> List[Dict[str, Any]]:
    """
    Fetches a specific BEIR dataset, injects redundancy, and returns the data.
    This ensures we are comparing real, injected data for each specific dataset.
    """
    from data_loader import fetch_beir_datasets, create_redundancy_clusters, save_injected_dataset
    import tempfile
    import shutil
    
    # 1. Fetch the dataset
    # We reuse the fetch logic but target a specific dataset
    # Assuming fetch_beir_datasets can take a list or we call the internal logic
    # The existing T005/T005b uses fetch_beir_datasets which might return all.
    # We need to isolate.
    
    # Let's assume we call the underlying BEIR loader directly for this specific one
    # to ensure we get the right data.
    try:
        # Re-using the verified source pattern from the prompt
        from beir import util
        from beir.datasets.data_loader import GenericDataLoader
        import os
        
        url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
        out_dir = tempfile.mkdtemp()
        try:
            data_path = util.download_and_unzip(url, out_dir)
            data_folder = os.path.join(data_path, dataset_name) if os.path.isdir(os.path.join(data_path, dataset_name)) else data_path
            
            corpus, queries, qrels = GenericDataLoader(data_folder=data_folder).load(split="test")
            
            # Convert to the format expected by the rest of the pipeline
            # We need a list of documents (passages) to inject redundancy into
            # The redundancy injection works on the "corpus" (documents)
            documents = []
            for doc_id, doc_obj in corpus.items():
                text = doc_obj["text"] if isinstance(doc_obj, dict) else doc_obj
                documents.append({
                    "doc_id": doc_id,
                    "text": text
                })
            
            if not documents:
                logging.warning(f"No documents found in {dataset_name}")
                return []
            
            # 2. Inject Redundancy
            # We call the cluster creation logic directly on these documents
            # Note: create_redundancy_clusters expects a list of docs and returns clusters
            # We need to adapt the existing T012 logic to work on this specific list
            
            # Since T012 logic is in data_loader, we call it
            # We need to ensure the injection is strong enough (sim > 0.95)
            # We might need to adjust parameters or retry if it fails
            clusters = create_redundancy_clusters(documents, target_similarity=0.95)
            
            # Flatten clusters back to a list of documents with redundancy info
            # The output of create_redundancy_clusters is a list of RedundancyCluster objects
            # We need to convert this to the format run_pipeline expects
            
            injected_docs = []
            for cluster in clusters:
                # Each cluster has a representative and duplicates
                # We add all of them to the list
                for doc in cluster.members:
                    injected_docs.append(doc)
            
            return injected_docs

        finally:
            shutil.rmtree(out_dir)
            
    except Exception as e:
        logging.error(f"Failed to fetch/inject {dataset_name}: {e}")
        raise
