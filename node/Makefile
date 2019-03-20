CFLAGS=-I./lmic -I/usr/local/include -I/usr/include/python2.7 
LDFLAGS=-L/usr/local/lib -lwiringPi -lzmq

mailman: lora_mailman.cpp
	cd ./lmic && $(MAKE)
	$(CC) -lstdc++ $(CFLAGS) -o lora_mailman lora_mailman.cpp ./lmic/*.o $(LDFLAGS)

all: mailman

.PHONY: clean

clean:
	rm -f *.o mailman
