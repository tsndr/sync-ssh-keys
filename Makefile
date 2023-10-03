CC=clang
CFLAGS=-O3 -Wall -Wextra -pedantic -lexif
SRC=src/main.c
DEBUG=dist/debug/sync
RELEASE=dist/release/sync

default: $(SRC)
	mkdir -p dist/debug
	$(CC) $(CFLAGS) -o $(DEBUG) -ggdb $(SRC)

release: $(SRC)
	mkdir -p dist/release
	$(CC) $(CFLAGS) -o $(RELEASE) $(SRC)

debug: $(DEBUG)
	lldb $(DEBUG)

run: $(DEBUG)
	./$(DEBUG)

clean:
	rm -rf dist/

test: $(DEBUG) L1000064.JPG 1G5A0135.jpg
	./$(DEBUG) L1000064.JPG
	./$(DEBUG) 1G5A0135.jpg
	./$(DEBUG) L1000064.JPG -f json | jq
	./$(DEBUG) 1G5A0135.jpg -f json | jq

.PHONY: clean
