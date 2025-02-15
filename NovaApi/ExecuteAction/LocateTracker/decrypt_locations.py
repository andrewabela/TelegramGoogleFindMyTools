#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import datetime
import hashlib

from FMDNCrypto.foreign_tracker_cryptor import decrypt
from KeyBackup.cloud_key_decryptor import decrypt_eik, decrypt_aes_gcm
from NovaApi.ExecuteAction.LocateTracker.decrypted_location import WrappedLocation
from ProtoDecoders import DeviceUpdate_pb2
from ProtoDecoders import Common_pb2
from ProtoDecoders.DeviceUpdate_pb2 import DeviceRegistration
from ProtoDecoders.decoder import parse_device_update_protobuf
from SpotApi.GetEidInfoForE2eeDevices.get_owner_key import get_owner_key
from SpotApi.CreateBleDevice.create_ble_device import mcu_fast_pair_model_id, flip_bits


# Indicates if the device is a custom microcontroller
def is_mcu_tracker(device_registration: DeviceRegistration) -> bool:
    return device_registration.fastPairModelId == mcu_fast_pair_model_id


def retrieve_identity_key(device_registration: DeviceRegistration) -> bytes:
    is_mcu = is_mcu_tracker(device_registration)

    encrypted_identity_key = flip_bits(
        device_registration.encryptedUserSecrets.encryptedIdentityKey,
        is_mcu)
    owner_key = get_owner_key()

    identity_key = decrypt_eik(owner_key, encrypted_identity_key)

    return identity_key


def decrypt_location_response_locations(device_update_protobuf, telegram_server):

    device_registration = device_update_protobuf.deviceMetadata.information.deviceRegistration

    identity_key = retrieve_identity_key(device_registration)
    locations_proto = device_update_protobuf.deviceMetadata.information.locationInformation.reports.recentLocationAndNetworkLocations
    is_mcu = is_mcu_tracker(device_registration)

    # At All Areas Reports or Own Reports
    recent_location = locations_proto.recentLocation
    recent_location_time = locations_proto.recentLocationTimestamp

    # High Traffic Reports
    network_locations = list(locations_proto.networkLocations)
    network_locations_time = list(locations_proto.networkLocationTimestamps)

    if locations_proto.HasField("recentLocation"):
        network_locations.append(recent_location)
        network_locations_time.append(recent_location_time)

    location_time_array = []
    for loc, time in zip(network_locations, network_locations_time):

        if loc.status == Common_pb2.Status.SEMANTIC:
            telegram_server.send_message("Semantic Location Report")

            wrapped_location = WrappedLocation(
                decrypted_location=b'',
                time=int(time.seconds),
                accuracy=0,
                status=loc.status,
                is_own_report=True,
                name=loc.semanticLocation.locationName
            )
            location_time_array.append(wrapped_location)
        else:

            encrypted_location = loc.geoLocation.encryptedReport.encryptedLocation
            public_key_random = loc.geoLocation.encryptedReport.publicKeyRandom

            if public_key_random == b"":  # Own Report
                identity_key_hash = hashlib.sha256(identity_key).digest()
                decrypted_location = decrypt_aes_gcm(identity_key_hash, encrypted_location)
            else:
                time_offset = 0 if is_mcu else loc.geoLocation.deviceTimeOffset
                decrypted_location = decrypt(identity_key, encrypted_location, public_key_random, time_offset)

            wrapped_location = WrappedLocation(
                decrypted_location=decrypted_location,
                time=int(time.seconds),
                accuracy=loc.geoLocation.accuracy,
                status=loc.status,
                is_own_report=loc.geoLocation.encryptedReport.isOwnReport,
                name=""
            )
            location_time_array.append(wrapped_location)

    telegram_server.send_message("-" * 40)
    telegram_server.send_message("[DecryptLocations] Decrypted Locations:")

    if not location_time_array:
        telegram_server.send_message("No locations found.")
        return

    for loc in location_time_array:
        msg_parts = []

        if loc.status == Common_pb2.Status.SEMANTIC:
            msg_parts.append(f"Semantic Location: {loc.name}")
        else:
            proto_loc = DeviceUpdate_pb2.Location()
            proto_loc.ParseFromString(loc.decrypted_location)

            latitude = proto_loc.latitude / 1e7
            longitude = proto_loc.longitude / 1e7
            altitude = proto_loc.altitude

            msg_parts.append(f"Latitude: {latitude}")
            msg_parts.append(f"Longitude: {longitude}")
            msg_parts.append(f"Altitude: {altitude}")

        msg_parts.append(f"Time: {datetime.datetime.fromtimestamp(loc.time).strftime('%Y-%m-%d %H:%M:%S')}")
        msg_parts.append(f"Status: {loc.status}")
        msg_parts.append(f"Is Own Report: {loc.is_own_report}")

        telegram_server.send_message("\n".join(msg_parts))

    latest_update = location_time_array[0]
    for loc in location_time_array:
        if datetime.datetime.fromtimestamp(loc.time) > datetime.datetime.fromtimestamp(latest_update.time):
            latest_update = loc
    
    telegram_server.send_message("The latest update is:")
    proto_loc = DeviceUpdate_pb2.Location()
    proto_loc.ParseFromString(latest_update.decrypted_location)
    latitude = proto_loc.latitude / 1e7
    longitude = proto_loc.longitude / 1e7
    altitude = proto_loc.altitude
    telegram_server.send_message(f"Latest Location: {latest_update.name}\nLatitude: {latitude}\nLongitude: {longitude}\nAltitude: {altitude}\nTime: {datetime.datetime.fromtimestamp(latest_update.time).strftime('%Y-%m-%d %H:%M:%S')}\nStatus: {latest_update.status}\nAccuracy: {latest_update.accuracy}\nIs Own Report: {latest_update.is_own_report}")
        


if __name__ == '__main__':
    res = parse_device_update_protobuf("")
    decrypt_location_response_locations(res)