
#include <Wire.h>
#include <math.h>

#define SDA_PIN 25
#define SCL_PIN 33
#define MPU_ADDR 0x68

// MPU6050 registers
#define PWR_MGMT_1   0x6B
#define CONFIG_REG   0x1A
#define SMPLRT_DIV   0x19
#define GYRO_CONFIG  0x1B
#define ACCEL_CONFIG 0x1C
#define ACCEL_XOUT_H 0x3B

// Joystick settings
const float MAX_TILT = 30.0f;   // Degrees
const float DEAD_ZONE = 3.0f;   // Degrees
const float MAX_SPEED = 900.0f; // Pixels/second
const float FILTER_TAU = 0.5f;  // Seconds
const float RESPONSE_EXP = 1.5f;

// Orientation
float roll = 0, pitch = 0;
float neutralRoll = 0, neutralPitch = 0;

// Gyroscope calibration
float offsetGX = 0, offsetGY = 0, offsetGZ = 0;

// Cursor velocity
float vx = 0, vy = 0;

uint32_t lastUpdate = 0;
uint32_t lastSend = 0;
uint32_t sequence = 0;

bool writeReg(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readMPU(float &ax, float &ay, float &az,
             float &gx, float &gy, float &gz) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(ACCEL_XOUT_H);

  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU_ADDR, 14, true) != 14)
    return false;

  int16_t aX = (Wire.read() << 8) | Wire.read();
  int16_t aY = (Wire.read() << 8) | Wire.read();
  int16_t aZ = (Wire.read() << 8) | Wire.read();

  Wire.read();
  Wire.read();

  int16_t gX = (Wire.read() << 8) | Wire.read();
  int16_t gY = (Wire.read() << 8) | Wire.read();
  int16_t gZ = (Wire.read() << 8) | Wire.read();

  ax = aX / 16384.0f;
  ay = aY / 16384.0f;
  az = aZ / 16384.0f;

  gx = gX / 131.0f;
  gy = gY / 131.0f;
  gz = gZ / 131.0f;

  return true;
}

float joystickResponse(float angle) {
  float magnitude = fabsf(angle);

  if (magnitude <= DEAD_ZONE) return 0.0f;

  float normalized =
    (magnitude - DEAD_ZONE) /
    (MAX_TILT - DEAD_ZONE);

  normalized = constrain(normalized, 0.0f, 1.0f);

  float response = powf(normalized, RESPONSE_EXP);

  return copysignf(response * MAX_SPEED, angle);
}

void calibrate() {
  Serial.println("Calibrating - keep sensor still!");
  delay(2000);

  double sumGX = 0, sumGY = 0, sumGZ = 0;
  double sumRoll = 0, sumPitch = 0;
  int count = 0;

  for (int i = 0; i < 1000; i++) {
    float ax, ay, az, gx, gy, gz;

    if (readMPU(ax, ay, az, gx, gy, gz)) {
      sumGX += gx;
      sumGY += gy;
      sumGZ += gz;

      sumRoll += atan2f(ay, az) * 180.0f / PI;
      sumPitch += atan2f(
        -ax, sqrtf(ay * ay + az * az)
      ) * 180.0f / PI;

      count++;
    }
    delay(3);
  }

  if (count < 500) {
    Serial.println("Calibration failed!");
    while (true) delay(1000);
  }

  offsetGX = sumGX / count;
  offsetGY = sumGY / count;
  offsetGZ = sumGZ / count;

  neutralRoll = sumRoll / count;
  neutralPitch = sumPitch / count;

  roll = neutralRoll;
  pitch = neutralPitch;

  Serial.println("Calibration complete!");
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  Wire.beginTransmission(MPU_ADDR);
  if (Wire.endTransmission() != 0) {
    Serial.println("MPU6050 not found!");
    while (true) delay(1000);
  }

  if (!writeReg(PWR_MGMT_1, 0x01) ||
      !writeReg(CONFIG_REG, 0x03) ||
      !writeReg(SMPLRT_DIV, 0x04) ||
      !writeReg(GYRO_CONFIG, 0x00) ||
      !writeReg(ACCEL_CONFIG, 0x00)) {
    Serial.println("MPU configuration failed!");
    while (true) delay(1000);
  }

  calibrate();

  lastUpdate = micros();
  lastSend = millis();
}

void loop() {
  float ax, ay, az, gx, gy, gz;

  if (!readMPU(ax, ay, az, gx, gy, gz)) {
    delay(5);
    lastUpdate = micros();
    return;
  }

  uint32_t now = micros();
  float dt = (uint32_t)(now - lastUpdate) * 1e-6f;
  lastUpdate = now;

  if (dt <= 0 || dt > 0.1f) return;

  gx -= offsetGX;
  gy -= offsetGY;
  gz -= offsetGZ;

  // Accelerometer tilt
  float accelRoll = atan2f(ay, az) * 180.0f / PI;
  float accelPitch = atan2f(
    -ax, sqrtf(ay * ay + az * az)
  ) * 180.0f / PI;

  // Time-dependent complementary filter
  float alpha = FILTER_TAU / (FILTER_TAU + dt);

  float predictedRoll = roll + gx * dt;
  float predictedPitch = pitch + gy * dt;

  float accelMagnitude = sqrtf(
    ax * ax + ay * ay + az * az
  );

  if (accelMagnitude > 0.85f &&
      accelMagnitude < 1.15f) {
    roll = alpha * predictedRoll +
           (1 - alpha) * accelRoll;

    pitch = alpha * predictedPitch +
            (1 - alpha) * accelPitch;
  } else {
    roll = predictedRoll;
    pitch = predictedPitch;
  }

  // Relative tilt from neutral position
  float relativeRoll = roll - neutralRoll;
  float relativePitch = pitch - neutralPitch;

  // Joystick velocities
  vx = joystickResponse(relativeRoll);
  vy = joystickResponse(relativePitch);

  // JSON messages at 50 Hz
  if ((uint32_t)(millis() - lastSend) >= 100) {
    lastSend = millis();

    Serial.printf(
      "{\"version\":1,\"type\":\"motion\","
      "\"sequence\":%lu,"
      "\"timestamp_us\":%lu,"
      "\"roll\":%.2f,\"pitch\":%.2f,"
      "\"vx\":%.2f,\"vy\":%.2f}\n",
      (unsigned long)sequence++,
      (unsigned long)micros(),
      roll, pitch, vx, vy
    );
  }
}
