from abc import *
import math
import numpy as np


class BaseDrone(metaclass=ABCMeta):
    polling_config = {
        'asked_health_check': False,
        'asked_sim': False,
        'checklist_result': None,
        'polling_time': 0.5,
        'timeout': 10
    }

    @abstractmethod
    def get_drone_name(self):
        pass

    @abstractmethod
    def get_camera_manufacturer_name(self):
        pass

    @abstractmethod
    def preprocess_eo_file(self, eo_path):
        """
        This abstract function parses a given EO file and returns parsed_eo (see below).
        It SHOULD BE implemented for each drone classes.

        An example of parsed_eo
        parsed_eo = [latitude, longitude, altitude, omega, phi, kappa]
        Unit of omega, phi, kappa: radian
        """
        pass

    # @abstractmethod
    def calibrate_initial_eo(self):
        pass


class FlirVueProR(BaseDrone):
    def __init__(self, pre_calibrated=False):
        self.ipod_params = {
            "sensor_width": 10.88,
            'focal_length': 0.013,
            'gsd': 0.25,
            'ground_height': 363.7,
            "R_CB": np.array([[0.996892729, -0.01561805212,   -0.0772072755],
                              [0.01841927538, 0.999192656, 0.03570387246],
                              [0.07658731773, -0.03701503292, 0.9963755668]], dtype=float)  # 191029
        }
        self.pre_calibrated = pre_calibrated

    def get_drone_name(self):
        return "FlirVueProR"

    def get_camera_manufacturer_name(self):
        return 'FlirVueProR'

    def preprocess_eo_file(self, eo_path):
        eo_line = np.genfromtxt(
            eo_path,
            delimiter='\t',
            dtype={
                'names': ('Image', 'Longitude', 'Latitude', 'Altitude', 'Yaw', 'Pitch', 'Roll'),
                'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')
            }
        )

        eo_line['Roll'] = eo_line['Roll'] * math.pi / 180
        eo_line['Pitch'] = eo_line['Pitch'] * math.pi / 180
        eo_line['Yaw'] = eo_line['Yaw'] * math.pi / 180

        parsed_eo = [float(eo_line['Longitude']), float(eo_line['Latitude']), float(eo_line['Altitude']),
                     float(eo_line['Roll']), float(eo_line['Pitch']), float(eo_line['Yaw'])]

        return parsed_eo


class AIMIFYFlirDuoProR(BaseDrone):
    def __init__(self, pre_calibrated=False):
        # self.ipod_params = {
        #     "sensor_width": 7.4,
        #     'focal_length': 0.008,
        #     'gsd': 'auto',
        #     'ground_height': 12.0,
        #     "R_CB": np.array(
        #         [[0.998424007914030, -0.0558051944297136, -0.00593975551236918],
        #         [-0.00675010686299412, -0.0143438195676995, -0.999874337553249],
        #         [0.0557129830310944,    0.998338637494749, -0.0146979048474889]], dtype=float)
        # }
        # TODO: 광나루 실험 (2019년 11월 6일)
        self.ipod_params = {
            "sensor_width": 7.4,
            'focal_length': 0.008,
            'gsd': 'auto',
            'ground_height': 12.0,
            "R_CB": np.eye(3, 3)
        }
        self.pre_calibrated = pre_calibrated

    def get_drone_name(self):
        return "AIMIFYFlirDuoProR"

    def get_camera_manufacturer_name(self):
        return 'AIMIFY/FLIR/Visible'

    def preprocess_eo_file(self, eo_path):
        eo_line = np.genfromtxt(
            eo_path,
            delimiter='\t',
            dtype={
                'names': ('Image', 'Longitude', 'Latitude', 'Altitude', 'Yaw', 'Pitch', 'Roll'),
                'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')
            }
        )

        eo_line['Roll'] = eo_line['Roll'] * math.pi / 180
        eo_line['Pitch'] = eo_line['Pitch'] * math.pi / 180
        eo_line['Yaw'] = eo_line['Yaw'] * math.pi / 180

        parsed_eo = [float(eo_line['Longitude']), float(eo_line['Latitude']), float(eo_line['Altitude']),
                     float(eo_line['Roll']), float(eo_line['Pitch']), float(eo_line['Yaw'])]

        return parsed_eo


class AIMIFYSONY(BaseDrone):
    def __init__(self, pre_calibrated=False):
        self.ipod_params = {
            "sensor_width": 23.5,
            'focal_length': 0.020,
            'gsd': 'auto',
            'ground_height': 0,
            "R_CB": np.array(
                [[0.994367334553110, 0.0724297138251540, -0.0773791995884510],
                [-0.0736697531217240, 0.997194145601333, -0.0132892232057198],
                [0.0761995501871716, 0.0189148759877907, 0.996913163729740]], dtype=float)
        }
        self.pre_calibrated = pre_calibrated

    def get_drone_name(self):
        return "AIMIFYSONY"

    def get_camera_manufacturer_name(self):
        return 'AIMIFY/SONY'

    def preprocess_eo_file(self, eo_path):
        eo_line = np.genfromtxt(
            eo_path,
            delimiter='\t',
            dtype={
                'names': ('Image', 'Longitude', 'Latitude', 'Altitude', 'Yaw', 'Pitch', 'Roll'),
                'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')
            }
        )

        eo_line['Roll'] = eo_line['Roll'] * math.pi / 180
        eo_line['Pitch'] = eo_line['Pitch'] * math.pi / 180
        eo_line['Yaw'] = eo_line['Yaw'] * math.pi / 180

        parsed_eo = [float(eo_line['Longitude']), float(eo_line['Latitude']), float(eo_line['Altitude']),
                     float(eo_line['Roll']), float(eo_line['Pitch']), float(eo_line['Yaw'])]

        return parsed_eo


class DJIMavic(BaseDrone):
    def __init__(self, pre_calibrated=False):
        self.ipod_params = {
            "sensor_width": 6.3,
            'focal_length': 0.0047,
            'gsd': 'auto',
            'ground_height': 363.7,
            "R_CB": np.array(
                [[0.996270284462972, -0.0845707313471919, -0.0171263450703691],
                 [0.0857291664934870, 0.992672993233668, 0.0851518556277114],
                 [0.00979950551814992, -0.0863024907167326, 0.996220783655756]], dtype=float)
        }
        self.pre_calibrated = pre_calibrated

    def get_drone_name(self):
        return "DJI Mavic"

    def get_camera_manufacturer_name(self):
        return 'DJI'

    def preprocess_eo_file(self, eo_path):
        eo_line = np.genfromtxt(
            eo_path,
            delimiter='\t',
            dtype={
                'names': ('Image', 'Longitude', 'Latitude', 'Altitude', 'Yaw', 'Pitch', 'Roll'),
                'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')
            }
        )

        eo_line['Roll'] = eo_line['Roll'] * math.pi / 180
        eo_line['Pitch'] = eo_line['Pitch'] * math.pi / 180
        eo_line['Yaw'] = eo_line['Yaw'] * math.pi / 180

        parsed_eo = [float(eo_line['Longitude']), float(eo_line['Latitude']), float(eo_line['Altitude']),
                     float(eo_line['Roll']), float(eo_line['Pitch']), float(eo_line['Yaw'])]

        return parsed_eo


class DJIPhantom4RTK(BaseDrone):
    def __init__(self, pre_calibrated=False):
        self.ipod_params = {
            "sensor_width": 6.3,
            'focal_length': 0.0088,
            'gsd': 'auto',
            'ground_height': 27.91387,
            "R_CB": np.array(
                [[0.992103011532570, -0.0478682839576757, -0.115932057253170],
                 [0.0636038625107261, 0.988653550290218, 0.136083452970098],
                 [0.108102558627082, -0.142382530141501, 0.983890772356761]], dtype=float)
        }
        self.pre_calibrated = pre_calibrated

    def get_drone_name(self):
        return "DJI Phantom 4 RTK"

    def get_camera_manufacturer_name(self):
        return 'DJI'

    def preprocess_eo_file(self, eo_path):
        eo_line = np.genfromtxt(
            eo_path,
            delimiter='\t',
            dtype={
                'names': ('Image', 'Longitude', 'Latitude', 'Altitude', 'Yaw', 'Pitch', 'Roll'),
                'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')
            }
        )

        eo_line['Roll'] = eo_line['Roll'] * math.pi / 180
        eo_line['Pitch'] = eo_line['Pitch'] * math.pi / 180
        eo_line['Yaw'] = eo_line['Yaw'] * math.pi / 180

        parsed_eo = [float(eo_line['Longitude']), float(eo_line['Latitude']), float(eo_line['Altitude']),
                     float(eo_line['Roll']), float(eo_line['Pitch']), float(eo_line['Yaw'])]

        return parsed_eo


class TiLabETRI(BaseDrone):
    def __init__(self, pre_calibrated=False):
        self.ipod_params = {
            "sensor_width": 23.5,
            "focal_length": 0.0016,
            "gsd": 0.25,
            "ground_height": 27.0,
        }
        self.pre_calibrated = pre_calibrated

    def get_drone_name(self):
        return "DJI M600 with TiLab-ETRI real-time transmission system"

    def get_camera_manufacturer_name(self):
        return 'SONY'

    def preprocess_eo_file(self, eo_path):
        with open(eo_path, 'r') as f:
            data = f.readline().split(' ')
            lat = data[1].split('=')[1]
            lon = data[2].split('=')[1]
            alt = data[3].split('=')[1]
            kappa = (float(data[6].split('=')[1]) + 90.0) * math.pi / 180
            parsed_eo = [float(lon), float(lat), float(alt), 0.0, 0.0, float(kappa)]

            return parsed_eo
