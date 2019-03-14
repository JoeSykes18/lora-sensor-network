CFLAGS=-I./lmic -I/usr/local/include -I/usr/include/python2.7 
LDFLAGS=-L/usr/local/lib -lwiringPi -lprotobuf -lzmq

mailman: lora_mailman.cpp
	cd ./lmic && $(MAKE)
#protoc -I=./ --cpp_out=./ --python_out=./ ./packet.proto
	$(CC) -lstdc++ $(CFLAGS) -o lora_mailman lora_mailman.cpp lorasensornetwork.pb.cc ./lmic/*.o $(LDFLAGS)

all: mailman

.PHONY: clean

clean:
	rm -f *.o mailman
