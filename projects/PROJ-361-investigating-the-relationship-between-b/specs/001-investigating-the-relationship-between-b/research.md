# Research: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

## 1. Scientific Background

### 1.1 Visual Illusions and Perception
Visual illusions, such as the Müller-Lyer and Ponzo illusions, reveal systematic biases in human perception where physical reality diverges from subjective experience. Susceptibility to these illusions varies across individuals and has been hypothesized to reflect differences in the brain's integration of sensory context and prior expectations.

### 1.2 Brain Network Topology
Resting-state functional connectivity (RSFC) networks exhibit small-world topology, balancing local segregation (clustering) and global integration (path length). Metrics such as modularity, efficiency, and small-worldness quantify these properties. Theoretical frameworks suggest that individual differences in network topology may underlie variations in cognitive processing, including perceptual susceptibility.

### 1.3 Hypothesis
Individuals with specific topological configurations (e.g., higher global efficiency or lower modularity) may exhibit different magnitudes of error in visual illusion tasks, suggesting a link between the brain's intrinsic functional architecture and perceptual bias.

**CRITICAL NOTE**: The target dataset (OpenNeuro ds004285) does not contain resting-state fMRI or illusion scores. This study will analyze the topology of *movie-watching* fMRI data and document the absence of the required behavioral variable.

## 2. Dataset Strategy

### 2.1 Primary Dataset: OpenNeuro ds004285
The project utilizes the OpenNeuro dataset **ds004285** (Naturalistic Viewing of Movies).

**Verified Sources**:
- **HuggingFace Mirror (Parquet)**: `
- **HuggingFace Mirror (Arrow)**: `
- **Original Source**: OpenNeuro ds004285 (referenced via the verified mirror for programmatic access).

**Dataset Verification**:
- **Accessibility**: The dataset is accessible via the HuggingFace `datasets` library.
- **Variables**:
 - **fMRI**: Movie-watching BOLD time series (NOT resting-state).
 - **Behavioral**: **NO visual illusion scores (Müller-Lyer, Ponzo) found in this dataset.** The dataset contains movie annotations but not the specific illusion task data required by the original hypothesis.
- **Feasibility**: The dataset size is compatible with the CPU-first compute budget (~7GB RAM) when streaming or sampling appropriately.

### 2.2 Data Acquisition Plan
1. **Download**: Use `datasets.load_dataset("clane9/openneuro-fslr64k")` to fetch the data.
2. **Verification**: Compute SHA-256 checksums for all downloaded files and record them in `data/metadata/checksums.json`.
3. **Streaming**: For large fMRI files, use `streaming=True` to avoid loading the entire dataset into memory.
4. **Behavioral Check**: Explicitly search for files matching `*illusion*` or `*behavioral*`. If not found, log a "MISSING BEHAVIORAL DATA" status.

### 2.3 Data Exclusion Criteria
- **Motion**: Subjects with Mean Framewise Displacement (FD) > 0.5mm will be excluded.
- **Missing Data**: Subjects lacking fMRI data will be excluded.
- **Artifact**: Exclusion lists will be materialized as `data/processed/excluded_subjects.csv` to ensure reproducibility.

## 3. Methodology

### 3.1 Preprocessing
- **Tool**: fMRIPrep (containerized via Docker/Singularity).
- **Steps**:
 1. Motion correction.
 2. Spatial normalization to MNI space.
 3. Nuisance regression (white matter, CSF, motion parameters).
 4. Bandpass filtering (0.01-0.1 Hz).
- **Output**: Preprocessed BOLD time series (nifti format).
- **Constraint**: CPU-only execution. Sample size limited to ~5-10 subjects to fit within 6h runtime.

### 3.2 Network Construction
- **Parcellation**: Use a standard atlas (e.g., AAL or Schaefer) to define regions of interest (ROIs).
- **Connectivity**: Compute Pearson correlation matrices between ROI time series.
- **Thresholding**: Apply a **fixed proportional threshold of 10%** to retain the top [deferred] of edges. A sensitivity analysis ([deferred]-20%) will be performed if time permits to ensure stability.

### 3.3 Graph Theory Metrics
Compute the following metrics for each subject's network (Small-worldness is **excluded** due to redundancy):
1. **Modularity (Q)**: Degree of community structure.
2. **Characteristic Path Length (L)**: Average shortest path between nodes.
3. **Clustering Coefficient (C)**: Tendency of nodes to cluster.
4. **Global Efficiency (E_glob)**: Inverse of path length; measure of integration.

**Library**: `networkx` and `bctpy` (Brain Connectivity Toolbox for Python).

### 3.4 Statistical Analysis
- **Collinearity Handling**: The five metrics are highly collinear. To address this, we will perform **Principal Component Analysis (PCA)** on the four metrics (Modularity, Path Length, Clustering, Efficiency) to derive orthogonal components.
- **Correlation**: Pearson or Spearman correlation between the **PCA components** and available behavioral data (if any).
- **Multiple Comparison Correction**: Benjamini-Hochberg FDR correction (q < 0.05) across all tested component-behavior pairs.
- **Reporting**: All claims framed as "associational"; no causal inference. If behavioral data is missing, the report will state "No behavioral correlation possible."

## 4. Compute Feasibility

### 4.1 CPU-First Strategy
- **fMRIPrep**: Runs on CPU; limited to ~5-10 subjects to fit within 6h.
- **Graph Metrics**: `networkx` operations are CPU-efficient.
- **Streaming**: Data is streamed to avoid RAM overflow.

### 4.2 GPU Escape Hatch
- **Trigger**: None for current pipeline (fMRIPrep is CPU-bound).
- **Plan**: If future deep learning steps are added, the pipeline will re-run on a Kaggle GPU instance (16GB VRAM) with `device="cuda"`.

## 5. Risk Assessment

| Risk | Probability | Mitigation |
|:--- |:--- |:--- |
| **Dataset Mismatch** | HIGH | ds004285 lacks illusion scores. Mitigation: Document gap; analyze topology only. |
| **Motion Exclusion** | Medium | Strict FD > 0.5mm may exclude many subjects; report power limitation honestly. |
| **Compute Time** | High | fMRIPrep may exceed 6h. Mitigation: Limit sample size to 5-10 subjects. |
| **Collinearity** | High | Metrics are related. Mitigation: Use PCA to derive orthogonal components. |

## 6. Decision Rationale

- **Dataset**: OpenNeuro ds004285 was chosen as the only verified source, but it lacks the required variables. The study is revised to analyze the available movie-watching data.
- **CPU-First**: The analysis relies on classical statistics and graph theory, which are computationally tractable on CPU.
- **FDR Correction**: Mandatory per Constitution Principle VII to control false discovery rates.
- **Associational Framing**: Per Constitution Constraint, all findings are framed as associations.
- **PCA**: Used to handle collinearity among graph metrics.