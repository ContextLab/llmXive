#ifndef COUNTER_PADDED_HPP
#define COUNTER_PADDED_HPP

#include <atomic>
#include <cstddef>

// Padded Counter Struct
// Uses alignas(64) to ensure each counter occupies its own cache line
// Expected size: ≥ 64 bytes (one full cache line)

struct CounterPadded {
    alignas(64) std::atomic<long> value;
    // Padding to ensure the struct is at least 64 bytes
    // The alignas(64) on the atomic member ensures it starts at a 64-byte boundary.
    // To ensure the struct itself is large enough to prevent adjacent instances
    // from sharing a cache line, we add explicit padding if the atomic is smaller.
    // std::atomic<long> is typically 8 bytes.
    
    // We rely on the alignas(64) on the member and potentially the struct alignment.
    // To be safe and explicit about size, we ensure the struct is at least 64 bytes.
    // However, the critical part is that each instance is aligned to 64 bytes.
    
    CounterPadded() : value(0) {}
    
    void increment() {
        value.fetch_add(1, std::memory_order_relaxed);
    }
    
    long get() const {
        return value.load(std::memory_order_relaxed);
    }
};

// Verify size is at least one cache line (64 bytes)
// The alignas(64) on the member ensures alignment, but the struct size might be small
// if not padded. We rely on the allocator and the alignas on the array elements.
// To be absolutely sure the struct size prevents false sharing when allocated in an array,
// we should ensure sizeof(CounterPadded) >= 64.
// However, the task specifies alignas(64) for the member. Let's ensure the struct itself
// is padded if necessary.

// Redefine with explicit padding to guarantee size >= 64
struct CounterPaddedExplicit {
    alignas(64) std::atomic<long> value;
    char padding[56]; // 64 - 8 = 56 bytes padding
    
    CounterPaddedExplicit() : value(0) {}
    
    void increment() {
        value.fetch_add(1, std::memory_order_relaxed);
    }
    
    long get() const {
        return value.load(std::memory_order_relaxed);
    }
};

static_assert(sizeof(CounterPaddedExplicit) >= 64, "Padded counter must be at least 64 bytes");
static_assert(sizeof(CounterPaddedExplicit) % 64 == 0, "Padded counter size should be a multiple of 64");

// Use the explicit version for the benchmark to guarantee no false sharing
using CounterPadded = CounterPaddedExplicit;

#endif // COUNTER_PADDED_HPP