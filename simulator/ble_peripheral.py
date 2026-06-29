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
        print("GetManagedObjects called")
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
                "UUID": dbus.String(self.uuid),
                "Primary": dbus.Boolean(self.primary),
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
        print("Service GetAll called:", interface)
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
                "UUID": dbus.String(self.uuid),
                "Flags": dbus.Array(self.flags, signature="s"),
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        print("Characteristic GetAll called:", interface)
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

    @dbus.service.method(
        GATT_CHARACTERISTIC_IFACE,
        in_signature="a{sv}",
        out_signature="ay",
    )
    def ReadValue(self, options):
        print("Firmware version read")
        return text_to_dbus_byte_array(FIRMWARE_VERSION)

class Advertisement(dbus.service.Object):
    PATH_BASE = "/org/bluez/example/advertisement"

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.advertising_type = advertising_type
        self.service_uuids = []
        self.local_name = None
        self.includes = []

        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = {
            "Type": self.advertising_type,
        }

        if self.service_uuids:
            properties["ServiceUUIDs"] = dbus.Array(
                self.service_uuids,
                signature="s",
            )

        if self.local_name:
            properties["LocalName"] = dbus.String(self.local_name)

        if self.includes:
            properties["Includes"] = dbus.Array(
                self.includes,
                signature="s",
            )

        return {
            LE_ADVERTISEMENT_IFACE: properties
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service_uuid(self, uuid):
        self.service_uuids.append(uuid)

    def add_local_name(self, name):
        self.local_name = name

    def add_include(self, include):
        self.includes.append(include)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise dbus.exceptions.DBusException(
                "Invalid interface",
                name="org.freedesktop.DBus.Error.InvalidArgs",
            )

        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature="", out_signature="")
    def Release(self):
        print("Advertisement released")

class IrrigationAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_service_uuid(SERVICE_UUID)
        self.add_local_name(DEVICE_NAME)

def register_app_cb():
    print("GATT application registered")

def register_app_error_cb(error):
    print("Failed to register GATT application:", error)
    mainloop.quit()

def register_ad_cb():
    print("Advertisement registered")

def register_ad_error_cb(error):
    print("Failed to register advertisement:", error)
    mainloop.quit()

def main():
    global mainloop

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    adapter = bus.get_object(BLUEZ_SERVICE_NAME, ADAPTER_PATH)

    service_manager = dbus.Interface(
        adapter,
        GATT_MANAGER_IFACE,
    )

    advertising_manager = dbus.Interface(
        adapter,
        LE_ADVERTISING_MANAGER_IFACE,
    )

    app = Application(bus)
    advertisement = IrrigationAdvertisement(bus, 0)

    service_manager.RegisterApplication(
        app.get_path(),
        {},
        reply_handler=register_app_cb,
        error_handler=register_app_error_cb,
    )

    advertising_manager.RegisterAdvertisement(
        advertisement.get_path(),
        {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb,
    )

    print("BLE irrigation simulator running")
    print("Device name:", DEVICE_NAME)
    print("Service UUID:", SERVICE_UUID)
    print("Press Ctrl+C to stop")

    mainloop = GLib.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("Stopping BLE irrigation simulator")
    finally:
        try:
            advertising_manager.UnregisterAdvertisement(advertisement.get_path())
            print("Advertisement unregistered")
        except dbus.exceptions.DBusException as error:
            print("Advertisement unregister skipped:", error)

        try:
            service_manager.UnregisterApplication(app.get_path())
            print("GATT application unregistered")
        except dbus.exceptions.DBusException as error:
            print("GATT unregister skipped:", error)

if __name__ == "__main__":
    main()
