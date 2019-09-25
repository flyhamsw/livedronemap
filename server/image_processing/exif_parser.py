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
    altitude = metadata['Exif.GPSInfo.GPSAltitude'].value

    latitude = convert_dms_to_deg(latitude)
    longitude = convert_dms_to_deg(longitude)
    altitude = convert_fractions_to_float(altitude)
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


if __name__ == '__main__':
    print(extract_eo('test.jpg'))
