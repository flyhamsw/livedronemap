import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
import sqlite3

from flask import Flask, request
from werkzeug.utils import secure_filename

from config import config_flask
from server.image_processing.img_metadata_generation import create_img_metadata
from server.image_processing.system_calibration import calibrate
from clients.webodm import WebODM
from clients.mago3d import Mago3D
from drone.drone_image_check import start_image_check
from server.object_detection.ship_yolo import detect_ship
from server.image_processing.orthophoto_generation.Orthophoto import rectify
from server.image_processing.exif_parser import get_create_time
from server.image_processing.photoscan.run import neighbor_AT

# Initialize flask
app = Flask(__name__)
app.config.from_object(config_flask.BaseConfig)

# Initialize multi-thread
executor = ThreadPoolExecutor(2)

# Initialize Mago3D client
mago3d = Mago3D(
    url=app.config['MAGO3D_CONFIG']['url'],
    user_id=app.config['MAGO3D_CONFIG']['user_id'],
    api_key=app.config['MAGO3D_CONFIG']['api_key']
)

from server.my_drones import FlirVueProR as My_drone
my_drone = My_drone(pre_calibrated=False)


def allowed_file(fname):
    return '.' in fname and fname.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/project/', methods=['GET', 'POST'])
def project():
    """
    GET : Query project list
    POST : Add a new project
    :return: project_list (GET), project_id (POST)
    """
    if request.method == 'GET':
        project_list = os.listdir(app.config['UPLOAD_FOLDER'])
        return json.dumps(project_list)
    if request.method == 'POST':
        if request.json['visualization_module'] == 'MAGO3D':
            # Create a new project on Mago3D
            res = mago3d.create_project(request.json['name'], request.json['project_type'],
                                        request.json['shooting_area'])
            # Mago3D assigns a new project ID to LDM
            project_id = str(res.json()['droneProjectId'])
        elif request.json['visualization_module'] == 'LOCAL':
            project_id = 'LOCAL_%s' % round(time.time())

        # Using the assigned ID, ldm makes a new folder to projects directory
        new_project_dir = os.path.join(app.config['UPLOAD_FOLDER'], project_id)
        os.mkdir(new_project_dir)

        conn = sqlite3.connect(app.config['LOG_DB_PATH'])
        cur = conn.cursor()

        query = 'INSERT INTO project VALUES (?, ?, ?, ?)'
        cur.execute(
            query,
            (
                project_id,
                request.json['name'],
                my_drone.get_drone_name(),
                time.time(),
            )
        )
        conn.commit()
        conn.close()

        # LDM returns the project ID that Mago3D assigned
        return project_id


# 라이브 드론맵: 이미지 업로드, 기하보정 및 가시화
@app.route('/ldm_upload/<project_id_str>', methods=['POST'])
def ldm_upload(project_id_str):
    """
    POST : Input images to the image processing and object detection chain of LDM
    The image processing and object detection chain of LDM covers following procedures.
        1) System calibration
        2) Individual ortho-image generation
        3) Object detection (red tide, ship, etc.)
    :param project_id_str: project_id which Mago3D assigned for each projects
    :return:
    """
    if request.method == 'POST':
        # Initialize variables
        project_path = os.path.join(app.config['UPLOAD_FOLDER'], project_id_str)
        # fname_time = str(round(time.time()))
        # fname_dict = {
        #     'img': my_drone.get_drone_name() + '_' + fname_time + '.JPG',
        #     'img_rectified': None,
        #     'eo': my_drone.get_drone_name() + '_' + fname_time + '.txt',
        #     'img_metadata': None,
        # }
        fname_dict = {
            'img': None,
            'img_orig': None,
            'img_rectified': None,
            'eo': None,
            'img_metadata': None,
        }

        # Establish connection to log DB
        conn = sqlite3.connect(app.config['LOG_DB_PATH'])
        cur = conn.cursor()

        # Check integrity of uploaded files
        for key in ['img', 'eo']:
            if key not in request.files:  # Key check
                return 'No %s part' % key
            file = request.files[key]
            if file.filename == '':  # Value check
                return 'No selected file'
            if file and allowed_file(file.filename):  # If the keys and corresponding values are OK
                fname_dict[key] = secure_filename(file.filename)
                if key == 'img':
                    fname_dict['img_orig'] = fname_dict['img']
                file.save(os.path.join(project_path, fname_dict[key]))
                time_recept = time.time()
            else:
                return 'Failed to save the uploaded files'

        # Insert initial data into log DB
        if my_drone.get_drone_name() == 'AIMIFYFlirDuoProR':
            create_time = get_create_time(fname_dict['img_orig'], my_drone.get_drone_name())
        else:
            create_time = get_create_time(os.path.join(project_path, fname_dict['img']), my_drone.get_drone_name())
        query = 'INSERT INTO processing_time '\
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(
            query,
            (
                project_id_str,
                fname_dict['img'],
                create_time,
                os.path.getmtime(os.path.join(project_path, fname_dict['img'])),
                time_recept,
                None, None, None, None, None,
                fname_dict['img_orig']
            )
        )

        # IPOD chain 1: Georeferencing
        if app.config['GEOREFERENCING_METHOD'] == 'DIRECT_GEOREFERENCING':
            parsed_eo = my_drone.preprocess_eo_file(os.path.join(project_path, fname_dict['eo']))
            if not my_drone.pre_calibrated:
                omega, phi, kappa = calibrate(parsed_eo[3], parsed_eo[4], parsed_eo[5], my_drone.ipod_params['R_CB'], my_drone.ipod_params['comb'])
                parsed_eo[3] = omega
                parsed_eo[4] = phi
                parsed_eo[5] = kappa
            # # Activate here to avoid memory fault (especially when using fixed-wing drones)
            # if omega > abs(0.175) or phi > abs(0.175):
            #     print('Too much omega/phi will kill you')
            #     return 'Too much omega/phi will kill you'

        elif app.config['GEOREFERENCING_METHOD'] == 'NEIGHBOR_AT_PHOTOSCAN':
            # Check if there are >= 5 images
            query = 'SELECT count(*) FROM processing_time ' \
                    'WHERE project_id=?;'
            cur.execute(query, (project_id_str,))
            num_of_images = cur.fetchone()[0]
            if num_of_images < 5:
                print('Current georeferencing mode is NEIGHTBOR_AT_PHOTOSCAN, and waiting for more images')
                conn.commit()
                conn.close()
                return 'Current georeferencing mode is NEIGHTBOR_AT_PHOTOSCAN, and waiting for more images'
            else:
                # TODO: Implement 5 images AT algorithm using PhotoScan
                print('Starting AT using PhotoScan...')
                # If there are >= 5 images, process image where ROWID = maxROWID - 2
                query = 'SELECT img_fname FROM processing_time ' \
                        'WHERE project_id=? AND ' \
                        'ABS(processing_time.ROWID - ' \
                        '(SELECT ROWID - 2 from processing_time ' \
                        'WHERE project_id=? AND ' \
                        'img_fname=?)' \
                        ') <= 2;'
                cur.execute(query, (project_id_str, project_id_str, fname_dict['img']))
                result = cur.fetchall()

                # Extract fnames from fetched result
                neighborhood_images_fname_list = []
                for row in result:
                    neighborhood_images_fname = row[0]
                    neighborhood_images_fname_list.append(neighborhood_images_fname)

                # Query 5 neighborhood images from log DB
                query = 'SELECT img_fname FROM processing_time ' \
                        'WHERE project_id=? AND ' \
                        'ABS(processing_time.ROWID - ' \
                        '(SELECT ROWID - 2 from processing_time ' \
                        'WHERE project_id=? AND ' \
                        'img_fname=?)' \
                        ') <= 2;'
                cur.execute(query, (project_id_str, project_id_str, fname_dict['img']))
                result = cur.fetchall()

                print(result)

                # Extract fnames from fetched result
                fname_neighborhood_list = []
                for row in result:
                    fname = row[0]
                    fpath = os.path.join(project_path, fname)
                    fname_neighborhood_list.append(fpath)

                # Substitute fname_dict with ROWID - 2
                fname_dict['img'] = fname_neighborhood_list[2]
                fname_dict['img_orig'] = fname_neighborhood_list[2]
                fname_dict['eo'] = fname_neighborhood_list[2].split('.')[0] + '_neighborhood_AT.txt'

                # Run neighborhood AT program
                neighbor_AT(fname_neighborhood_list, os.path.join(project_path, fname_dict['eo']))
                parsed_eo = my_drone.preprocess_eo_file(os.path.join(project_path, fname_dict['eo']))
        time_syscal = time.time()

        # IPOD chain 2: Individual ortho-image generation
        fname_dict['img_rectified'] = fname_dict['img'].split('.')[0] + '_rectified.tif'
        bbox_wkt = rectify(
            project_path=project_path,
            img_fname=fname_dict['img'],
            img_rectified_fname=fname_dict['img_rectified'],
            eo=parsed_eo,
            ground_height=my_drone.ipod_params['ground_height'],
            sensor_width=my_drone.ipod_params['sensor_width'],
            focal_length=my_drone.ipod_params['focal_length'],
            gsd=my_drone.ipod_params['gsd']
        )
        time_ortho = time.time()

        # IPOD chain 3: Object detection
        detected_objects = detect_ship(
            'server/json_template/ldm_mago3d_detected_objects.json',
            os.path.join(project_path, fname_dict['img_rectified'])
        )
        time_od = time.time()

        # Mago3D에 전송
        if project_id_str[0:5] != 'LOCAL':
            # Generate metadata for Mago3D
            img_metadata = create_img_metadata(
                drone_project_id=int(project_id_str),
                data_type='0',
                file_name=fname_dict['img_rectified'],
                detected_objects=detected_objects,
                drone_id='0',
                drone_name=my_drone.get_drone_name(),
                parsed_eo=parsed_eo
            )
            print(img_metadata)
            fname_dict['img_metadata'] = fname_dict['img'].split('.')[0] + '_metadata.json'
            with open(os.path.join(project_path, fname_dict['img_metadata']), 'w') as f:
                f.write(json.dumps(img_metadata))
            res = mago3d.upload(
                img_rectified_path=os.path.join(project_path, fname_dict['img_rectified']),
                img_metadata=img_metadata
            )
            print(res.text)
            time_mago = time.time()
        else:
            time_mago = None

        # 로그 DB 갱신: 결과 입력
        if not detected_objects:
            detected_objects = [{
                'geometry': None,
                'bounding_box_geometry': None
            }]
        query = 'UPDATE processing_time ' \
                'SET time_syscal = ?, ' \
                'time_ortho = ?, ' \
                'time_od = ?, ' \
                'time_mago = ?, ' \
                'ship_detection = ? ' \
                'WHERE project_id = ?'
        cur.execute(
            query,
            (
                time_syscal,
                time_ortho,
                time_od,
                time_mago,
                json.dumps(detected_objects),
                project_id_str
            )
        )

        conn.commit()
        conn.close()

        return 'Image upload and IPOD chain complete'


@app.route('/check/drone_polling')
def check_drone_polling():
    """
    Maintains polling connection with drone system. Whenever Mago3D asks to check the drone system (START_HEALTH_CHECK),
    this polling connection will be disconnected and be connected again immediately.
    :return:
    """
    app.config['DRONE']['asked_health_check'] = False
    app.config['DRONE']['asked_sim'] = False
    while True:
        time.sleep(app.config['DRONE']['polling_time'])
        if app.config['DRONE']['asked_health_check']:
            return 'START_HEALTH_CHECK'
        elif app.config['DRONE']['asked_sim']:
            return app.config['SIMULATION_ID']


@app.route('/check/drone_checklist_result')
def check_drone_result():
    app.config['DRONE']['checklist_result'] = 'OK'
    return 'OK'


@app.route('/check/drone')
def check_drone():
    app.config['DRONE']['asked_health_check'] = True
    time.sleep(app.config['DRONE']['timeout'])
    if app.config['DRONE']['checklist_result'] == 'OK':
        app.config['DRONE']['checklist_result'] = 'None'
        return 'OK'
    else:
        return 'DISCONNECTED_OR_NOT_RESPONDING'


@app.route('/check/beacon')
def check_beacon():
    # UN Test
    return 'OK'


@app.route('/check/sim/from_ldm')
def check_sim_from_ldm():
    app.config['SIMULATION_ID'] = request.args.get('simulation_id')
    executor.submit(start_image_check, app.config['SIMULATION_ID'])
    return 'OK'


@app.route('/check/sim/from_drone')
def check_sim_from_drone():
    app.config['SIMULATION_ID'] = request.args.get('simulation_id')
    app.config['DRONE']['asked_sim'] = True
    return 'OK'


@app.route('/check/drone_name')
def check_drone_name():
    return my_drone.get_drone_name()


# 오픈드론맵: 후처리
@app.route('/webodm_upload/start_processing/<project_id>')
def webodm_start_processing(project_id_str):
    webodm = WebODM(
        url=app.config['WEBODM_CONFIG']['url'],
        username=app.config['WEBODM_CONFIG']['username'],
        password=app.config['WEBODM_CONFIG']['password']
    )
    webodm.create_project(project_name=project_id_str)
    project_folder = 'project/' + project_id_str
    webodm.create_task(project_folder)

    return 'ODM'


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=5000)
