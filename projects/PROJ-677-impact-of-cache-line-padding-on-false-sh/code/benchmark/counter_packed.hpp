#pragma once

#include <atomic>
#include <cstdint>

// Packed counter struct: 24 bytes total (3 * 8 bytes)
// No padding between members, leading to potential false sharing
#pragma pack(push, 1)
struct CounterPacked {
    std::atomic<long> value1;
    std::atomic<long> value2;
    std::atomic<long> value3;

    CounterPacked() : value1(0), value2(0), value3(0) {}
};
#pragma pack(pop)

static_assert(sizeof(CounterPacked) == 24, "CounterPacked must be exactly 24 bytes");
