#ifndef COUNTER_PACKED_HPP
#define COUNTER_PACKED_HPP

#include <cstdint>
#include <atomic>

// Packed counter structure: No padding between members.
// Expected size: 8 (atomic) + 8 (padding) + 8 (data) = 24 bytes (on 64-bit).
// This structure is prone to false sharing if multiple threads access
// different instances that reside on the same cache line.
#pragma pack(push, 1)
struct CounterPacked {
    std::atomic<long> value;
    char padding[8]; // Explicit padding to align next member if needed, but struct remains packed
    long data;

    CounterPacked() : value(0), data(0) {
        // Initialize padding to 0 for safety, though not strictly required for logic
        for(int i = 0; i < 8; ++i) padding[i] = 0;
    }
};
#pragma pack(pop)

static_assert(sizeof(CounterPacked) == 24, "CounterPacked must be exactly 24 bytes");

#endif // COUNTER_PACKED_HPP
