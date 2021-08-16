import os

import rcal.segmentation
import rcal.visualization

import argparse

def get_parser():
    parser = argparse.ArgumentParser(description="Tumour segmentation and visualization")
    parser.add_argument('--resegment', action='store_true', default=False)

    return parser

def main(args):
    # Perform Segmentation before visualization
    #rcal.segmentation.segment_tumour(datafile, maskfile)
    datafile = 'data/BRATS_HG0015_T1C.mha'
    maskfile = 'data/segmentation_mask.mha'

    # if segmentation is already done skip
    if args.resegment:
        rcal.segmentation.segment_tumour(datafile, maskfile)
    if maskfile.split('/')[1] not in os.listdir('data/'):
        rcal.segmentation.segment_tumour(datafile, maskfile)

    # Start Qt App and visualization
    rcal.visualization.run_visualization(datafile, maskfile)


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    main(args)
