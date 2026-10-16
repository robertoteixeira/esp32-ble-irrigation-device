# ESP32 BLE Irrigation Device

A small ESP32 BLE peripheral prototype for developing and testing a mobile-to-device connection. It advertises as **Irrigation Controller** and exposes a read-only firmware version through a custom GATT service. A Linux simulator implements the same BLE contract for development without the ESP32 firmware running.

The current implementation is the communication foundation: it does not operate pumps or valves, read soil sensors, or schedule watering.

## Implemented behavior

- Advertise a custom service and device name.
- Accept a BLE central connection.
- Return a UTF-8 firmware version from a readable characteristic.
- Log connection state over serial and restart ESP32 advertising after a disconnect.
- Provide an equivalent Linux BlueZ/D-Bus GATT peripheral simulator.

## BLE contract

| Item | Value |
| --- | --- |
| Device name | `Irrigation Controller` |
| Service UUID | `7b6a0001-4f7a-4f2e-9f1b-91b0f3c7d001` |
| Firmware version characteristic | `7b6a0002-4f7a-4f2e-9f1b-91b0f3c7d001` |
| Characteristic property | Read |
| Encoding | UTF-8 |
| Current value | `0.1.0-dev` |

The characteristic does not support writes or notifications. Firmware and simulator share these identifiers.

## Build and flash the ESP32

Requirements: an ESP32 board compatible with PlatformIO's `esp32dev` configuration, a USB data cable, and PlatformIO Core or the VS Code extension. The firmware uses the Arduino framework and ESP32 BLE libraries.

```sh
git clone https://github.com/robertoteixeira/esp32-ble-irrigation-device.git
cd esp32-ble-irrigation-device
pio run
pio run --target upload
pio device monitor --baud 115200
```

Select the appropriate upload/monitor port for your board if automatic detection fails. No external sensor or actuator wiring is required for the implemented firmware-version service.

## Run the Linux simulator

The simulator uses Linux BlueZ, the system D-Bus, Python 3, `dbus-python`, and PyGObject/GLib. It expects a powered Bluetooth adapter at `/org/bluez/hci0` that supports LE advertising and GATT server registration.

On Debian/Ubuntu, the Python bindings are commonly available as `python3-dbus` and `python3-gi`; install the appropriate packages for your distribution and enable Bluetooth before running:

```sh
python3 simulator/ble_peripheral.py
```

Run it with an account permitted to register services and advertisements on the system bus. If the adapter is not `hci0`, update `ADAPTER_PATH` in the script. Registration failures are printed in the terminal. Stop with Ctrl+C to unregister the advertisement and application.

The simulator is a Linux peripheral implementation, not a macOS or Windows Bluetooth emulator.

## Connect from iOS

Use [iOS BLE Device Explorer](https://github.com/robertoteixeira/ios-ble-device-explorer):

1. Run the ESP32 firmware or Linux simulator.
2. Choose **Scan Irrigation Device** in the app.
3. Connect to **Irrigation Controller**.
4. Confirm that the firmware version reads `0.1.0-dev`.
5. Disconnect and scan again to check that the peripheral becomes discoverable.

A generic GATT explorer can also read the characteristic using the UUIDs above.

## Repository layout

- `src/main.cpp`: ESP32 BLE peripheral and connection callbacks.
- `platformio.ini`: board, framework, and serial monitor configuration.
- `simulator/ble_peripheral.py`: BlueZ GATT application and advertisement.

## Validation and status

The firmware build command checks compilation. The connection/read/disconnect sequence above is a manual integration check; there is no automated hardware test suite in this repository. This is an early personal prototype, with no implemented watering-control protocol or application-level authentication.
