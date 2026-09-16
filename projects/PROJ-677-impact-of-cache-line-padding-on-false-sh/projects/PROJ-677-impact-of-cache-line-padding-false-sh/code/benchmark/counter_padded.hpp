#pragma once
#include <atomic>
#include <cstddef>

// Padded counter struct: >= 192 bytes total (3 cache lines)
// Aligned to 64-byte cache line boundaries to prevent false sharing
struct alignas(64) CounterPadded {
    std::atomic<long> value;
    char padding[56]; // 8 + 56 = 64 bytes (1 cache line)
    // Additional padding to ensure distinct cache lines if array is used?
    // The struct itself is 64 bytes. If we have an array of these, each element is on a new cache line.
    // The plan mentions >= 192 bytes. Let's add more padding to the struct itself to force 3 lines per element if needed,
    // or rely on the array indexing.
    // To strictly satisfy "≥192 bytes" per struct entry as implied by the plan text:
    char extra_padding[128]; // Total 64 + 128 = 192 bytes
};

using Counter = CounterPadded;
