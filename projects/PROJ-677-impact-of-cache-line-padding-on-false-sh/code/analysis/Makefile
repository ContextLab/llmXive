# Makefile for C++17 Benchmark Suite
# This Makefile complements CMakeLists.txt for direct compilation without cmake invocation.

CXX := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -O3 -march=native
LDFLAGS :=

# Directories
BENCHMARK_DIR := ../benchmark
BUILD_DIR := ./build

# Source files
VERIFY_SRC := $(BENCHMARK_DIR)/verify_layout.cpp
MAIN_SRC := $(BENCHMARK_DIR)/main.cpp

# Targets
VERIFY_BIN := $(BUILD_DIR)/verify_layout
MAIN_BIN := $(BUILD_DIR)/benchmark_main

.PHONY: all clean build_dirs

all: build_dirs $(VERIFY_BIN) $(MAIN_BIN)

build_dirs:
	@mkdir -p $(BUILD_DIR)

$(VERIFY_BIN): $(VERIFY_SRC)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

$(MAIN_BIN): $(MAIN_SRC)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -rf $(BUILD_DIR)

# Help target
help:
	@echo "Available targets:"
	@echo "  all     - Build all binaries (default)"
	@echo "  clean   - Remove build directory and binaries"
	@echo "  help    - Show this help message"
