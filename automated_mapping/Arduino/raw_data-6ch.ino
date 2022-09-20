#include <compat/deprecated.h>
#include <FlexiTimer2.h>
#define SAMPFREQ 256*6                   // ADC sampling rate 256
#define TIMER2VAL (1024/(SAMPFREQ))    // Set 256 Hz sampling frequency  
                  
volatile unsigned char CurrentCh = 0;  // Current channel being sampled.
volatile unsigned int ADC_Value = 0;   // ADC current value
volatile unsigned int ADC_Value1 = 0;  // ADC current
volatile unsigned int ADC_Value2 = 0;  // ADC current
volatile unsigned int ADC_Value3 = 0;  // ADC current
volatile unsigned int ADC_Value4 = 0;  // ADC current 
volatile unsigned int ADC_Value5 = 0;  // ADC current 
volatile unsigned int smpCounter;
const int ledPin = 4;
int incomingByte;


void setup(){
 noInterrupts();  // Disable all interrupts before initialization
 smpCounter = 0; // setup sample counter
 FlexiTimer2::set(TIMER2VAL, Timer2_Overflow_ISR);
 FlexiTimer2::start();
 Serial.begin(9600);
volatile unsigned int ADC_Value2 = 0;  // ADC current 
volatile unsigned int ADC_Value3 = 0;  // ADC current );
 interrupts();  // Enable all interrupts after initialization has been completed
}

void Timer2_Overflow_ISR(){
  ADC_Value = analogRead(CurrentCh);
  ADC_Value1 = analogRead(1);
  ADC_Value2 = analogRead(2);
  ADC_Value3 = analogRead(3);
  ADC_Value4 = analogRead(4);
  ADC_Value5 = analogRead(5);

  Serial.println(ADC_Value, DEC);      //the first variable for plotting
  Serial.println(ADC_Value1, DEC);  
  Serial.println(ADC_Value2, DEC);   
  Serial.println(ADC_Value3, DEC);   
  Serial.println(ADC_Value4, DEC);        
  Serial.println(ADC_Value5, DEC);   
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
