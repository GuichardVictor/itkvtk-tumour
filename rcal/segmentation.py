import itk

def segment_tumour(input_filename, output_filename):
    """
    Perform the tumour segmentation on the given input file
    and save the mask on the given output file.

    Args:
        input_filename: input file path to read
        output_filename: output file path to write segmentation mask
    """
    reader = itk.ImageFileReader.New(FileName=input_filename)

    medianFilter = itk.MedianImageFilter.New(Input=reader.GetOutput(), Radius=[9, 9, 0])

    thresholdFilter = itk.BinaryThresholdImageFilter.New(Input=medianFilter.GetOutput())

    thresholdFilter.SetUpperThreshold(int(2592 * 0.34))
    thresholdFilter.SetOutsideValue(255)
    thresholdFilter.SetInsideValue(0)

    writer = itk.ImageFileWriter.New(Input=thresholdFilter.GetOutput(), FileName=output_filename)
    writer.Update()
