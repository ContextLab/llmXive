#pragma once
#include <atomic>
#include <cstddef>

// Cache line size constant
constexpr size_t CACHE_LINE_SIZE = 64;

// Padded counter structure: designed to prevent false sharing
// Each counter occupies its own cache line
struct alignas(CACHE_LINE_SIZE) PaddedCounter {
    std::atomic<long> value;
    char padding[CACHE_LINE_SIZE - sizeof(std::atomic<long>)];
};

static_assert(sizeof(PaddedCounter) >= CACHE_LINE_SIZE, 
              "PaddedCounter must be at least 64 bytes");
static_assert(alignof(PaddedCounter) == CACHE_LINE_SIZE, 
              "PaddedCounter must be aligned to 64 bytes");
