CXX = g++
CXXFLAGS = -O3 -march=native -Wall -Wextra
TARGETS = matmul

all: $(TARGETS)

matmul: matmul.cpp
	$(CXX) $(CXXFLAGS) -o matmul matmul.cpp

clean:
	rm -f $(TARGETS)

.PHONY: all clean