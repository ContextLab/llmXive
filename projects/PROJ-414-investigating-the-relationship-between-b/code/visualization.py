"""Visualization of vertex‑block connectivity topology.

This script produces a single PNG figure (`results/fig_network_topology.png`)
that visualises the mean adjacency matrix derived from the vertex‑block
time‑series.  If real task‑condition labels are present (as recorded in
`data/derived/task_label_status.json`), the figure shows two side‑by‑side
graphs – one per condition – with node colours indicating Louvain
communities and edge widths proportional to the mean edge weight.
If no task‑condition labels exist, a single‑group descriptive topology
is rendered.

The adjacency matrix is computed from the block‑mean time‑series
(`roi_timeseries_<subject>.csv`) that were produced by the extraction
stage.  For each subject we compute the Pearson correlation matrix
between the 100 deterministic vertex‑blocks, then average these matrices
across all (or per‑condition) subjects.

The figure is saved to `results/fig_network_topology.png` using
Matplotlib.  The function ``compute_mean_adjacency`` is also imported by
the unit test to verify the matrix shape and node labels.
"""
import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from llmxive_toolkit import get_logger, paths
from code.graph_metrics import louvain_modularity

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_task_label_status() -> dict:
    """Load the JSON file that records whether task labels exist."""
    status_path = paths.data("derived", "task_label_status.json")
    if not status_path.is_file():
        log.warning("Task‑label status file not found – assuming no labels.")
        return {"task_labels_present": False}
    return json.loads(status_path.read_text())

def _load_subject_time_series(subject_id: str) -> pd.DataFrame:
    """Load a subject's block‑wise time‑series CSV.

    Returns a DataFrame with columns ``timepoint`` and one column per
    ``roi_id`` (``roi_1`` … ``roi_100``)."""
    csv_path = paths.data("derived", f"roi_timeseries_{subject_id}.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Missing ROI timeseries for subject {subject_id}")
    df = pd.read_csv(csv_path)
    # Pivot to wide format: rows = timepoints, columns = roi_id
    wide = df.pivot(index="timepoint", columns="roi_id", values="value")
    # Ensure deterministic ordering of ROI columns
    roi_order = [f"roi_{i+1}" for i in range(100)]
    wide = wide[roi_order]
    return wide

def _subject_correlation_matrix(wide: pd.DataFrame) -> np.ndarray:
    """Pearson correlation matrix (100 × 100) for a single subject."""
    # ``wide`` is (timepoints, 100); ``np.corrcoef`` expects variables in rows
    corr = np.corrcoef(wide.T)
    # Clip to [‑1, 1] to guard against numerical noise
    np.clip(corr, -1.0, 1.0, out=corr)
    return corr

def compute_mean_adjacency() -> dict:
    """Compute the mean adjacency matrix.

    Returns a dictionary with keys:
        - ``matrix``: (100, 100) ``np.ndarray`` of mean correlations
        - ``per_condition``: optional dict mapping condition label → matrix
    """
    # Discover all subject IDs from the extracted ROI files
    derived_dir = paths.data("derived")
    roi_files = sorted(derived_dir.glob("roi_timeseries_*.csv"))
    if not roi_files:
        raise RuntimeError("No ROI timeseries files found – cannot build adjacency.")

    # Load task‑label status to decide whether to split by condition
    status = _load_task_label_status()
    per_condition = {}

    # Helper to fetch condition for a subject from its QC record
    def _subject_condition(sid: str) -> str | None:
        qc_path = derived_dir / f"qc_{sid}.json"
        if not qc_path.is_file():
            return None
        qc = json.loads(qc_path.read_text())
        # ``task_values`` is a list; we take the first entry if present
        vals = qc.get("task_values", [])
        return vals[0] if vals else None

    # Accumulate correlation matrices
    accum_all = np.zeros((100, 100), dtype=np.float64)
    count_all = 0

    for roi_path in roi_files:
        sid = roi_path.stem.replace("roi_timeseries_", "")
        wide = _load_subject_time_series(sid)
        corr = _subject_correlation_matrix(wide)

        # Global (all subjects) accumulation
        accum_all += corr
        count_all += 1

        # Conditional accumulation
        if status.get("task_labels_present"):
            cond = _subject_condition(sid)
            if cond is None:
                continue
            if cond not in per_condition:
                per_condition[cond] = {"sum": np.zeros_like(corr), "count": 0}
            per_condition[cond]["sum"] += corr
            per_condition[cond]["count"] += 1

    mean_all = accum_all / max(count_all, 1)

    result = {"matrix": mean_all}
    if per_condition:
        result["per_condition"] = {
            cond: data["sum"] / max(data["count"], 1)
            for cond, data in per_condition.items()
        }
    return result

def _build_graph(adjacency: np.ndarray) -> nx.Graph:
    """Create a weighted undirected graph from an absolute correlation matrix."""
    # Use absolute values because edge weight must be non‑negative
    weights = np.abs(adjacency)
    np.fill_diagonal(weights, 0.0)  # remove self‑loops
    G = nx.Graph()
    n = weights.shape[0]
    for i in range(n):
        G.add_node(i, label=f"roi_{i+1}")
    # Add edges for all non‑zero weights (the matrix is dense)
    rows, cols = np.where(weights > 0)
    for i, j in zip(rows, cols):
        if i < j:  # avoid double‑adding
            G.add_edge(i, j, weight=weights[i, j])
    return G

def _draw_graph(G: nx.Graph, ax, title: str = ""):
    """Draw ``G`` on ``ax`` with edge widths ∝ weight and node colours ∝ Louvain community."""
    # Determine Louvain communities (deterministic seed via config)
    import config

    # NetworkX's Louvain implementation uses a random seed; we set NumPy's RNG
    rng = np.random.default_rng(config.LOUVAIN_SEED)
    # The community detection function is deterministic given the seed
    communities = list(nx.algorithms.community.louvain_communities(G, seed=config.LOUVAIN_SEED))
    # Map node → community index
    comm_map = {}
    for idx, comm in enumerate(communities):
        for node in comm:
            comm_map[node] = idx

    # Node colours
    colours = [comm_map[n] for n in G.nodes()]

    # Positions – use a circular layout for reproducibility
    pos = nx.circular_layout(G, scale=2.0, seed=config.LOUVAIN_SEED)

    # Edge widths – scale so that typical weights are visible
    edges = G.edges(data=True)
    weights = [d["weight"] for (_, _, d) in edges]
    # Normalise to a reasonable range for linewidths
    max_w = max(weights) if weights else 1.0
    widths = [3.0 * (w / max_w) for w in weights]

    nx.draw_networkx_nodes(G, pos, node_color=colours, cmap=plt.cm.tab20, ax=ax, node_size=150)
    nx.draw_networkx_edges(G, pos, width=widths, alpha=0.6, ax=ax)
    nx.draw_networkx_labels(
        G,
        pos,
        labels={n: f"roi_{n+1}" for n in G.nodes()},
        font_size=6,
        ax=ax,
    )
    ax.set_title(title, fontsize=10)
    ax.axis("off")

def _save_figure(mean_adj: np.ndarray, per_condition: dict | None):
    """Render and save the topology figure."""
    out_path = paths.results("fig_network_topology.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(
        nrows=1,
        ncols=2 if per_condition else 1,
        figsize=(10, 5),
        constrained_layout=True,
    )
    if not isinstance(axes, np.ndarray):
        axes = [axes]

    # Single‑group plot (always the first subplot)
    G_all = _build_graph(mean_adj)
    _draw_graph(G_all, axes[0], title="Mean vertex‑block topology (all subjects)")

    # Conditional plots – we only render the first condition if many exist
    if per_condition:
        # Choose a deterministic ordering of conditions
        cond_names = sorted(per_condition.keys())
        # Render the first condition only (the figure caption explains the fallback)
        cond = cond_names[0]
        G_cond = _build_graph(per_condition[cond])
        _draw_graph(G_cond, axes[1], title=f"Mean topology – condition: {cond}")

    # Caption / legend note – added as a text box
    fig.text(
        0.5,
        0.01,
        "Vertex‑block connectivity descriptors (deterministic 100‑block scheme). "
        "Edge width ∝ absolute correlation; node colour ∝ Louvain community.",
        ha="center",
        fontsize=8,
    )
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info("Network topology figure saved to %s", out_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    """Generate the network topology figure."""
    # ``argv`` is ignored – the orchestrator supplies configuration via globals.
    adjacency_info = compute_mean_adjacency()
    mean_matrix = adjacency_info["matrix"]
    per_cond = adjacency_info.get("per_condition")
    _save_figure(mean_matrix, per_cond)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
