#pragma once

#include <atomic>
#include <cstdint>
#include <cstddef>

// Cache line size constant (typical x86_64)
constexpr size_t CACHE_LINE_SIZE = 64;

// Padded counter struct: each atomic is on its own cache line
// Total size >= 192 bytes (3 * 64 bytes)
struct alignas(CACHE_LINE_SIZE) CounterPadded {
    alignas(CACHE_LINE_SIZE) std::atomic<long> value1;
    alignas(CACHE_LINE_SIZE) std::atomic<long> value2;
    alignas(CACHE_LINE_SIZE) std::atomic<long> value3;

    CounterPadded() : value1(0), value2(0), value3(0) {}
};

static_assert(sizeof(CounterPadded) >= 192, "CounterPadded must be at least 192 bytes");
static_assert(alignof(CounterPadded) >= CACHE_LINE_SIZE, "CounterPadded must be cache-line aligned");
