from innophotoscan import Innophotoscan
import argparse
import json


def solve_AT(fname_list, eo_path):
    ip = Innophotoscan()

    fname, EO = ip.photoscan_alignphotos(fname_list)

    print(fname)
    print(EO)

    with open(eo_path, 'w') as f:
        f.write('PhotoScanEO\t%f\t%f\t%f\t%f\t%f\t%f' % (EO[0], EO[1], EO[2], EO[3], EO[4], EO[5]))


if __name__ == '__main__':
    # Set argument parser
    parser = argparse.ArgumentParser(description='InnoPhotoScan')
    parser.add_argument('--images', required=True)
    parser.add_argument('--eo_path', required=True)
    args = parser.parse_args()
    fname_list = args.images.split(',')
    solve_AT(fname_list, args.eo_path)
