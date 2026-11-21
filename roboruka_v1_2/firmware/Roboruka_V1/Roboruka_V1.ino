#include <Wire.h>
#include <math.h>

// ROBORUKA v1.2 — ESP32 + MPU6050 (USB Serial)
// SDA=GPIO25, SCL=GPIO33, MPU6050 VCC=3V3, GND=GND.
// Every output line is JSON. Serial Monitor: 115200 baud.
// Send 'R' plus newline to recalibrate neutral orientation.

constexpr uint8_t SDA_PIN = 25;
constexpr uint8_t SCL_PIN = 33;
constexpr uint8_t MPU = 0x68;
constexpr float RAD2DEG = 180.0f / PI;
constexpr float MAX_TILT_DEG = 30.0f;
constexpr float DEAD_ZONE_DEG = 3.0f;
constexpr float MAX_SPEED_PX_S = 650.0f;
constexpr float RESPONSE_EXP = 1.5f;
constexpr float FILTER_TAU_S = 0.45f;
constexpr uint32_t SEND_PERIOD_MS = 20; // 50 Hz

// Flip either of these if the visual cursor travels the wrong way.
constexpr float INVERT_X = 1.0f;
constexpr float INVERT_Y = -1.0f; // Positive pitch usually means move upward

float gyroBiasX = 0, gyroBiasY = 0, gyroBiasZ = 0;
float roll = 0, pitch = 0;
float neutralRoll = 0, neutralPitch = 0;
uint32_t lastSampleUs = 0, lastSendMs = 0, lastProbeMs = 0;
uint32_t sequenceNumber = 0;
uint8_t consecutiveFailures = 0;
bool online = false;

void status(const char *value) {
  Serial.printf("{\"version\":1,\"type\":\"status\",\"state\":\"%s\"}\n", value);
}

bool writeReg(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(MPU);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readMPU(float &ax, float &ay, float &az,
             float &gx, float &gy, float &gz) {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU, (uint8_t)14, (uint8_t)true) != 14) return false;

  int16_t aX = (int16_t)((Wire.read() << 8) | Wire.read());
  int16_t aY = (int16_t)((Wire.read() << 8) | Wire.read());
  int16_t aZ = (int16_t)((Wire.read() << 8) | Wire.read());
  Wire.read(); Wire.read(); // Temperature bytes (unused)
  int16_t gX = (int16_t)((Wire.read() << 8) | Wire.read());
  int16_t gY = (int16_t)((Wire.read() << 8) | Wire.read());
  int16_t gZ = (int16_t)((Wire.read() << 8) | Wire.read());

  ax = aX / 16384.0f; ay = aY / 16384.0f; az = aZ / 16384.0f;
  gx = gX / 131.0f; gy = gY / 131.0f; gz = gZ / 131.0f;
  return true;
}

bool startMPU() {
  Wire.beginTransmission(MPU);
  if (Wire.endTransmission() != 0) return false;
  return writeReg(0x6B, 0x01) && // Wake up; PLL clock
         writeReg(0x1A, 0x03) && // Low-pass filter
         writeReg(0x19, 0x04) && // Sample-rate divider
         writeReg(0x1B, 0x00) && // +/-250 deg/s
         writeReg(0x1C, 0x00);   // +/-2 g
}

bool calibrate() {
  status("calibrating");
  // Keep sensor still and at a comfortable neutral angle.
  delay(700);
  double sx = 0, sy = 0, sz = 0, sr = 0, sp = 0;
  float minGX = 10000, maxGX = -10000;
  float minGY = 10000, maxGY = -10000;
  int good = 0;
  const int N = 350;

  for (int i = 0; i < N; ++i) {
    float ax, ay, az, gx, gy, gz;
    if (readMPU(ax, ay, az, gx, gy, gz)) {
      float mag = sqrtf(ax*ax + ay*ay + az*az);
      if (mag > 0.85f && mag < 1.15f) {
        sx += gx; sy += gy; sz += gz;
        sr += atan2f(ay, az) * RAD2DEG;
        sp += atan2f(-ax, sqrtf(ay*ay + az*az)) * RAD2DEG;
        if (gx < minGX) minGX = gx;
        if (gx > maxGX) maxGX = gx;
        if (gy < minGY) minGY = gy;
        if (gy > maxGY) maxGY = gy;
        ++good;
      }
    }
    delay(3);
  }
  if (good < 300) { status("calibration_failed"); return false; }
  if ((maxGX - minGX) > 12.0f || (maxGY - minGY) > 12.0f) {
    status("keep_still");
    return false;
  }

  gyroBiasX = sx / good; gyroBiasY = sy / good; gyroBiasZ = sz / good;
  neutralRoll = sr / good; neutralPitch = sp / good;
  roll = neutralRoll; pitch = neutralPitch;
  lastSampleUs = micros();
  lastSendMs = millis();
  sequenceNumber = 0;
  consecutiveFailures = 0;
  status("ready");
  return true;
}

float joystick(float angle) {
  float magnitude = fabsf(angle);
  if (magnitude <= DEAD_ZONE_DEG) return 0;
  float t = (magnitude - DEAD_ZONE_DEG) / (MAX_TILT_DEG - DEAD_ZONE_DEG);
  t = constrain(t, 0.0f, 1.0f);
  return copysignf(MAX_SPEED_PX_S * powf(t, RESPONSE_EXP), angle);
}

void setup() {
  Serial.begin(115200);
  delay(400);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000); // More forgiving than 400 kHz for prototype wiring
  Wire.setTimeOut(30);
  status("starting");
  lastProbeMs = millis() - 2000;
}

void loop() {
  // A failed/disconnected sensor never traps the firmware permanently.
  // We retry about once per second so fixing VCC can recover automatically.
  if (!online) {
    if ((uint32_t)(millis() - lastProbeMs) >= 1000) {
      lastProbeMs = millis();
      if (startMPU() && calibrate()) {
        online = true;
      } else {
        status("sensor_missing_or_unstable");
      }
    }
    delay(10);
    return;
  }

  // Serial command R = recalibrate in the current neutral pose.
  while (Serial.available()) {
    int command = Serial.read();
    if (command == 'R' || command == 'r') {
      if (!calibrate()) online = false;
      return;
    }
  }

  float ax, ay, az, gx, gy, gz;
  if (!readMPU(ax, ay, az, gx, gy, gz)) {
    if (++consecutiveFailures >= 3) {
      online = false;
      status("sensor_lost");
      lastProbeMs = millis();
    }
    delay(5);
    lastSampleUs = micros();
    return;
  }
  consecutiveFailures = 0;

  uint32_t nowUs = micros();
  float dt = (uint32_t)(nowUs - lastSampleUs) * 1e-6f;
  lastSampleUs = nowUs;
  if (dt <= 0 || dt > 0.1f) return;

  gx -= gyroBiasX;
  gy -= gyroBiasY;
  // gz is intentionally not integrated (MPU6050 cannot provide stable absolute yaw).

  float aRoll = atan2f(ay, az) * RAD2DEG;
  float aPitch = atan2f(-ax, sqrtf(ay*ay + az*az)) * RAD2DEG;
  float alpha = FILTER_TAU_S / (FILTER_TAU_S + dt);
  float predictedRoll = roll + gx * dt;
  float predictedPitch = pitch + gy * dt;
  float magnitude = sqrtf(ax*ax + ay*ay + az*az);
  if (magnitude > 0.85f && magnitude < 1.15f) {
    roll = alpha*predictedRoll + (1-alpha)*aRoll;
    pitch = alpha*predictedPitch + (1-alpha)*aPitch;
  } else {
    roll = predictedRoll;
    pitch = predictedPitch;
  }

  float vx = INVERT_X * joystick(roll - neutralRoll);
  float vy = INVERT_Y * joystick(pitch - neutralPitch);

  if ((uint32_t)(millis() - lastSendMs) >= SEND_PERIOD_MS) {
    lastSendMs = millis();
    Serial.printf(
      "{\"version\":1,\"type\":\"motion\",\"sequence\":%lu,"
      "\"timestamp_us\":%lu,\"roll\":%.2f,\"pitch\":%.2f,"
      "\"vx\":%.2f,\"vy\":%.2f,\"quality\":1}\n",
      (unsigned long)sequenceNumber++, (unsigned long)micros(),
      roll, pitch, vx, vy
    );
  }
  delay(5);
}
