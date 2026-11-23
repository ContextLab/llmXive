import logging
from typing import Any, Dict, List, Optional, Tuple
from code.src.generators.binning import classify_graph
from code.src.generators.quota_checker import check_quota_status
from code.src.generators.generation_trigger import check_trigger
from code.src.generators.metrics import compute_graph_metrics
from code.src.generators.metadata import save_metadata

logger = logging.getLogger(__name__)

def run_stratified_generation(
    generators: Dict[str, Any],
    stratification_params: Dict[str, Any],
    monitor: Any
) -> Dict[str, Any]:
    """
    Run stratified generation loop until quotas are met.
    """
    bins = stratification_params.get("bins", [])
    target_counts = stratification_params.get("target_counts", {})
    tolerance = stratification_params.get("tolerance", 0.0)

    current_counts = {bin_label: 0 for bin_label in target_counts.keys()}
    generated_graphs = []
    batch_results = []

    max_iterations = 1000  # Safety limit
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Stratified generation iteration {iteration}")

        # Check quota status
        quota_status = check_quota_status(current_counts, target_counts, tolerance)
        trigger_bin = check_trigger(quota_status, target_counts)

        if trigger_bin is None:
            logger.info("All quotas satisfied. Stopping stratified generation.")
            break

        # Select a generator that can produce graphs for the trigger bin
        # For simplicity, we iterate through all generators until we find one that fits
        # In a real implementation, we might map bins to specific generators
        found = False
        for topo_type, gen in generators.items():
            try:
                graph, metadata = gen.generate()
                if graph is None:
                    continue

                # Classify
                bin_label = classify_graph(graph, bins)
                if bin_label == trigger_bin:
                    # Accept this graph
                    metrics = compute_graph_metrics(graph)
                    metadata.update(metrics)
                    metadata["graph_id"] = f"{topo_type}_{iteration}"
                    metadata["topology_type"] = topo_type
                    metadata["bin"] = bin_label

                    save_metadata(metadata)
                    generated_graphs.append(graph)
                    batch_results.append({
                        "graph_id": metadata["graph_id"],
                        "topology_type": topo_type,
                        "bin": bin_label,
                        "metrics": metrics
                    })
                    current_counts[bin_label] = current_counts.get(bin_label, 0) + 1
                    monitor.record_attempt(True)
                    found = True
                    break
            except Exception as e:
                logger.error(f"Error generating graph for {topo_type}: {e}")
                monitor.record_attempt(False)

        if not found:
            logger.warning(f"No suitable graph found for bin {trigger_bin} in this iteration")
            monitor.record_attempt(False)

    return {
        "graphs": generated_graphs,
        "results": batch_results,
        "final_counts": current_counts
    }
