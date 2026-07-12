"""
T033a: Generate data flow diagram for the Neural Entropy and Cognitive Flexibility pipeline.
Produces docs/diagrams/data_flow.png illustrating data movement from raw to final report.
"""
import os
import sys
from pathlib import Path

# Attempt to import graphviz; if missing, fallback to a static image generation using matplotlib
# which is more likely to be available in the constrained environment.
try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

def generate_with_graphviz(output_path: Path):
    """Generate diagram using graphviz."""
    dot = graphviz.Digraph(comment='Data Flow', format='png')
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box', style='filled', fillcolor='lightblue')
    dot.attr('edge', fontsize='10')

    # Nodes: Raw Data
    dot.node('raw_openneuro', 'OpenNeuro Datasets\nds003104', fillcolor='lightyellow')
    
    # Nodes: Intermediate
    dot.node('raw_parquet', 'data/raw/*.parquet', fillcolor='lightgreen')
    dot.node('behavioral_csv', 'data/processed/behavioral_scores.csv', fillcolor='lightgreen')
    dot.node('preprocessed_eeg', 'data/processed/*.fif (epoched)', fillcolor='lightgreen')
    dot.node('snr_json', 'data/processed/snr_metrics.json', fillcolor='lightgreen')
    dot.node('exclusion_log', 'data/processed/exclusion_log.csv', fillcolor='lightpink')
    dot.node('entropy_csv', 'data/processed/entropy_metrics.csv', fillcolor='lightgreen')
    dot.node('regression_csv', 'data/processed/correlation_results_fdr.csv', fillcolor='lightgreen')
    dot.node('sensitivity_json', 'data/processed/sensitivity_report.json', fillcolor='lightgreen')
    dot.node('bonferroni_csv', 'data/processed/correlation_results_bonferroni_historical.csv', fillcolor='lightgray')

    # Nodes: Final
    dot.node('report_md', 'reports/final_report.md', shape='note', fillcolor='lightblue')
    dot.node('validation_logs', 'logs/validation_log.*.txt', shape='note', fillcolor='lightgray')

    # Edges: Process Flow
    dot.edge('raw_openneuro', 'raw_parquet', 'T012: Download & Verify')
    dot.edge('raw_parquet', 'behavioral_csv', 'T012b: Extract Behavioral')
    dot.edge('raw_parquet', 'preprocessed_eeg', 'T013: Preprocess EEG')
    dot.edge('preprocessed_eeg', 'snr_json', 'T014: Calc SNR')
    dot.edge('snr_json', 'exclusion_log', 'T016: Quality Checks')
    dot.edge('preprocessed_eeg', 'entropy_csv', 'T015: Compute Entropy')
    
    dot.edge('entropy_csv', 'regression_csv', 'T020a/T021: OLS + FDR')
    dot.edge('behavioral_csv', 'regression_csv', 'Join')
    dot.edge('regression_csv', 'bonferroni_csv', 'T022: Historical Track')
    dot.edge('regression_csv', 'sensitivity_json', 'T027/T028: Sensitivity')
    
    dot.edge('sensitivity_json', 'report_md', 'T030: Generate Report')
    dot.edge('regression_csv', 'report_md', 'T030: Include Results')
    
    # Validation Edges
    dot.edge('regression_csv', 'validation_logs', 'T032a: Schema Check')
    dot.edge('sensitivity_json', 'validation_logs', 'T032b: Schema Check')

    dot.render(str(output_path), cleanup=True)

def generate_with_matplotlib(output_path: Path):
    """Generate diagram using matplotlib as fallback."""
    fig, ax = plt.subplots(figsize=(20, 10))
    ax.axis('off')
    
    # Define boxes
    boxes = [
        # Raw
        {'label': 'OpenNeuro\nds003104', 'x': 0.05, 'y': 0.5, 'w': 0.15, 'h': 0.1, 'color': 'lightyellow'},
        # Intermediate
        {'label': 'data/raw/*.parquet', 'x': 0.25, 'y': 0.5, 'w': 0.15, 'h': 0.1, 'color': 'lightgreen'},
        {'label': 'behavioral_scores.csv', 'x': 0.25, 'y': 0.2, 'w': 0.15, 'h': 0.1, 'color': 'lightgreen'},
        {'label': 'preprocessed EEG\n(epoched)', 'x': 0.45, 'y': 0.5, 'w': 0.15, 'h': 0.1, 'color': 'lightgreen'},
        {'label': 'snr_metrics.json', 'x': 0.45, 'y': 0.35, 'w': 0.15, 'h': 0.08, 'color': 'lightgreen'},
        {'label': 'exclusion_log.csv', 'x': 0.45, 'y': 0.65, 'w': 0.15, 'h': 0.08, 'color': 'lightpink'},
        {'label': 'entropy_metrics.csv', 'x': 0.65, 'y': 0.5, 'w': 0.15, 'h': 0.1, 'color': 'lightgreen'},
        {'label': 'correlation_results_fdr.csv', 'x': 0.85, 'y': 0.5, 'w': 0.15, 'h': 0.1, 'color': 'lightgreen'},
        {'label': 'sensitivity_report.json', 'x': 0.85, 'y': 0.3, 'w': 0.15, 'h': 0.1, 'color': 'lightgreen'},
        {'label': 'correlation_results_bonferroni\n(historical)', 'x': 0.85, 'y': 0.7, 'w': 0.15, 'h': 0.1, 'color': 'lightgray'},
        # Final
        {'label': 'final_report.md', 'x': 1.0, 'y': 0.5, 'w': 0.15, 'h': 0.1, 'color': 'lightblue', 'shape': 'box'},
        {'label': 'validation_logs', 'x': 1.0, 'y': 0.7, 'w': 0.15, 'h': 0.1, 'color': 'lightgray', 'shape': 'box'},
    ]

    # Draw boxes
    for box in boxes:
        rect = patches.Rectangle(
            (box['x'], box['y']), box['w'], box['h'], 
            linewidth=2, edgecolor='black', facecolor=box['color'], 
            clip_on=False
        )
        ax.add_patch(rect)
        ax.text(
            box['x'] + box['w']/2, box['y'] + box['h']/2, 
            box['label'], ha='center', va='center', fontsize=9, 
            fontweight='bold'
        )

    # Draw arrows (lines)
    arrows = [
        # Raw -> Parquet
        (0.20, 0.55, 0.25, 0.55, "T012"),
        # Parquet -> Behavioral
        (0.25, 0.50, 0.25, 0.25, "T012b"),
        # Parquet -> EEG
        (0.40, 0.55, 0.45, 0.55, "T013"),
        # EEG -> SNR
        (0.52, 0.45, 0.52, 0.40, "T014"),
        # SNR -> Exclusion
        (0.52, 0.35, 0.52, 0.65, "T016"),
        # EEG -> Entropy
        (0.60, 0.55, 0.65, 0.55, "T015"),
        # Entropy + Behavioral -> Regression
        (0.80, 0.50, 0.85, 0.50, "T020a/021"),
        (0.40, 0.20, 0.85, 0.50, "Join"),
        # Regression -> Bonferroni
        (0.92, 0.55, 0.92, 0.70, "T022"),
        # Regression -> Sensitivity
        (0.92, 0.45, 0.92, 0.35, "T027/028"),
        # Sensitivity -> Report
        (1.00, 0.35, 1.00, 0.50, "T030"),
        # Regression -> Report
        (0.92, 0.50, 1.00, 0.50, "T030"),
        # Regression -> Validation
        (0.92, 0.50, 0.92, 0.75, "T032a"),
        (0.92, 0.35, 0.92, 0.75, "T032b"),
    ]

    for x1, y1, x2, y2, label in arrows:
        ax.annotate(
            '', xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5)
        )
        # Add label text if present
        if label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            ax.text(mid_x, mid_y, label, fontsize=8, color='darkblue', ha='center', va='center')

    plt.tight_layout()
    plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
    plt.close()

def main():
    output_dir = Path("docs/diagrams")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "data_flow.png"

    print(f"Generating data flow diagram to {output_path}...")

    if HAS_GRAPHVIZ:
        try:
            generate_with_graphviz(output_path)
            print("Successfully generated diagram using graphviz.")
            return
        except Exception as e:
            print(f"Graphviz generation failed: {e}, falling back to matplotlib.")
    
    if HAS_MATPLOTLIB:
        try:
            generate_with_matplotlib(output_path)
            print("Successfully generated diagram using matplotlib.")
            return
        except Exception as e:
            print(f"Matplotlib generation failed: {e}")
    
    raise RuntimeError("Failed to generate diagram: Neither graphviz nor matplotlib is available.")

if __name__ == "__main__":
    main()