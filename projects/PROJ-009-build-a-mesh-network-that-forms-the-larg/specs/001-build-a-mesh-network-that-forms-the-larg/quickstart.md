# Quickstart: Mesh Network Supercomputer Using Pooled Idle Computing Resources

## Prerequisites
- **Local Machine**: Linux/macOS with Python 3.11+ installed.  
- **Testbed Devices**: 10–20 heterogeneous devices (laptops, Raspberry Pis, Android phones) on the same Wi‑Fi network.  
- **SSH Access**: Password‑less SSH keys configured for every testbed device.  
- **CLI Tools on Nodes**: `tcpdump`, `mpstat`, `iperf3`, `ping`, `tc` (for latency injection), `sensors` (for temperature), `iwconfig` (for RSSI).  
- **Network**: Ability to shape traffic (e.g., `tc qdisc add …`).  

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-009-build-a-mesh-network-that-forms-the-larg

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r code/requirements.txt
```

## Configuration
Create a `config.yaml` in the project root (the file is required by the test suite and the CLI).

```yaml
testbed:
  nodes:
    - ip: "192.168.1.101"
      hardware: "Raspberry Pi 4"
    - ip: "192.168.1.102"
      hardware: "Laptop Intel i7"
    # Add additional nodes as needed
  network:
    base_latency_ms: 5      # typical baseline latency on your network
    packet_loss_rate: 0.0   # expected baseline loss
    bandwidth_mbps: 100     # approximate baseline bandwidth
    snr_db: 40              # typical SNR on your channel

benchmark:
  granularity: ["fine", "medium", "coarse"]
  node_counts: [10, 15, 20]
  injected_latencies: [0, 50, 100, 200]  # ms
  runs_per_config: 2
  random_seed: 42

analysis:
  max_runtime_hours: 5   # CI‑friendly default; adjust if you have more resources
```

Verify SSH connectivity to all nodes:

```bash
python -m code.orchestrator.node_manager --verify
```

## Step‑by‑Step Workflow

### 1. Calibration (creates real‑world conversion factors)
```bash
python -m code.orchestrator.calibration --config config.yaml
```
- **Network calibration** → `data/raw/network_calibration.json` (packet‑count ↔ throughput).  
- **CPU calibration** → `data/raw/cpu_calibration.json` (mpstat % ↔ CPU load).  

### 2. Run a Single Benchmark (real hardware)
```bash
python -m code.orchestrator.cli run \
  --config config.yaml \
  --granularity fine \
  --node-count 15 \
  --injected-latency 100
```
*Outcome*:  
- Scheduler distributes Monte Carlo integration chunks.  
- Each node logs `tcpdump` and `mpstat`; metadata written to `data/raw/physical_node_<ip>.json`.  
- Dropout events recorded in `data/raw/dropout_events.json`.  
- Raw CSV `data/raw/run_<id>.csv` and `task_chunks/<run_id>.jsonl` are produced.  

### 3. Full Parameter Sweep (research‑scale, CI‑verified)
```bash
python -m code.orchestrator.cli sweep --config config.yaml
```
*What happens*:  
- Executes every combination of granularity, node count, and injected latency (default 2 replicates each).  
- After each run, calibration factors are applied, and aggregated metrics are stored under `data/processed/`.  

### 4. Mock Run (CPU‑only, used by CI verification)
```bash
python -m code.orchestrator.cli mock --config config.yaml
```
- Generates a synthetic mesh of virtual nodes with realistic heterogeneity distributions.  
- Produces **all** required artefacts (`run_*.csv`, `task_chunks/*.jsonl`, `dropout_events.json`, `physical_node_*.json`, calibration JSONs, runtime JSON, timeout log).  
- All files are validated against the schemas in `contracts/`.  

### 5. Analysis (runs on either real or mock data)
```bash
# Aggregate and fit regression
python -m code.analysis.regression \
  --input data/raw/ \
  --output data/processed/

# Theoretical bound validation
python -m code.analysis.theoretical_bound \
  --input data/processed/execution_runs.csv \
  --output data/processed/
```
*Outputs*:  
- `data/processed/execution_runs.csv` (one row per configuration).  
- `data/processed/regression_model.json` (coefficients, p‑values, R², VIF, FDR‑adjusted p‑values).  
- `data/processed/theoretical_bound_validation.json` (normalized efficiency, scaling‑law exponent comparison, deviation flags).  

### 6. Testing
```bash
# Unit tests
pytest tests/unit/ -v

# Contract (schema) tests
pytest tests/contract/ -v

# Integration test (mock pipeline end‑to‑end)
pytest tests/integration/ -v --mock-testbed
```
All tests must exit with status 0; CI will fail otherwise.

## Output Artefacts
| Artifact | Location | Description |
|----------|----------|-------------|
| Raw execution logs | `data/raw/run_*.csv` | One row per task chunk (wall‑clock time, CPU %, packet count). |
| Dropout events | `data/raw/dropout_events.json` | JSON array of node dropout/re‑assignment events. |
| Physical node metadata | `data/raw/physical_node_*.json` | Baseline & runtime metrics per node. |
| TaskChunk records | `data/raw/task_chunks/*.jsonl` | JSON‑Lines of each dispatched chunk (validated against schema). |
| Calibration data | `data/raw/network_calibration.json`, `data/raw/cpu_calibration.json` | Conversion factors used in analysis. |
| Aggregated metrics | `data/processed/execution_runs.csv` | One row per configuration (throughput, efficiency, overhead). |
| Regression model | `data/processed/regression_model.json` | Coefficients, p‑values, R², VIF, FDR‑adjusted results. |
| Theoretical bound validation | `data/processed/theoretical_bound_validation.json` | Deviation ratio, scaling‑law exponent comparison, bound‑violation flags. |
| Runtime tracker | `data/runtime/pipeline_runtime.json` | Total pipeline wall‑clock time. |
| Timeout log | `data/runtime/timeout_enforced.log` | Message indicating whether the hard timeout was triggered. |
| Checksums & hashes | `state/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg.yaml` | SHA‑256 hashes for raw files (data hygiene). |

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `ssh: connect to host … Connection refused` | Node unreachable or firewall | Verify IP, ensure SSH port 22 open, test manually with `ssh user@IP`. |
| `tcpdump: command not found` | Missing tool on node | Install via package manager (`apt-get install tcpdump`). |
| Run exceeds 6 h limit | Too many replicates or high node count | Reduce `runs_per_config` or drop highest‑latency setting. |
| High packet loss (> 20 %) aborts run | Wi‑Fi saturation or external traffic | Reduce injected latency, move to a less congested channel, or abort as per spec. |
| Unit tests fail on parsing | Real node output format differs from mock samples | Update `instrumentor.py` parsing regexes; add new sample files to `tests/unit/samples/`. |
| Calibration step fails | Missing `iperf3` or `sysbench` on controller machine | Install via package manager (`apt-get install iperf3 sysbench`). |
| `pytest` reports missing `config.yaml` | File not committed or path typo | Ensure `config.yaml` exists at project root and is tracked by Git. |
| VIF > 5 reported | Predictors highly collinear (e.g., `granularity` and `injected_latency`) | Consider dropping one predictor or reporting interaction only. |

---
