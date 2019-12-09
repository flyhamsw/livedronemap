import os
import json


def run_neighbor_AT(fname_list, eo_path):
    # Make bash command to run PhotoScan
    bash_str = 'bash /home/innopam-ldm/PhotoScan/photoscan-pro/photoscan.sh -r server/image_processing/photoscan_neighbor_AT/neighbor_AT.py --images '
    for fname in fname_list:
        bash_str += fname + ','
    bash_str = bash_str[0:-1]
    bash_str += ' --eo_path %s' % eo_path

    # Run PhotoScan in bash
    print('Executing python scripts in PhotoScan...')
    print(bash_str)
    os.system(bash_str)


if __name__ == '__main__':
    run_neighbor_AT(['IMG_9354.jpg', 'IMG_9355.jpg', 'IMG_9356.jpg', 'IMG_9357.jpg', 'IMG_9358.jpg'], 'test.txt')
