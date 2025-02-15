# import gpxpy
# import gpxpy.gpx
import os
from ProtoDecoders import DeviceUpdate_pb2

directory = "locations/"
os.makedirs(directory, exist_ok=True)

# wrapped_location = WrappedLocation(
#                 decrypted_location=decrypted_location,
#                 time=int(time.seconds),
#                 accuracy=loc.geoLocation.accuracy,
#                 status=loc.status,
#                 is_own_report=loc.geoLocation.encryptedReport.isOwnReport,
#                 name=""
#             )


def save_location(loc, request_name):
    # open directory/request_name.gpx 
    if not os.path.exists(directory + request_name + ".csv"):
        # if not, create a new file
            os.makedirs(directory, exist_ok=True)
            # write the header to the file, "time,latitude,longitude,altitude,desc"
            with open(directory + request_name + ".csv", "w") as f:
                f.write("time,latitude,longitude,altitude,desc\n")
                f.close()
    # if last location is not identical to current location, append it to the file
    with open(directory + request_name + ".csv", "a+") as f:
        proto_loc = DeviceUpdate_pb2.Location()
        proto_loc.ParseFromString(loc.decrypted_location)

        latitude = proto_loc.latitude / 1e7
        longitude = proto_loc.longitude / 1e7
        altitude = proto_loc.altitude
        time_stamp = loc.time
        desc = f"is_own_report-{loc.is_own_report}--status-{loc.status}--accuracy-{loc.accuracy}"
        print(f"Longitude: {longitude}")
        print(f"Latitude: {latitude}")
        print(f"Altitude: {altitude}")
        print(f"Time: {time_stamp}")
        print(f"Desc: {desc}")
        # check that time stamp is not the same as the last time stamp
        f.seek(0)
        lines = f.readlines()
        if not lines or lines[-1].split(',')[0] != str(time_stamp):
            # create a new point to csv file "time,latitude,longitude,altitude,desc\n"
            f.write(f"{time_stamp},{latitude},{longitude},{altitude},{desc}\n")
            print (f"Saved location to {directory + request_name + '.csv'}")    
        else:
            print("Location is identical to last location, skipping.")
    
        