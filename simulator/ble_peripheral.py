import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

from gi.repository import GLib


BLUEZ_SERVICE_NAME = "org.bluez"
ADAPTER_PATH = "/org/bluez/hci0"

DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"

LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"

GATT_MANAGER_IFACE = "org.bluez.GattManager1"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHARACTERISTIC_IFACE = "org.bluez.GattCharacteristic1"

DEVICE_NAME = "Irrigation Controller"
FIRMWARE_VERSION = "0.1.0-dev"

SERVICE_UUID = "7b6a0001-4f7a-4f2e-9f1b-91b0f3c7d001"
FIRMWARE_VERSION_CHAR_UUID = "7b6a0002-4f7a-4f2e-9f1b-91b0f3c7d001"

def text_to_dbus_byte_array(value):
    return [dbus.Byte(byte) for byte in value.encode("utf-8")]

class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = "/"
        self.services = [
            IrrigationService(bus, 0),
        ]

        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature="a{oa{sa{sv}}}")
    def GetManagedObjects(self):
        response = {}

        for service in self.services:
            response[service.get_path()] = service.get_properties()

            for characteristic in service.characteristics:
                response[characteristic.get_path()] = characteristic.get_properties()

        return response

class Service(dbus.service.Object):
    PATH_BASE = "/org/bluez/example/service"

    def __init__(self, bus, index, uuid, primary):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []

        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                "UUID": self.uuid,
                "Primary": self.primary,
                "Characteristics": dbus.Array(
                    self.get_characteristic_paths(),
                    signature="o",
                ),
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        return [characteristic.get_path() for characteristic in self.characteristics]

    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise dbus.exceptions.DBusException(
                "Invalid interface",
                name="org.freedesktop.DBus.Error.InvalidArgs",
            )

        return self.get_properties()[GATT_SERVICE_IFACE]

class IrrigationService(Service):
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, SERVICE_UUID, True)
        self.add_characteristic(FirmwareVersionCharacteristic(bus, 0, self))

class Characteristic(dbus.service.Object):
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + "/char" + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags

        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_CHARACTERISTIC_IFACE: {
                "Service": self.service.get_path(),
                "UUID": self.uuid,
                "Flags": self.flags,
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != GATT_CHARACTERISTIC_IFACE:
            raise dbus.exceptions.DBusException(
                "Invalid interface",
                name="org.freedesktop.DBus.Error.InvalidArgs",
            )

        return self.get_properties()[GATT_CHARACTERISTIC_IFACE]

    @dbus.service.method(
        GATT_CHARACTERISTIC_IFACE,
        in_signature="a{sv}",
        out_signature="ay",
    )
    def ReadValue(self, options):
        raise dbus.exceptions.DBusException(
            "Read not supported",
            name="org.bluez.Error.NotSupported",
        )

    @dbus.service.method(
        GATT_CHARACTERISTIC_IFACE,
        in_signature="aya{sv}",
    )
    def WriteValue(self, value, options):
        raise dbus.exceptions.DBusException(
            "Write not supported",
            name="org.bluez.Error.NotSupported",
        )

class FirmwareVersionCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self,
            bus,
            index,
            FIRMWARE_VERSION_CHAR_UUID,
            ["read"],
            service,
        )

    def ReadValue(self, options):
        print("Firmware version read")
        return text_to_dbus_byte_array(FIRMWARE_VERSION)
