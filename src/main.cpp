#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

static const char *DEVICE_NAME = "Irrigation Controller";
static const char *FIRMWARE_VERSION = "0.1.0-dev";

static const char *SERVICE_UUID = "7b6a0001-4f7a-4f2e-9f1b-91b0f3c7d001";
static const char *FIRMWARE_VERSION_CHAR_UUID = "7b6a0002-4f7a-4f2e-9f1b-91b0f3c7d001";

class IrrigationServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer *server) override {
        Serial.println("BLE client connected");
    }

    void onDisconnect(BLEServer *server) override {
        Serial.println("BLE client disconnected");
        Serial.println("Restarting BLE advertising");
        server->getAdvertising()->start();
    }
};

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println("Starting BLE peripheral");

    BLEDevice::init(DEVICE_NAME);

    BLEServer *server = BLEDevice::createServer();
    server->setCallbacks(new IrrigationServerCallbacks());

    BLEService *service = server->createService(SERVICE_UUID);

    BLECharacteristic *firmwareVersionCharacteristic = service->createCharacteristic(
        FIRMWARE_VERSION_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ);

    firmwareVersionCharacteristic->setValue(FIRMWARE_VERSION);

    service->start();

    BLEAdvertising *advertising = BLEDevice::getAdvertising();
    advertising->addServiceUUID(SERVICE_UUID);
    advertising->setScanResponse(true);

    BLEDevice::startAdvertising();

    Serial.println("BLE advertising as: ");
    Serial.println(DEVICE_NAME);
}

void loop() {
    delay(1000);
}
