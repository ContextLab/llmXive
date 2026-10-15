# Quickstart: Mesh Network Supercomputer Using Pooled Idle Computing Resources

## Prerequisites
- **Local Machine**: Linux/macOS with Python 3.11+ installed.  
- **Testbed Devices**: 10–20 heterogeneous devices (laptops, Raspberry Pis, Android phones) on the same Wi‑Fi network.  
- **SSH Access**: Password‑less SSH keys configured for every testbed device.  
- **CLI Tools on Nodes**: `tcpdump`, `mpstat`, `iperf`, `ping`, `tc` (for latency injection).  
- **Network**: Ability to shape traffic (e.g., `tc qdisc add ...`).  

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
    base_latency_ms: (baseline latency, on the order of tens of milliseconds)
    packet_loss_rate: low
    bandwidth_mbps: a high bandwidth sufficient for the planned data acquisition
    snr_db: high

benchmark:
  granularity: ["fine", "medium", "coarse"]
  node_counts: [10, 15, 20]
  injected_latencies: [0, 50, 100, 200]  # ms
  runs_per_config: several   # increase for full study
  random_seed: 42

analysis:
  max_runtime_hours: a constrained runtime of a few hours
```

Verify SSH connectivity to all nodes:

```bash
python code/orchestrator/node_manager.py --verify
```

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
- Scheduler distributes the Monte Carlo integration task.  
- Each node records `tcpdump` and `mpstat` logs.  
- A CSV file (e.g., `data/raw/run_<identifier>.csv`) and `data/raw/dropout_events.json` are produced.

### 2. Full Parameter Sweep (Research‑Scale)
```bash
python code/orchestrator/cli.py sweep --config config.yaml
```
*What happens*:  
- Executes every combination of granularity, node count, and injected latency (default 2 replicates each).  
- Aggregated raw logs → `data/raw/`.  
- After the sweep finishes, the script automatically runs `analysis/regression.py` and `analysis/theoretical_bound.py`.  
- Final artefacts:
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
Runs the entire workflow on a synthetic mesh of multiple mock nodes; verifies that the final artefacts exist and pass schema validation.

## Output Artifacts
| Artifact | Location | Description |
|----------|----------|-------------|
| Raw execution logs | `data/raw/run_*.csv` | One row per task chunk, includes timing, CPU, packet counts |
| Dropout events | `data/raw/dropout_events.json` | JSON array of node dropout/re‑assignment events |
| Aggregated metrics | `data/processed/execution_runs.csv` | One row per configuration (throughput, efficiency, overhead) |
| Regression model | `data/processed/regression_model.json` | Coefficients, p‑values, R² |
| Theoretical bound validation | `data/processed/theoretical_bound_validation.json` | Deviation ratio, flag for bound violation |
| Checksums & hashes | `state/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg.yaml` | SHA‑256 hashes for raw files |

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `ssh: connect to host … Connection refused` | Node unreachable or firewall | Verify IP address, ensure SSH port 22 is open, test with `ssh user@IP` manually |
| `tcpdump: command not found` | Missing tool on node | Install `tcpdump` via package manager (`apt-get install tcpdump` on Debian/Ubuntu) |
| Run exceeds 6 h limit | Too many replicates or large node count | Reduce `runs_per_config` or drop the highest‑latency setting |
| High packet loss (> 20 %) aborts run | Wi‑Fi saturation or external interference | Reduce injected latency, move to a less congested channel, or abort as per spec |
| Unit tests fail on parsing | Real node output format differs from mock samples | Update `instrumentor.py` parsing regexes; add new sample files to `tests/unit/samples/` |

---
