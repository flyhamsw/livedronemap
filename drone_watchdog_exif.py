import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config.config_watchdog import BaseConfig as Config
from clients.ldm_client import Livedronemap
from server.image_processing.exif_parser import extract_eo

image_list = []
eo_list = []

ldm = Livedronemap(Config.LDM_ADDRESS)
project_id = ldm.create_project(Config.LDM_PROJECT_NAME, visualization_module=Config.VISUALIZATION_MODE)
ldm.set_current_project(project_id)

print('Current project ID: %s' % project_id)


def upload_data(image_fname, eo_fname):
    result = ldm.ldm_upload(image_fname, eo_fname)
    print('response from LDM server:')
    print(result)


class Watcher:
    def __init__(self, directory_to_watch):
        self.observer = Observer()
        self.directory_to_watch = directory_to_watch

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type == 'created':
            file_name = event.src_path.split('\\')[-1][:-(len(Config.IMAGE_FILE_EXT) + 1)]
            extension_name = event.src_path.split('\\')[-1].split('.')[-1]
            print('A new file detected: %s' % file_name)
            if Config.IMAGE_FILE_EXT in extension_name:
                image_list.append(file_name)
                time.sleep(10)
                eo_dict = extract_eo(file_name + '.' + Config.IMAGE_FILE_EXT, Config.CAMERA_MANUFACTURER)
                with open(file_name + '.' + Config.EO_FILE_EXT, 'w') as f:
                    eo_file_data = file_name.split('/')[-1] + '.' + Config.IMAGE_FILE_EXT + '\t' + \
                                   str(eo_dict['longitude']) + '\t' + \
                                   str(eo_dict['latitude']) + '\t' + \
                                   str(eo_dict['altitude']) + '\t' + \
                                   str(eo_dict['yaw']) + '\t' + \
                                   str(eo_dict['pitch']) + '\t' + \
                                   str(eo_dict['roll']) + '\t'
                    print('EO data:')
                    print(eo_file_data)
                    f.write(eo_file_data)
                eo_list.append(file_name + Config.EO_FILE_EXT)
                print('uploading data...')
                upload_data(
                    file_name + '.' + Config.IMAGE_FILE_EXT,
                    file_name + '.' + Config.EO_FILE_EXT
                )
            else:
                print('But it is not an image file.')
            print('===========================================================')


if __name__ == '__main__':
    w = Watcher(directory_to_watch=Config.DIRECTORY_TO_WATCH)
    w.run()
