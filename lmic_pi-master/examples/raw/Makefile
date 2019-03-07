CFLAGS=-I../../lmic
LDFLAGS=-lwiringPi

raw: raw.cpp
	cd ../../lmic && $(MAKE)
	$(CC) $(CFLAGS) -o raw raw.cpp ../../lmic/*.o $(LDFLAGS)

all: raw

.PHONY: clean

clean:
	rm -f *.o raw
