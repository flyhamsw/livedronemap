import json
import arrow
import gdal
from server.object_detection.core.ship_yolo.object_detection_yolo import start_ship_detection


def detect_ship(json_template_fname, input_img_path):
    ds = gdal.Open(input_img_path)
    gdal_transform_info = ds.GetGeoTransform()
    geom_info = {
        'gsd': {
            'x': float(gdal_transform_info[1]),
            'y': float(gdal_transform_info[5])
        },
        'ul': {
            'x': float(gdal_transform_info[0]),
            'y': float(gdal_transform_info[3])
        }
    }
    geom_boxes = start_ship_detection(input_img_path, geom_info)
    detected_objects_list = []
    for number, geom_box in enumerate(geom_boxes):
        geometry = 'POINT (%f %f)' % (geom_box['center']['x'], geom_box['center']['y'])
        bounding_box_geometry = 'POLYGON ((%f %f, %f %f, %f %f, %f %f, %f %f))' % (
            geom_box['bounding_box']['coord_1']['x'],
            geom_box['bounding_box']['coord_1']['y'],
            geom_box['bounding_box']['coord_2']['x'],
            geom_box['bounding_box']['coord_2']['y'],
            geom_box['bounding_box']['coord_3']['x'],
            geom_box['bounding_box']['coord_3']['y'],
            geom_box['bounding_box']['coord_4']['x'],
            geom_box['bounding_box']['coord_4']['y'],
            geom_box['bounding_box']['coord_1']['x'],
            geom_box['bounding_box']['coord_1']['y']
        )
        detected_objects = json.load(open(json_template_fname, 'r'))
        detected_objects['number'] = number
        detected_objects['object_type'] = '0'  # 0: 선박탐지, 1: 기름유출
        detected_objects['geometry'] = geometry
        detected_objects['bounding_box_geometry'] = bounding_box_geometry
        detected_objects['detected_date'] = arrow.utcnow().format('YYYYMMDDHHmmss')
        detected_objects['insert_date'] = arrow.utcnow().format('YYYYMMDDHHmmss')
        detected_objects_list.append(detected_objects)
    return detected_objects_list


if __name__ == '__main__':
    detect_ship(json_template_fname=None, input_img_path='test.png')
