/*******************************************************************************
 * Copyright (c) 2015 Matthijs Kooijman
 *
 * Permission is hereby granted, free of charge, to anyone
 * obtaining a copy of this document and accompanying files,
 * to do whatever they want with them without any restriction,
 * including, but not limited to, copying, modification and redistribution.
 * NO WARRANTY OF ANY KIND IS PROVIDED.
 *
 * This example transmits data on hardcoded channel and receives data
 * when not transmitting. Running this sketch on two nodes should allow
 * them to communicate.
 *******************************************************************************/

#include <wiringPi.h>
//#include <boost/python.hpp>
#include <zmq.hpp>
#include <stdio.h>
#include <lmic.h>
#include <hal.h>
#include <local_hal.h>
//#include <SPI.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <string.h>

#if !defined(DISABLE_INVERT_IQ_ON_RX)
#error This example requires DISABLE_INVERT_IQ_ON_RX to be set. Update \
       config.h in the lmic library to set it.
#endif

// How often to send a packet. Note that this sketch bypasses the normal
// LMIC duty cycle limiting, so when you change anything in this sketch
// (payload length, frequency, spreading factor), be sure to check if
// this interval should not also be increased.
// See this spreadsheet for an easy airtime and duty cycle calculator:
// https://docs.google.com/spreadsheets/d/1voGAtQAjC1qBmaVuP1ApNKs1ekgUjavHuVQIXyYSvNc 
#define TX_INTERVAL 2000

// Pin mapping
lmic_pinmap pins = {
  .nss = 6,
  .rxtx = UNUSED_PIN, // Not connected on RFM92/RFM95
  .rst = 0,  // Needed on RFM92/RFM95
  .dio = {7,4,5}
};

// These callbacks are only used in over-the-air activation, so they are
// left empty here (we cannot leave them out completely unless
// DISABLE_JOIN is set in config.h, otherwise the linker will complain).
void os_getArtEui (u1_t* buf) { }
void os_getDevEui (u1_t* buf) { }
void os_getDevKey (u1_t* buf) { }

void onEvent (ev_t ev) {
}

osjob_t txjob;
osjob_t timeoutjob;
static void tx_func (osjob_t* job);
void receive(zmq::socket_t & socket, std::string& output); 
static void printArr(unsigned char* arr);

// Transmit the given string and call the given function afterwards
void tx(const std::string & packet) {
  os_radio(RADIO_RST); // Stop RX first
  sleep(1); // Wait a bit, without this os_radio below asserts, apparently because the state hasn't changed yet
  
  fprintf(stdout, "[MAILMAN] Preparing to transmit packet: ");
  fprintf(stdout, packet.c_str());
  fprintf(stdout, "...");
  
  LMIC.dataLen = 0;
  
  for (char c : packet) {
    LMIC.frame[LMIC.dataLen++] = c;
  }
  
  //LMIC.osjob.func = func;
  os_radio(RADIO_TX);
  fprintf(stdout, "transmitted\n");
}

// Enable rx mode and call func when a packet is received
void rx(osjobcb_t func) {
  LMIC.osjob.func = func;
  LMIC.rxtime = os_getTime(); // RX _now_
  // Enable "continuous" RX (e.g. without a timeout, still stops after
  // receiving a packet)
  os_radio(RADIO_RXON);
  fprintf(stdout, "RX\n");
}

static void rxtimeout_func(osjob_t *job) {
  //digitalWrite(LED_BUILTIN, LOW); // off
  fprintf(stdout, "Receive timedout\n");
}

static void rx_func (osjob_t* job) {
  // Blink once to confirm reception and then keep the led on
  //digitalWrite(LED_BUILTIN, LOW); // off
  //delay(10);
  //digitalWrite(LED_BUILTIN, HIGH); // on

  // Timeout RX (i.e. update led status) after 3 periods without RX
  os_setTimedCallback(&timeoutjob, os_getTime() + ms2osticks(3*TX_INTERVAL), rxtimeout_func);

  // Reschedule TX so that it should not collide with the other side's
  // next TX
  //os_setTimedCallback(&txjob, os_getTime() + ms2osticks(TX_INTERVAL/2), tx_func);

  fprintf(stdout, "[MAILMAN] Got %d bytes\n", LMIC.dataLen);
  printArr(LMIC.frame);

  // Restart RX
  rx(rx_func);
}

static void printArr(unsigned char* arr) {
  int i;
  for (i=0; i < (sizeof(arr) / sizeof(arr[0])); ++i) {
    fprintf(stdout, "%s", arr[i]);
  }
  fprintf(stdout, " (frame was %d bytes long)\n", i);
}

static void txdone_func (osjob_t* job) {
  rx(rx_func);
}

// log text to USART and toggle LED
static void tx_func (osjob_t* job) {
  // say hello
  //tx("101110", txdone_func);
  // reschedule job every TX_INTERVAL (plus a bit of random to prevent
  // systematic collisions), unless packets are received, then rx_func
  // will reschedule at half this time.
  //int rando = rand() % 500;
  //os_setTimedCallback(job, os_getTime() + ms2osticks(TX_INTERVAL + rando), tx_func);
}

// application entry point
void setup() {
  // Init LMIC
  wiringPiSetup();

  // Init random util
  srand(time(NULL));

  // initialize runtime env
  os_init();

  // Set up these settings once, and use them for both TX and RX
#if defined(CFG_eu868)
  // Use a frequency in the g3 which allows 10% duty cycling.
  LMIC.freq = 869525000;
#elif defined(CFG_us915)
  LMIC.freq = 902300000;
#endif

  // Maximum TX power
  LMIC.txpow = 27;
  
  // Use a medium spread factor. This can be increased up to SF12 for
  // better range, but then the interval should be (significantly)
  // lowered to comply with duty cycle limits as well.
  LMIC.datarate = DR_SF7;
  
  // This sets CR 4/5, BW125 (except for DR_SF7B, which uses BW250)
  LMIC.rps = updr2rps(LMIC.datarate);

  // setup initial job
  //os_setCallback(&txjob, tx_func);
}

void check_transmissions(zmq::socket_t & socket) {
    // Check for any outbound packets to send
    zmq::message_t mq_msg;
    socket.recv(&mq_msg);
    fprintf(stdout, "[MAILMAN] Packet received on message queue...");

    fprintf(stdout, "[MAILMAN] packet length:");
    fprintf(stdout, std::to_string(mq_msg.size()).c_str());

    std::string pkt_str = std::string(static_cast<char*>(mq_msg.data()), mq_msg.size()); 

    if (pkt_str.length() == 0) {
      fprintf(stdout, "packet on queue had length 0 so transmission finishing.\n");
      return;
    }

    fprintf(stdout, "\n");

    tx(pkt_str);

    fprintf(stdout, "[MAILMAN] Waiting for LoRa reply...");

    std::string loraReply;
    receive(socket, loraReply);

    fprintf(stdout, "received LoRa reply. Sending to python node...");

    zmq::message_t ack(5);
    memcpy(ack.data(), loraReply.c_str(), 5);
    socket.send(ack);

    fprintf(stdout, "sent.\n"); 
}

void receive(zmq::socket_t & socket, std::string& output) {
    fprintf(stdout, "[MAILMAN] Checking for incoming LoRa packets...");
    rx(rx_func);

    if (LMIC.dataLen == 0) {
      output = "FAILED";
      return;
    }

    output = "";
    output.append(reinterpret_cast<const char*>(LMIC.frame));
}

void loop() {
  // Set up ZeroMQ socket to receive/deposit packets
  zmq::context_t context(1);
  zmq::socket_t socket(context, ZMQ_REP);
  socket.bind("tcp://*:5555");

  fprintf(stdout, "[MAILMAN] Binded to ZeroMQ socket, listening...\n");

  while(1) {
    fprintf(stdout, "Loop\n");

    check_transmissions(socket);

    //receive(socket);
  }
}


int main() {
  fprintf(stdout, "==== Mailman Started ====\n[MAILMAN] Setting up...");
  setup();
  fprintf(stdout, "set up. Starting loop...\n");
  
  loop();

  return 0;
}
