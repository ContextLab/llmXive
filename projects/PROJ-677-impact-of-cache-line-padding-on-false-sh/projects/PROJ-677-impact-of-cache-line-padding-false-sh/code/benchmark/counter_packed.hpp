#ifndef COUNTER_PACKED_HPP
#define COUNTER_PACKED_HPP

#include <atomic>
#include <cstddef>

// Packed Counter Struct
// Uses #pragma pack(1) to force minimal alignment, resulting in false sharing
// Expected size: 3 threads * (8 bytes atomic + 8 bytes padding + 8 bytes atomic) ≈ 24 bytes total
// but with 3 counters in a struct, it's 3 * 8 = 24 bytes exactly.

#pragma pack(push, 1)
struct CounterPacked {
    std::atomic<long> value;
    
    CounterPacked() : value(0) {}
    
    void increment() {
        value.fetch_add(1, std::memory_order_relaxed);
    }
    
    long get() const {
        return value.load(std::memory_order_relaxed);
    }
};
#pragma pack(pop)

// Verify size is minimal (expected ~8 bytes per counter, but struct overhead might vary)
// We expect this to be smaller than 64 bytes to encourage false sharing when multiple
// instances are allocated contiguously.
static_assert(sizeof(CounterPacked) <= 32, "Packed counter should be small");

#endif // COUNTER_PACKED_HPP
