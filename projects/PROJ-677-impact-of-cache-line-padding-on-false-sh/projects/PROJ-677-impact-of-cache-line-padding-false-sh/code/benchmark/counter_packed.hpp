#ifndef COUNTER_PACKED_HPP
#define COUNTER_PACKED_HPP

#include <cstdint>
#include <atomic>

// Packed structure: 3 fields, no padding.
// Expected size: 8 (long) + 8 (long) + 8 (long) = 24 bytes.
// This creates false sharing if multiple threads access different fields 
// that fall on the same cache line (64 bytes).
struct __attribute__((packed)) PackedCounter {
    std::atomic<long> a;
    std::atomic<long> b;
    std::atomic<long> c;
};

static_assert(sizeof(PackedCounter) == 24, "PackedCounter must be 24 bytes");

#endif // COUNTER_PACKED_HPP
