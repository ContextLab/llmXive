# Quickstart: Mesh Network Supercomputer Using Pooled Idle Computing Resources

## Prerequisites

- **Local Machine**: Linux/macOS with Python 3.11+
- **Testbed Devices**: 10–20 heterogeneous devices (laptops, Raspberry Pis, mobile devices) on the same Wi-Fi network
- **SSH Access**: Passwordless SSH keys configured for all testbed devices
- **CLI Tools**: `tcpdump`, `mpstat`, `iperf`, `ping` installed on testbed devices
- **Network**: Local Wi-Fi network with ability to inject latency (e.g., `tc` command on Linux)

## Installation

```bash
# Clone repository
git clone <repo-url>
cd projects/PROJ-009-build-a-mesh-network-that-forms-the-larg

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Configuration

1. **Create `config.yaml`** in the project root:
```yaml
testbed:
  nodes:
    - ip: "192.168.1.101"
      hardware: "Raspberry Pi 4"
    - ip: "192.168.1.102"
      hardware: "Laptop Intel i7"
    # Add more nodes...
  network:
    base_latency_ms: 10
    packet_loss_rate: 0.01
    bandwidth_mbps: 100
    snr_db: 25

benchmark:
  granularity: ["fine", "medium", "coarse"]
  node_counts: [10, 15, 20]
  injected_latencies: [0, 50, 100, 200]
  runs_per_config: 5

analysis:
  random_seed: 42
  max_runtime_hours: 6
```

2. **Verify SSH connectivity**:
```bash
python code/orchestrator/node_manager.py --verify
```

## Execution

### Run a Single Benchmark

```bash
python code/orchestrator/scheduler.py --config config.yaml --granularity fine --nodes 15 --latency 100
```

This will:
1. Deploy tasks to 15 nodes
2. Inject 100ms latency
3. Collect execution logs
4. Output `data/raw/run_001.csv`

### Run Full Parameter Sweep

```bash
python code/orchestrator/scheduler.py --config config.yaml --sweep
```

This will:
1. Execute all granularity/node/latency combinations
2. Aggregate results into `data/processed/execution_runs.csv`
3. Fit regression model and output `data/processed/regression_model.json`

### Validate Against Theoretical Bound

```bash
python code/analysis/theoretical_bound.py --config config.yaml --input data/processed/regression_model.json
```

This will:
1. Load regression model results
2. Compute Ong & Motani (2007) bound
3. Output deviation metric and flag if empirical exceeds theoretical

## Testing

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Contract Tests (Schema Validation)

```bash
pytest tests/contract/ -v
```

### Integration Tests (Mocked Testbed)

```bash
pytest tests/integration/ -v --mock-testbed
```

## Output Artifacts

- **Raw Logs**: `data/raw/run_*.csv` (one per execution)
- **Aggregated Metrics**: `data/processed/execution_runs.csv`
- **Regression Model**: `data/processed/regression_model.json`
- **Validation Report**: `data/processed/theoretical_bound_validation.json`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| SSH connection refused | Verify SSH keys and firewall settings |
| `tcpdump` not found | Install `tcpdump` on testbed devices |
| Memory overflow on low-end device | Reduce `estimated_ops` in benchmark config |
| Run exceeds 6-hour limit | Reduce `runs_per_config` or node count |
| High packet loss detected | Check Wi-Fi interference; abort run if >20% |
