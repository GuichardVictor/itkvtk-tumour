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
    
    normalizeFilter = itk.RescaleIntensityImageFilter(Input=medianFilter.GetOutput(), OutputMinimum=0, OutputMaximum=255)

    thresholdFilter = itk.BinaryThresholdImageFilter.New(Input=normalizeFilter)

    thresholdFilter.SetUpperThreshold(int(255 * 0.75))
    thresholdFilter.SetOutsideValue(255)
    thresholdFilter.SetInsideValue(0)

    writer = itk.ImageFileWriter.New(Input=thresholdFilter.GetOutput(), FileName=output_filename)
    writer.Update()
