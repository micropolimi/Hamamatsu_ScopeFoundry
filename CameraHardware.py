from ScopeFoundry import HardwareComponent
import CameraDevice
from CameraDevice import HamamatsuDeviceMR, dcam, DCAMERR_NOERROR, DCAMException
from numpy import dtype

class HamamatsuHardware(HardwareComponent):
    
    name = "HamamatsuHardware"
    
    def setup(self):
        
        self.camera = self.add_logged_quantity('camera', dtype=str, si=False, ro=1, initial = 'No camera found' )
        self.temperature = self.add_logged_quantity('temperature', dtype=float, si=False, ro=1, unit = 'Celsius')
        self.exposure_time = self.add_logged_quantity('exposure_time', dtype = float, si = False, ro = 0, unit = 'sec', initial = 0.01)
        self.acquisition_mode = self.add_logged_quantity('acquisition_mode', dtype = str, choices = ["fixed_length", "run_till_abort"], initial = "fixed_length")
        self.number_frames = self.add_logged_quantity("number_frames", dtype = int, si = False, ro = 0, initial = 1)
        self.subarrayh = self.add_logged_quantity("subarray_hsize", dtype=int, si = False, ro= 0, initial = 2048)
        self.subarrayv = self.add_logged_quantity("subarray_vsize", dtype=int, si = False, ro= 0, initial = 2048)
        self.submode = self.add_logged_quantity("subarray_mode", dtype = str, si = False, ro = 1, initial = 'ON')
        
    def connect(self):
        """
        The initial connection does not update the value in the device,
        since there is no set_from_hardware function, so the device has
        as initial values the values that we initialize in the HamamatsuDevice
        class. I'm struggling on how I can change this. There must be some function in
        ScopeFoundry
        """
        
        self.hamamatsu = HamamatsuDeviceMR(camera_id=0, frame_x=self.subarrayh.val, frame_y=self.subarrayv.val, acquisition_mode=self.acquisition_mode.val, number_frames=self.number_frames.val, exposure=self.exposure_time.val ) #maybe with more cameras we have to change  
        
        self.camera.hardware_read_func = self.hamamatsu.getModelInfo
        self.temperature.hardware_read_func = self.hamamatsu.getTemperature
        self.submode.hardware_read_func = self.hamamatsu.setSubArrayMode
        
        self.subarrayh.hardware_set_func = self.hamamatsu.setSubarrayH
        self.subarrayv.hardware_set_func = self.hamamatsu.setSubarrayV
        self.exposure_time.hardware_set_func = self.hamamatsu.setExposure
        self.acquisition_mode.hardware_set_func = self.hamamatsu.setAcquisition
        self.number_frames.hardware_set_func = self.hamamatsu.setNumberImages
        
#         self.subarrayh.update_value(2048)
#         self.subarrayv.update_value(2048)
#         self.exposure_time.update_value(0.01)
#         self.acquisition_mode.update_value("fixed_length")
#         self.number_frames.update_value(2)

        self.read_from_hardware()     
        
    def disconnect(self):
        
        if hasattr(self, 'hamamatsu'):
            self.hamamatsu.stopAcquisition()
            self.hamamatsu.shutdown() 
#             error_uninit = self.hamamatsu.dcam.dcamapi_uninit()
#             if (error_uninit != DCAMERR_NOERROR):
#                 raise DCAMException("DCAM uninitialization failed with error code " + str(error_uninit))    
            del self.hamamatsu
            
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None