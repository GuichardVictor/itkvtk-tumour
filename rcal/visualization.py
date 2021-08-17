import sys
import os

import vtk
from PyQt5 import QtCore, QtGui
from PyQt5 import Qt

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

def GetSlicingCallBack(interactor, interactorStyle, reslice, window):
    # Create callbacks for slicing the image
    actions = {}
    actions["Slicing"] = 0

    def ButtonCallback(obj, event):
        if event == "LeftButtonPressEvent":
            actions["Slicing"] = 1
        else:
            actions["Slicing"] = 0

    def MouseMoveCallback(obj, event):
        (lastX, lastY) = interactor.GetLastEventPosition()
        (mouseX, mouseY) = interactor.GetEventPosition()
        if actions["Slicing"] == 1:
            deltaY = mouseY - lastY
            reslice.Update()
            sliceSpacing = reslice.GetOutput().GetSpacing()[2]
            matrix = reslice.GetResliceAxes()
            # move the center point that we are slicing through
            center = matrix.MultiplyPoint((0, 0, sliceSpacing*deltaY, 1))
            matrix.SetElement(0, 3, center[0])
            matrix.SetElement(1, 3, center[1])
            matrix.SetElement(2, 3, center[2])
            window.Render()
        else:
            interactorStyle.OnMouseMove()

    return ButtonCallback, MouseMoveCallback

class QtVTKMainWindow(Qt.QMainWindow):
    """ QtVTKMainWindow class

    Qt window that displays a volume on the left, and the different
    slices on the right.

    A mask can be given or not and will be displayed in red.

    Args:
        input_filename: volume file path as a metaimage
        mask_filename: mask volume file path as a metaimage
        parent: Qt parent for QMainWindow class (opt)
    """
 
    def __init__(self, input_filename, mask_filename=None, parent=None):
        Qt.QMainWindow.__init__(self, parent)

        self.input_filename = input_filename
        self.mask_filename = mask_filename
 
        self.frame = Qt.QFrame()
 
        self.vl = Qt.QHBoxLayout()

        hl_inner = Qt.QHBoxLayout()

        vl_left = Qt.QVBoxLayout()
        vl_right = Qt.QVBoxLayout()

        with_mask = mask_filename is not None
        reader = self.get_reader(with_mask=with_mask)

        self.volumeVTKWidget, self.interactorVolume = self.build_view_volume(reader)

        self.vtkWidgetAxes = []
        self.interactorsAxes = []
        self.interactorsStyles = []
        self.labelsAxes = []

        for axis in ['sagital', 'coronal', 'axial', 'oblique']:
            vtkWidget, interactor = self.build_view_axis(axis, reader)
            self.vtkWidgetAxes.append(vtkWidget)
            self.interactorsAxes.append(interactor)

            label = Qt.QLabel(self.frame)
            label.setText(axis)
            label.setAlignment(Qt.Qt.AlignCenter)
            label.setFont(Qt.QFont('Arial', 14))
            self.labelsAxes.append(label)
        
        vl_left.addWidget(self.labelsAxes[0])
        vl_left.addWidget(self.vtkWidgetAxes[0])
        vl_left.addWidget(self.labelsAxes[1])
        vl_left.addWidget(self.vtkWidgetAxes[1])
        
        vl_right.addWidget(self.labelsAxes[2])
        vl_right.addWidget(self.vtkWidgetAxes[2])
        vl_right.addWidget(self.labelsAxes[3])
        vl_right.addWidget(self.vtkWidgetAxes[3])
         
        hl_inner.addLayout(vl_left)
        hl_inner.addLayout(vl_right)

        self.vl.addWidget(self.volumeVTKWidget)
        self.vl.addLayout(hl_inner)
 
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)
        
        self.show()

        for interactor in self.interactorsAxes:
            interactor.Initialize()

        self.interactorVolume.Initialize()
    
    def closeEvent(self, *args, **kwargs):
        """ Destructor of the main window. """
        for vtkWdiget in self.vtkWidgetAxes:
            vtkWdiget.close()
        
        self.volumeVTKWidget.close()

    def get_reader(self, with_mask=True):
        """ Creates the reader and do some small pre processing

        Args:
            with_mask: if with_mask, the mask and the volume will be merged using vtkImageMask
        """
        readerBrain = vtk.vtkMetaImageReader()
        readerBrain.SetFileName(self.input_filename)
        readerBrain.Update()

        rescale_readerBrain = vtk.vtkImageShiftScale()
        rescale_readerBrain.SetOutputScalarTypeToFloat()
        rescale_readerBrain.SetScale(255 / readerBrain.GetOutput().GetScalarRange()[1])
        rescale_readerBrain.SetInputConnection(readerBrain.GetOutputPort())
        rescale_readerBrain.Update()

        if not with_mask:
            return rescale_readerBrain

        readerMask = vtk.vtkMetaImageReader()
        readerMask.SetFileName(self.mask_filename)
        readerMask.Update()

        unsigned_readerMask = vtk.vtkImageShiftScale()
        unsigned_readerMask.SetOutputScalarTypeToUnsignedChar()
        unsigned_readerMask.SetInputConnection(readerMask.GetOutputPort())
        unsigned_readerMask.Update()

        maskedImage = vtk.vtkImageMask()
        maskedImage.SetImageInputData(rescale_readerBrain.GetOutput())
        maskedImage.SetMaskInputData(unsigned_readerMask.GetOutput())
        maskedImage.NotMaskOn()
        maskedImage.SetMaskedOutputValue(300)
        maskedImage.Update()

        return maskedImage

    @staticmethod
    def GetMatrixView(axis, center):
        """ creates the matrix view

        Args:
            axis: type of the view
            center: center coordinates of the volume 
        """
        axes = ['axial', 'coronal', 'sagital', 'oblique']

        idx = axes.index(axis)

        axial = vtk.vtkMatrix4x4()
        axial.DeepCopy((1, 0, 0, center[0],
                        0, -1, 0, center[1],
                        0, 0, 1, center[2],
                        0, 0, 0, 1))

        coronal = vtk.vtkMatrix4x4()
        coronal.DeepCopy((1, 0, 0, center[0],
                        0, 0, 1, center[1],
                        0,1, 0, center[2],
                        0, 0, 0, 1))

        sagittal = vtk.vtkMatrix4x4()
        sagittal.DeepCopy((0, 0,-1, center[0],
                        1, 0, 0, center[1],
                        0,1, 0, center[2],
                        0, 0, 0, 1))

        oblique = vtk.vtkMatrix4x4()
        oblique.DeepCopy((1, 0, 0, center[0],
                        0, 0.866025, -0.5, center[1],
                        0, 0.5, 0.866025, center[2],
                        0, 0, 0, 1))

        orientations = [axial, coronal, sagittal, oblique]

        return orientations[idx]

    def build_view_volume(self, reader):
        """ Create the left view (volume view)

        Args:
            reader: VTK reader given by the get_reader function
        """
        polyMapper = vtk.vtkSmartVolumeMapper()
        polyMapper.SetInputConnection(reader.GetOutputPort())

        opacity_transfer_function = vtk.vtkPiecewiseFunction()
        opacity_transfer_function.AddPoint(0, 0.00)
        opacity_transfer_function.AddPoint(0.1, 0.01)
        opacity_transfer_function.AddPoint(255, 0.01)
        opacity_transfer_function.AddPoint(300, 0.09)

        color_transfer_function = vtk.vtkColorTransferFunction()
        color_transfer_function.AddRGBPoint(0.0, 0, 0, 0)
        color_transfer_function.AddRGBPoint(64, 0.75, 0.75, 0.75)
        color_transfer_function.AddRGBPoint(128, 0.8, 0.8, 0.8)
        color_transfer_function.AddRGBPoint(255, 1.0, 1.0, 1.0)
        color_transfer_function.AddRGBPoint(300, 1.0, 0.2, 0.2)

        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(color_transfer_function)
        volume_property.SetScalarOpacity(opacity_transfer_function)

        actor = vtk.vtkVolume()
        actor.SetMapper(polyMapper)
        actor.SetProperty(volume_property)

        actorScale = vtk.vtkLegendScaleActor()
        actorScale.TopAxisVisibilityOff()
        actorScale.LeftAxisVisibilityOff()
        actorScale.SetLabelModeToDistance()

        renderer = vtk.vtkRenderer()
        renderer.ResetCamera()
        renderer.AddActor(actor)
        renderer.AddActor(actorScale)

        vtkWidget = QVTKRenderWindowInteractor(self.frame)
        vtkWidget.GetRenderWindow().AddRenderer(renderer)

        vtkWidget.GetRenderWindow().GetInteractor().SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

        return vtkWidget, vtkWidget.GetRenderWindow().GetInteractor()

    def build_view_axis(self, axis, reader):
        """ Create a view based on an axis

        Args:
            axis: axis name
            reader: vtk reader given by the get_reader function
        """
        vtkWidget = QVTKRenderWindowInteractor(self.frame)

        (xMin, xMax, yMin, yMax, zMin, zMax) = reader.GetExecutive().GetWholeExtent(reader.GetOutputInformation(0))
        (xSpacing, ySpacing, zSpacing) = reader.GetOutput().GetSpacing()
        (x0, y0, z0) = reader.GetOutput().GetOrigin()

        center = [x0 + xSpacing * 0.5 * (xMin + xMax),
                y0 + ySpacing * 0.5 * (yMin + yMax),
                z0 + zSpacing * 0.5 * (zMin + zMax)]

        axis_matrix = QtVTKMainWindow.GetMatrixView(axis, center)

        # Extract a slice in the desired orientation
        reslice = vtk.vtkImageReslice()
        reslice.SetInputConnection(reader.GetOutputPort())
        reslice.SetOutputDimensionality(2)
        reslice.SetResliceAxes(axis_matrix)
        reslice.SetInterpolationModeToLinear()

        reslice = reslice

        # Create a greyscale lookup table
        table = vtk.vtkLookupTable()
        table.SetRange(0, 255) # image intensity range
        table.SetValueRange(0.0, 1.0) # from black to white
        table.SetSaturationRange(0.0, 0.0) # no color saturation
        table.SetRampToLinear()
        table.SetUseAboveRangeColor(True)
        table.SetAboveRangeColor(1.0, 0.2, 0.2, 1.0)
        table.Build()

        # Map the image through the lookup table
        color = vtk.vtkImageMapToColors()
        color.SetLookupTable(table)
        color.SetInputConnection(reslice.GetOutputPort())

        # Display the image
        actor = vtk.vtkImageActor()
        actor.GetMapper().SetInputConnection(color.GetOutputPort())

        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)

        interactorStyle = vtk.vtkInteractorStyleImage()
        self.interactorsStyles.append(interactorStyle)
        interactor = vtkWidget.GetRenderWindow().GetInteractor()
        interactor.SetInteractorStyle(interactorStyle)

        vtkWidget.GetRenderWindow().AddRenderer(renderer)

        ButtonCallback, MouseMoveCallback = GetSlicingCallBack(interactor, interactorStyle, reslice, vtkWidget.GetRenderWindow())

        interactorStyle.AddObserver("MouseMoveEvent", MouseMoveCallback)
        interactorStyle.AddObserver("LeftButtonPressEvent", ButtonCallback)
        interactorStyle.AddObserver("LeftButtonReleaseEvent", ButtonCallback)

        return vtkWidget, interactor

def run_visualization(datafile, maskfile=None):
    """ Create the QT application and the main window

    Args:
        datafile: path to the volume to render
        maskfile: path to the tumour mask
    """
    app = Qt.QApplication(sys.argv)
    
    window = QtVTKMainWindow(datafile, maskfile)
    window.setWindowTitle('ITK/VTK - Victor GUICHARD')
    
    sys.exit(app.exec_())
