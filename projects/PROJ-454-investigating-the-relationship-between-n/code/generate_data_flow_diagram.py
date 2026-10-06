"""
Generate the data flow diagram for the Neural Entropy and Cognitive Flexibility project.
Creates a PNG visualization illustrating data movement from raw to final report.
"""
import os
import sys
from pathlib import Path

# Try to use graphviz for high-quality diagrams, fallback to matplotlib if unavailable
try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        HAS_MATPLOTLIB = True
    except ImportError:
        HAS_MATPLOTLIB = False

def generate_with_graphviz(output_path: Path):
    """Generate diagram using Graphviz DOT language."""
    dot = graphviz.Digraph(
        'data_flow',
        comment='Neural Entropy Data Flow',
        format='png',
        graph_attr={'rankdir': 'LR', 'fontsize': '12', 'splines': 'ortho', 'label': 'Data Flow: Raw EEG to Final Report', 'labelloc': 't', 'fontname': 'Helvetica'}
    )

    # Define nodes (stages)
    # Raw Data
    dot.node('raw', 'Raw Data\n(data/raw/)', shape='box', style='filled', fillcolor='lightblue')
    dot.node('parquet', 'Parquet Files\n(data/raw/*.parquet)', shape='box', style='filled', fillcolor='lightblue')

    # Preprocessing
    dot.node('preprocess', 'Preprocessing\n(02_preprocess_eeg.py)', shape='box', style='filled', fillcolor='lightyellow')
    dot.node('epoched', 'Epoched Data\n(data/processed/*.pkl)', shape='box', style='filled', fillcolor='lightyellow')
    dot.node('snr', 'SNR Metrics\n(data/processed/snr_metrics.json)', shape='box', style='filled', fillcolor='lightyellow')
    dot.node('exclusion', 'Exclusion Log\n(data/processed/exclusion_log.csv)', shape='box', style='filled', fillcolor='lightyellow')

    # Entropy
    dot.node('entropy', 'Entropy Compute\n(compute_entropy.py)', shape='box', style='filled', fillcolor='lightgreen')
    dot.node('entropy_out', 'Entropy Metrics\n(data/processed/entropy_metrics.csv)', shape='box', style='filled', fillcolor='lightgreen')

    # Behavioral
    dot.node('behavioral', 'Behavioral Extract\n(012c_extract_behavioral_scores.py)', shape='box', style='filled', fillcolor='lightcyan')
    dot.node('behavioral_out', 'Behavioral Scores\n(data/processed/behavioral_scores.csv)', shape='box', style='filled', fillcolor='lightcyan')

    # Regression
    dot.node('regression', 'Regression Analysis\n(04_regression_analysis.py)', shape='box', style='filled', fillcolor='orange')
    dot.node('ols_out', 'OLS Results\n(data/processed/correlation_results_ols.csv)', shape='box', style='filled', fillcolor='orange')
    dot.node('fdr_out', 'FDR Results\n(data/processed/correlation_results_fdr.csv)', shape='box', style='filled', fillcolor='orange')
    dot.node('sensitivity', 'Sensitivity Report\n(data/processed/sensitivity_report.json)', shape='box', style='filled', fillcolor='orange')

    # Report
    dot.node('report_gen', 'Report Generation\n(05_generate_report.py)', shape='box', style='filled', fillcolor='plum')
    dot.node('final_report', 'Final Report\n(reports/final_report.md)', shape='box', style='filled', fillcolor='plum')
    dot.node('notes', 'Methodology Notes\n(docs/methodology_notes.md)', shape='box', style='filled', fillcolor='plum')

    # Define edges (flow)
    dot.edge('raw', 'parquet', label='Download\n(01_download_data.py)')
    dot.edge('parquet', 'preprocess', label='Load & Validate\n(01_validate_data.py)')
    dot.edge('parquet', 'behavioral', label='Extract Scores')
    dot.edge('behavioral', 'behavioral_out')
    
    dot.edge('preprocess', 'epoched', label='Filter, ICA, Epoch')
    dot.edge('preprocess', 'snr', label='Calculate SNR')
    dot.edge('preprocess', 'exclusion', label='Quality Checks')
    
    dot.edge('epoched', 'entropy', label='Load Cleaned Data')
    dot.edge('entropy', 'entropy_out', label='Compute Sample/ApEn')
    
    dot.edge('entropy_out', 'regression', label='Join with Behavioral')
    dot.edge('behavioral_out', 'regression')
    dot.edge('exclusion', 'regression', label='Apply Filters')
    
    dot.edge('regression', 'ols_out', label='Run OLS')
    dot.edge('ols_out', 'fdr_out', label='FDR Correction')
    dot.edge('fdr_out', 'sensitivity', label='Sensitivity Analysis')
    
    dot.edge('ols_out', 'report_gen')
    dot.edge('fdr_out', 'report_gen')
    dot.edge('sensitivity', 'report_gen')
    dot.edge('behavioral_out', 'report_gen')
    dot.edge('entropy_out', 'report_gen')
    
    dot.edge('report_gen', 'final_report')
    dot.edge('report_gen', 'notes')

    # Render
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dot.render(str(output_path), cleanup=True)
    return True

def generate_with_matplotlib(output_path: Path):
    """Generate diagram using Matplotlib as a fallback."""
    if not HAS_MATPLOTLIB:
        raise RuntimeError("Neither Graphviz nor Matplotlib is available.")
    
    fig, ax = plt.subplots(figsize=(20, 10))
    ax.axis('off')
    
    # Define layout coordinates (x, y)
    # Stage 1: Raw
    stages = [
        {"name": "Raw Data", "files": "data/raw/", "x": 1, "y": 5, "color": "lightblue"},
        {"name": "Download", "files": "01_download_data.py", "x": 2.5, "y": 5, "color": "lightblue"},
        {"name": "Validate", "files": "01_validate_data.py", "x": 3.5, "y": 5, "color": "lightblue"},
        
        # Stage 2: Preprocessing
        {"name": "Preprocessing", "files": "02_preprocess_eeg.py", "x": 5, "y": 5, "color": "lightyellow"},
        {"name": "Epoched Data", "files": "data/processed/*.pkl", "x": 6.5, "y": 6, "color": "lightyellow"},
        {"name": "SNR Metrics", "files": "data/processed/snr_metrics.json", "x": 6.5, "y": 5, "color": "lightyellow"},
        {"name": "Exclusion Log", "files": "data/processed/exclusion_log.csv", "x": 6.5, "y": 4, "color": "lightyellow"},
        
        # Stage 3: Entropy & Behavioral
        {"name": "Entropy Compute", "files": "compute_entropy.py", "x": 8, "y": 6, "color": "lightgreen"},
        {"name": "Entropy Metrics", "files": "data/processed/entropy_metrics.csv", "x": 9.5, "y": 6, "color": "lightgreen"},
        
        {"name": "Behavioral Extract", "files": "012c_extract_behavioral_scores.py", "x": 8, "y": 4, "color": "lightcyan"},
        {"name": "Behavioral Scores", "files": "data/processed/behavioral_scores.csv", "x": 9.5, "y": 4, "color": "lightcyan"},
        
        # Stage 4: Regression
        {"name": "Regression Analysis", "files": "04_regression_analysis.py", "x": 11, "y": 5, "color": "orange"},
        {"name": "OLS Results", "files": "data/processed/correlation_results_ols.csv", "x": 12.5, "y": 5.5, "color": "orange"},
        {"name": "FDR Results", "files": "data/processed/correlation_results_fdr.csv", "x": 14, "y": 5.5, "color": "orange"},
        {"name": "Sensitivity Report", "files": "data/processed/sensitivity_report.json", "x": 15.5, "y": 5.5, "color": "orange"},
        
        # Stage 5: Report
        {"name": "Report Generation", "files": "05_generate_report.py", "x": 13, "y": 3, "color": "plum"},
        {"name": "Final Report", "files": "reports/final_report.md", "x": 14.5, "y": 2, "color": "plum"},
        {"name": "Methodology Notes", "files": "docs/methodology_notes.md", "x": 14.5, "y": 1, "color": "plum"},
    ]
    
    # Draw boxes
    for stage in stages:
        rect = mpatches.FancyBboxPatch(
            (stage["x"] - 1.5, stage["y"] - 0.4),
            3.0, 0.8,
            boxstyle="round,pad=0.1,rounding_size=0.1",
            linewidth=1, edgecolor='black', facecolor=stage["color"]
        )
        ax.add_patch(rect)
        ax.text(stage["x"], stage["y"] + 0.15, stage["name"], ha='center', va='center', fontsize=9, fontweight='bold')
        ax.text(stage["x"], stage["y"] - 0.15, stage["files"], ha='center', va='center', fontsize=7)
    
    # Draw arrows
    arrows = [
        (2.5, 5, 3.5, 5), (3.5, 5, 5, 5), (5, 5, 6.5, 6), (5, 5, 6.5, 5), (5, 5, 6.5, 4),
        (6.5, 6, 8, 6), (8, 6, 9.5, 6),
        (6.5, 4, 8, 4), (8, 4, 9.5, 4),
        (9.5, 6, 11, 5), (9.5, 4, 11, 5), (6.5, 5, 11, 5),
        (11, 5, 12.5, 5.5), (12.5, 5.5, 14, 5.5), (14, 5.5, 15.5, 5.5),
        (12.5, 5.5, 13, 3), (14, 5.5, 13, 3), (15.5, 5.5, 13, 3),
        (13, 3, 14.5, 2), (13, 3, 14.5, 1)
    ]
    
    for x1, y1, x2, y2 in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))
        
    plt.title('Neural Entropy Data Flow Diagram', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
    plt.close()
    return True

def main():
    """Main entry point to generate the data flow diagram."""
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "docs" / "diagrams"
    output_path = output_dir / "data_flow.png"
    
    print(f"Generating data flow diagram to: {output_path}")
    
    try:
        if HAS_GRAPHVIZ:
            print("Using Graphviz backend...")
            generate_with_graphviz(output_path)
        elif HAS_MATPLOTLIB:
            print("Using Matplotlib backend...")
            generate_with_matplotlib(output_path)
        else:
            print("Error: No diagram backend available. Install graphviz or matplotlib.")
            sys.exit(1)
            
        print(f"Successfully created: {output_path}")
        
    except Exception as e:
        print(f"Error generating diagram: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
