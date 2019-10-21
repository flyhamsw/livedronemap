from datetime import datetime

import pyexiv2


def convert_fractions_to_float(fraction):
    return fraction.numerator / fraction.denominator


def convert_dms_to_deg(dms):
    d = convert_fractions_to_float(dms[0])
    m = convert_fractions_to_float(dms[1]) / 60
    s = convert_fractions_to_float(dms[2]) / 3600
    deg = d + m + s
    return deg


def extract_eo(fname):
    metadata = pyexiv2.ImageMetadata(fname)
    metadata.read()

    latitude = metadata['Exif.GPSInfo.GPSLatitude'].value
    longitude = metadata['Exif.GPSInfo.GPSLongitude'].value
    altitude = metadata['Xmp.drone-dji.AbsoluteAltitude'].value

    latitude = convert_dms_to_deg(latitude)
    longitude = convert_dms_to_deg(longitude)
    altitude = float(altitude)
    roll = float(metadata['Xmp.drone-dji.FlightRollDegree'].value)
    pitch = float(metadata['Xmp.drone-dji.FlightPitchDegree'].value)
    yaw = float(metadata['Xmp.drone-dji.FlightYawDegree'].value)

    result = {
        'longitude': longitude,
        'latitude': latitude,
        'altitude': altitude,
        'yaw': yaw,
        'pitch': pitch,
        'roll': roll
    }

    return result


def get_create_time(fname):
    metadata = pyexiv2.ImageMetadata(fname)
    metadata.read()
    create_time_local = metadata['Exif.Image.DateTime'].value
    create_time = (create_time_local - datetime(1970, 1, 1)).total_seconds() - 3600*9  # GMT+9 (S.Korea)
    return create_time


if __name__ == '__main__':
    print(get_create_time('server/image_processing/test.jpg'))
