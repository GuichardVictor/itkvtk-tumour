import os

import rcal.segmentation
import rcal.visualization

def main():
    # Perform Segmentation before visualization
    #rcal.segmentation.segment_tumour(datafile, maskfile)
    datafile = 'data/BRATS_HG0015_T1C.mha'
    maskfile = 'data/segmentation_mask.mha'

    # if segmentation is already done skip
    if maskfile.split('/')[1] not in os.listdir('data/'):
        rcal.segmentation.segment_tumour(datafile, maskfile)

    # Start Qt App and visualization
    rcal.visualization.run_visualization(datafile, maskfile)


if __name__ == "__main__":
    main()