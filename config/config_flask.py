import json
from abc import *


class BaseConfig(object, metaclass=ABCMeta):
    DEBUG = False
    TESTING = False
    UPLOAD_FOLDER = '/hdd/ldm_workspace'
    ALLOWED_EXTENSIONS = set(['JPG', 'jpg', 'txt', 'tiff'])
    WEBODM_CONFIG = json.load(open('config/config_webodm.json', 'r'))
    MAGO3D_CONFIG = json.load(open('config/config_mago3d.json', 'r'))
    LOG_DB_PATH = 'server/livedronemap_log.db'
    SIMULATION_ID = None
    CALIBRATION = True
    GEOREFERENCING_METHOD = 'NEIGHBOR_AT_PHOTOSCAN'  # DIRECT_GEOREFERENCING, NEIGHBOR_AT_PHOTOSCAN
