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
Create a `config.yaml` in the project root:

```yaml
testbed:
  nodes:
    - ip: "192.168.1.101"
      hardware: "Raspberry Pi 4"
    - ip: "192.168.1.102"
      hardware: "Laptop Intel i7"
    # Add additional nodes as needed
  network:
    base_latency_ms: <typical baseline latency>   # typical baseline latency
    packet_loss_rate: negligible (approaching zero)
    bandwidth_mbps: sufficient for the intended data transfer.
    snr_db: high

benchmark:
  granularity: ["fine", "medium", "coarse"]
  node_counts: [10, 15, 20]
  injected_latencies: [0, 50, 100, 200]  # ms
  runs_per_config: 2
  random_seed: 42

analysis:
  max_runtime_hours: appropriate duration to be defined during the implementation phase
```

Verify SSH connectivity to all nodes:

```bash
python code/orchestrator/node_manager.py --verify
```

## Calibration (new step)
Before any sweep, run the calibration suite to ensure measurement validity:

```bash
python code/orchestrator/cli.py calibrate --config config.yaml
```

- **Network Calibration**: runs `iperf3` between a designated pair of nodes, stores conversion factors in `data/raw/network_calibration.json`.  
- **CPU Utilization Calibration**: runs `sysbench cpu --threads=1 run`, stores mapping in `data/raw/cpu_calibration.json`.  

## Running the Pipeline

### 1. Single Benchmark Run
```bash
python code/orchestrator/cli.py run \
  --config config.yaml \
  --granularity fine \
  --node-count 15 \
  --injected-latency 100
```
*What happens*:  
- Scheduler distributes the Monte Carlo integration task.  
- Each node records `tcpdump` and `mpstat` logs.  
- Generates per‑node metadata `physical_node_<ip>.json` and a `dropout_events.json` log.  
- Outputs: `data/raw/run_<id>.csv`, `data/raw/physical_node_<ip>.json`, `data/raw/dropout_events.json`, and `data/raw/task_chunks/<run_id>.jsonl`.

### 2. Full Parameter Sweep (Research‑Scale)
```bash
python code/orchestrator/cli.py sweep --config config.yaml
```
*What happens*:  
- Executes every combination of granularity, node count, and injected latency (default 2 replicates each).  
- After each run, calibration files are consulted to correct packet‑count and CPU‑util metrics.  
- Aggregated raw logs are placed under `data/raw/`.  
- After the sweep finishes, the script automatically runs the analysis modules, producing:
  - `data/processed/execution_runs.csv`
  - `data/processed/regression_model.json`
  - `data/processed/theoretical_bound_validation.json`

### 3. Validation Only (if you already have processed data)
```bash
python code/analysis/theoretical_bound.py \
  --input data/processed/regression_model.json \
  --config config.yaml
```

## Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```
Covers node discovery, SSH health checks, metric parsing, scheduler fault handling, and dropout logging.

### Contract Tests (Schema Validation)
```bash
pytest tests/contract/ -v
```
Ensures every JSON/CSV output conforms to the schemas in `contracts/`.

### Integration Tests (Mock Testbed)
```bash
pytest tests/integration/ -v --mock-testbed
```
Runs the entire workflow on a synthetic mesh of mock nodes; verifies that the final artefacts exist and pass schema validation.

## Output Artefacts
| Artifact | Location | Description |
|----------|----------|-------------|
| Raw execution logs | `data/raw/run_*.csv` | One row per task chunk, includes timing, CPU, packet counts |
| Dropout events | `data/raw/dropout_events.json` | JSON array of node dropout/re‑assignment events |
| Physical node metadata | `data/raw/physical_node_*.json` | Per‑node baseline and runtime metrics |
| TaskChunk records | `data/raw/task_chunks/<run_id>.jsonl` | JSON‑Lines of each dispatched chunk, validated against schema |
| Aggregated metrics | `data/processed/execution_runs.csv` | One row per configuration (throughput, efficiency, overhead) |
| Regression model | `data/processed/regression_model.json` | Coefficients, p‑values, R² |
| Theoretical bound validation | `data/processed/theoretical_bound_validation.json` | Deviation ratio, scaling‑law exponent comparison, flag for bound violation |
| Checksums & hashes | `state/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg.yaml` | SHA‑256 hashes for raw files |

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `ssh: connect to host … Connection refused` | Node unreachable or firewall | Verify IP address, ensure SSH port 22 is open, test manually with `ssh user@IP`. |
| `tcpdump: command not found` | Missing tool on node | Install via package manager (`apt-get install tcpdump` on Debian/Ubuntu). |
| Run exceeds 6 h limit | Too many replicates or high node count | Reduce `runs_per_config` or drop the highest‑latency setting. |
| High packet loss (> 20 %) aborts run | Wi‑Fi saturation or external traffic | Reduce injected latency, move to a less congested channel, or abort as per spec. |
| Unit tests fail on parsing | Real node output format differs from mock samples | Update `instrumentor.py` parsing regexes; add new sample files to `tests/unit/samples/`. |
| Calibration step fails | Missing `iperf3` or `sysbench` on controller machine | Install via package manager (`apt-get install iperf3 sysbench`). |

---


