"""
Runtime guard utilities used by the training loop.

* Warn if a single epoch exceeds 30 minutes.
* Halt the whole run if total wall‑time exceeds 6 hours.
* Log the peak RAM usage (must stay ≤ 6 GB).
"""
import time
import logging
import psutil

log = logging.getLogger(__name__)

# thresholds (seconds)
EPOCH_TIME_WARN = 30 * 60          # 30 min
TOTAL_TIME_LIMIT = 6 * 60 * 60    # 6 h
RAM_LIMIT_BYTES = 6 * 1024 ** 3   # 6 GB

class RuntimeGuard:
    """
    Simple guard that can be instantiated at the start of a training run.
    """
    def __init__(self):
        self.start_time = time.time()
        self.epoch_start = None
        self.peak_ram = 0

    def epoch_started(self):
        """Mark the beginning of an epoch."""
        self.epoch_start = time.time()

    def epoch_finished(self):
        """Mark the end of an epoch and enforce the per‑epoch warning."""
        if self.epoch_start is None:
            raise RuntimeError("epoch_started() must be called before epoch_finished()")
        elapsed = time.time() - self.epoch_start
        if elapsed > EPOCH_TIME_WARN:
            log.warning(
                "Epoch took %.2f minutes (> 30 min). Continuing per FR‑009.",
                elapsed / 60,
            )
        # update peak RAM
        current_ram = psutil.Process().memory_info().rss
        if current_ram > self.peak_ram:
            self.peak_ram = current_ram

        # total‑time check
        total_elapsed = time.time() - self.start_time
        if total_elapsed > TOTAL_TIME_LIMIT:
            log.error(
                "Total runtime %.2f hours exceeds the 6 h limit. Halting per FR‑009.",
                total_elapsed / 3600,
            )
            raise RuntimeError("Total runtime limit exceeded")

    def log_peak_ram(self):
        """Log the peak RAM usage (in GB)."""
        ram_gb = self.peak_ram / (1024 ** 3)
        log.info("Peak RAM usage during training: %.2f GB", ram_gb)
        if self.peak_ram > RAM_LIMIT_BYTES:
            log.error(
                "Peak RAM usage %.2f GB exceeds the 6 GB limit.", ram_gb
            )
            raise RuntimeError("RAM usage limit exceeded")
