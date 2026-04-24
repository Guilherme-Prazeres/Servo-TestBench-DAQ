#include <Servo.h>
#include "HX711_ADC.h"
#include <EEPROM.h>

// --- Moving Average Filter Class ---
// Change this value to make the filter stronger (higher number = smoother but slower to react)
#define FILTER_SIZE 15

enum SystemState {
  WAITING_FOR_CONNECTION,
  INITIALIZATION,
  IDLE,
  RUNNING,
  TARE,
  MAX_TORQUE_TEST,
  ERROR_STATE
};

// --- NEW: Sub-states for the torque test ---
enum TestPhase {
  NONE,
  STARTING,
  PULLING,
  COOLDOWN
};

TestPhase currentTestPhase = NONE;

SystemState currentState = WAITING_FOR_CONNECTION;
class MovingAverage {
  private:
    float readings[FILTER_SIZE];
    int readIndex = 0;
    float total = 0;

  public:
    MovingAverage() {
      // Initialize all readings to 0
      for (int i = 0; i < FILTER_SIZE; i++) {
        readings[i] = 0.0;
      }
    }

    // Adds a new reading and returns the current average
    float update(float newReading) {
      total = total - readings[readIndex];       // Subtract the oldest reading
      readings[readIndex] = newReading;          // Add the new reading to the array
      total = total + readings[readIndex];       // Add the new reading to the total
      readIndex = (readIndex + 1) % FILTER_SIZE; // Advance to the next position, wrap around
      
      return total / FILTER_SIZE;                // Return the mean
    }
};



Servo Servo;
unsigned long previousMillis = 0;
const long interval = 50;
const int SERVO_ARM = 1.5; //cm
const int PWM_MAX = 2000;
const int PWM_MIN = 1000;

// Hardware Pin Definitions
const int SERVO_PIN = 3;         // PD3
const int LOADCELL_DOUT_PIN = 6; // PD6 (DT)
const int LOADCELL_SCK_PIN = 7;  // PD7 (SCK)
const int CURRENT_PIN = A3;      // A3
const int VOLTAGE_PIN = A0;      // A0

HX711_ADC LoadCell(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

const int calVal_eepromAdress = 0;

// --- Filter Instances ---
// MovingAverage torqueFilter;
MovingAverage currentFilter;
MovingAverage voltageFilter;
// MovingAverage torqueFilter;

// --- Sensor Configuration ---
const float VREF = 4.81; // Arduino reference voltage (measure your 5V pin for exact accuracy, e.g., 4.98)

// Voltage Divider Constants
const float R1 = 980.0; // 1000 Ohm
const float R2 = 200.0;  // 200 Ohm
const float VOLTAGE_DIVIDER_RATIO = (R1 + R2) / R2; 
const float V_OFFSET = - 0.2;

// ACS712 Constants
// Sensitivities: 5A module = 0.185 (V/A), 20A module = 0.100 (V/A), 30A module = 0.066 (V/A)
const float ACS712_SENSITIVITY = 0.066; 
const float ACS712_OFFSET = VREF / 2.0; // ACS712 outputs Vcc/2 at 0 Amps (usually 2.5V)

void setup() {
  Serial.begin(115200);
  // Serial.setTimeout(5);

  while (currentState == WAITING_FOR_CONNECTION) {
    if (Serial.available() > 0) {
      char incomingByte = Serial.read();
      if (incomingByte == 'C') {           // PC is requesting to connect
        currentState = INITIALIZATION;               // Transition state
        Serial.println("ACK_CONNECT");     // Acknowledge back to the PC
      }
    }
  }
  
  while (currentState == INITIALIZATION){

    Serial.println("INIT_BEGIN");
    Servo.attach(SERVO_PIN);

    Servo.writeMicroseconds(0.1*PWM_MAX);
    delay(200);
    Servo.writeMicroseconds(PWM_MIN);

    float calibrationValue;
    EEPROM.get(calVal_eepromAdress, calibrationValue); 

    LoadCell.begin();
    unsigned long stabilizingtime = 2000; 
    LoadCell.start(stabilizingtime, true);
    
    if (LoadCell.getTareTimeoutFlag()) {
      // Note: We can route this to the ERROR_STATE later
    } else {
      LoadCell.setCalFactor(calibrationValue); 
    }
    
    LoadCell.tare();
    while (LoadCell.getTareStatus() == false){
      delay(100);
    }

    // "Disables" the librarie moving average
    LoadCell.setSamplesInUse(1);
    
    Serial.println("INIT_COMPLETE");
    currentState = IDLE;
  }
}

void sendFormattedTelemetry(float torque, float current, float voltage) {
  // 1. Determine the string name of the current state
  String stateName = "";
  switch (currentState) {
    case IDLE:            stateName = "IDLE"; break;
    case RUNNING:         stateName = "RUNNING"; break;
    case TARE:            stateName = "TARE"; break;
    case ERROR_STATE:     stateName = "ERROR"; break;
    
    // --- NEW: Dynamic state naming for the test ---
    case MAX_TORQUE_TEST: 
      if (currentTestPhase == NONE) stateName = "IDLE";
      else if (currentTestPhase == STARTING) stateName = "STARTING";
      else if (currentTestPhase == PULLING) stateName = "PULLING";
      else if (currentTestPhase == COOLDOWN) stateName = "COOLDOWN";
      else stateName = "MAX_TORQUE_TEST"; 
      break;
      
    default:              stateName = "SYS"; break;
  }

  // 2. Output the concatenated data
  Serial.print(stateName);
  Serial.print(",");
  Serial.print(torque);
  Serial.print(",");
  Serial.print(current, 2); 
  Serial.print(",");
  Serial.println(voltage, 2); 
}

void readAndSendTelemetry() {
  unsigned long currentMillis = millis();
  static boolean newDataReady = false;
  static float actualTorque = 0.0; // Keep track of the latest filtered torque

  // 1. ASYNC POLLING: Run continuously, outside the interval check
  // This catches data exactly when the HX711 pushes it
  if (LoadCell.dataWaitingAsync()) {
    LoadCell.updateAsync();
    newDataReady = true;
  }

  // Process new torque data the exact millisecond it arrives
  if (newDataReady) {
    float rawTorque = LoadCell.getData(); 
    actualTorque = (rawTorque * 0.001) * SERVO_ARM; 
    
    // Feed your custom filter at the maximum hardware sampling rate
    // actualTorque = torqueFilter.update(instantTorque);
    newDataReady = false;
  }

  // 2. TIMED TELEMETRY: Read analog pins and send data at the set interval
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    // --- Current Reading & Filtering ---
    int rawCurrent = analogRead(CURRENT_PIN);
    float pinVoltageCurrent = (rawCurrent / 1023.0) * VREF;
    float instantCurrent = (pinVoltageCurrent - ACS712_OFFSET) / ACS712_SENSITIVITY;
    float actualCurrent = currentFilter.update(instantCurrent); 

    // --- Voltage Reading & Filtering ---
    int rawVoltage = analogRead(VOLTAGE_PIN);
    float pinVoltageDivider = (rawVoltage / 1023.0) * VREF;
    float instantVoltage = (pinVoltageDivider * VOLTAGE_DIVIDER_RATIO) + V_OFFSET;

    if (instantVoltage > 6.0) {
      instantVoltage -= 0.15; 
    }
    if (instantVoltage <= 3.0) {
      instantVoltage += 0.1; 
    }
    
    float actualVoltage = voltageFilter.update(instantVoltage);

    // --- NEW: Pass the latest filtered variables to the printing function ---
    sendFormattedTelemetry(actualTorque, actualCurrent, actualVoltage);
  }
}

void loop() {
  // COMMAND ROUTER 
  if (Serial.available() > 0) {
    String incomingData = Serial.readStringUntil('\n');
    incomingData.trim(); // Remove any trailing \r or whitespace
    
    if (incomingData.length() > 0) {
      int commaIndex = incomingData.indexOf(',');
      String commandPrefix = "";
      String valueString = "";

      // Split the prefix and the value
      if (commaIndex > 0) {
        commandPrefix = incomingData.substring(0, commaIndex);
        valueString = incomingData.substring(commaIndex + 1);
      } else {
        commandPrefix = incomingData;
      }

      // Route the command based on the prefix
      if (commandPrefix == "SERVO") {
        float servoValue = valueString.toFloat();
        int PWM = PWM_MIN + ((PWM_MAX - PWM_MIN) * servoValue);
        Servo.writeMicroseconds(PWM);

      } else if (commandPrefix == "RUNNING") {
        currentState = RUNNING;

      } else if (commandPrefix == "IDLE") {
        currentState = IDLE;

      } else if (commandPrefix == "TARE") {
        currentState = TARE;

      } else if (commandPrefix == "MAX_TORQUE_TEST") {
        currentState = MAX_TORQUE_TEST;

      } else {
        // Ignore unknown prefixes
      }
    }
  }

  // 2. FSM ENGINE (Executes actions based on current state)
  switch (currentState) {

    case RUNNING:
      readAndSendTelemetry();
      break;

    case TARE:
      Serial.println("TARE");
      delay(300);
      LoadCell.tare();
      while (LoadCell.getTareStatus() == false){
        delay(100);
      }
      currentState = RUNNING;
      break;

    case MAX_TORQUE_TEST:
      {
        
        // --- ADDED: Set phase to stabilizing ---
        currentTestPhase = STARTING;
        unsigned long stabilizeStart = millis();
        while (millis() - stabilizeStart <= 1000) {
          readAndSendTelemetry();
        }

        for (int pull = 1; pull <= 3; pull++) {

          Servo.writeMicroseconds(PWM_MAX);

          // --- ADDED: Set phase to pulling ---
          currentTestPhase = PULLING;
          unsigned long pullStartTime = millis();
          unsigned long pullDuration = 10000; // 10 seconds

          while (millis() - pullStartTime <= pullDuration) {
            readAndSendTelemetry(); 
          }

          Servo.writeMicroseconds(PWM_MIN);

          if (pull < 3) {
            // --- ADDED: Set phase to cooldown ---
            currentTestPhase = COOLDOWN;
            unsigned long cooldownStart = millis();
            while (millis() - cooldownStart <= 3000) {
              readAndSendTelemetry();
            }
          }
        }

        // --- ADDED: Back to stabilizing for the end ---
        currentTestPhase = COOLDOWN;
        unsigned long finalStabilizeStart = millis();
        while (millis() - finalStabilizeStart <= 3000) {
          readAndSendTelemetry();
        }
        
        // --- ADDED: Reset phase and go IDLE ---
        currentTestPhase = NONE; 
        currentState = IDLE;
      }
      break;

    case ERROR_STATE:
      // Safe mode operations here
      break;
      
    case IDLE:
      readAndSendTelemetry();
      break;

    case WAITING_FOR_CONNECTION:
    case INITIALIZATION:
      // These are handled in setup(), do nothing here
      break;
  }
}

