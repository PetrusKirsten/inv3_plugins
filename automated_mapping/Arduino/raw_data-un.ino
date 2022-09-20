#include <compat/deprecated.h>
#include <FlexiTimer2.h>  
#define SAMPFREQ 256                    // ADC sampling rate 256
#define TIMER2VAL (1024/(SAMPFREQ))     // Set 256 Hz sampling frequency  
                  
volatile unsigned char CurrentCh = 0;   // Current channel being sampled.
volatile unsigned int ADC_Value = 0;    // ADC current value
volatile unsigned int smpCounter;
const int ledPin = 4;
int incomingByte;

void setup(){
 noInterrupts();  // Disable all interrupts before initialization
 smpCounter = 0; // setup sample counter
 FlexiTimer2::set(TIMER2VAL, Timer2_Overflow_ISR);
 FlexiTimer2::start();
 Serial.begin(9600);
 pinMode(ledPin, OUTPUT);
 digitalWrite(ledPin, LOW);
 interrupts();  // Enable all interrupts after initialization has been completed
}

void Timer2_Overflow_ISR(){
  ADC_Value = analogRead(CurrentCh);
  // Serial.write(ADC_Value); // print sample
  Serial.println(ADC_Value, DEC); // print sample
}

void loop(){
  __asm__ __volatile__ ("sleep");
  if (Serial.available() > 0) {
    incomingByte = Serial.read();

    if (incomingByte == 'H') {
      digitalWrite(ledPin, HIGH);
      delay(50);
      digitalWrite(ledPin, LOW);
      delay(1000);
    }
    if (incomingByte == 'L'){
      digitalWrite(ledPin, LOW);
    }
  }
}
