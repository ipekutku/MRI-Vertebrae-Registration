import os
import SimpleITK as sitk
from utils.helpers import get_fnumber


class MRIProcessor:
    def __init__(self, preprocessed_dir, data_dir='/local_ssd/practical_wise24/vertebra_labeling/data'):
        self.data_dir = data_dir
        self.preprocessed_dir = preprocessed_dir

    def preprocess_data(self):
        for subject_dir in os.listdir(os.path.join(self.data_dir, 'spider_raw')):
            subject_path = os.path.join(self.data_dir, 'spider_raw', subject_dir, 'T1w')

            if os.path.exists(subject_path):
                nii_files = [file for file in os.listdir(subject_path) if file.endswith('.nii.gz')]

                if len(nii_files) > 0:
                    img = self.correct_bias(os.path.join(subject_path, nii_files[0]))
                    normalized = self.normalize(img)
                    sitk.WriteImage(normalized, f'{self.preprocessed_dir}/file{get_fnumber(os.path.join(subject_path, nii_files[0]))}.nii.gz')

    @staticmethod
    def correct_bias(raw_img_path, shrinkFactor = 1):
        print('Reading Image...')
        raw_img_sitk = sitk.ReadImage(raw_img_path, sitk.sitkFloat32)
        raw_img_sitk = sitk.DICOMOrient(raw_img_sitk, 'LPS')
        print('Rescaling Image...')
        transformed = sitk.RescaleIntensity(raw_img_sitk, 0, 255)

        transformed = sitk.LiThreshold(transformed, 0, 1)

        head_mask = transformed
        inputImage = raw_img_sitk

        inputImage = sitk.Shrink(raw_img_sitk, [shrinkFactor] * inputImage.GetDimension())
        maskImage = sitk.Shrink(head_mask, [shrinkFactor] * inputImage.GetDimension())

        bias_corrector = sitk.N4BiasFieldCorrectionImageFilter()

        print('Correcting Bias...')
        corrected = bias_corrector.Execute(inputImage, maskImage)
        log_bias_field = bias_corrector.GetLogBiasFieldAsImage(raw_img_sitk)
        corrected_image_full_resolution = raw_img_sitk / sitk.Exp(log_bias_field)

        return corrected_image_full_resolution

    @staticmethod
    def normalize(img, template_img_path = '/local_ssd/practical_wise24/vertebra_labeling/data/spider_raw/sub-0083/T1w/sub-0083_T1w.nii.gz'):

        template_img_sitk = sitk.ReadImage(template_img_path, sitk.sitkFloat64)
        template_img_sitk = sitk.DICOMOrient(template_img_sitk, 'LPS')

        transformed = sitk.HistogramMatching(img, template_img_sitk)
        return transformed

