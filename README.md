# VTK - ITK Project

This project was made to try the itk vtk libraries. The program will perform both segmentation and rendering of a brain tumour.

![example](https://github.com/GuichardVictor/itkvtk-tumour/blob/master/data/example.gif)


## Authors

* Victor Guichard

---

## Run

Make sure you have all requirements before running the application:

```sh
$ pip install -r requirements.txt 
```

Update files path in `main.py` (mask path, and data path)

Run
```sh
$ python main.py 
```

## Segmentation

The segmentation approach is quite simple:

First we use a median filter then we treshold the tumor for values that are greater than 34% of the maximum.

As the wrapper did not work (tested with python3.7 and python3.8) the mask is written on the disk and then load back by vtk.

## Visualization

We are using QT in order to make a more insightful visualization:

- Apply the mask after the reader (and do a little bit of pre processing).
- On the left side of the QT window we are using a `vtkSmartVolumeMapper`.
- On the right there is four different type of slices.
- The tumour will appear red while the brain will be gray.
