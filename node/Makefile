CFLAGS=-I./lmic -I/usr/local/include -I/usr/include/python2.7 
LDFLAGS=-L/usr/local/lib -lwiringPi -lprotobuf -lzmq

raw: raw.cpp
	cd ./lmic && $(MAKE)
#protoc -I=./ --cpp_out=./ --python_out=./ ./packet.proto
	$(CC) -lstdc++ $(CFLAGS) -o raw loraraw.cpp packet.pb.cc ./lmic/*.o $(LDFLAGS)

all: raw

.PHONY: clean

clean:
	rm -f *.o raw
