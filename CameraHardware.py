from ScopeFoundry import HardwareComponent
import CameraDevice
from CameraDevice import HamamatsuDevice
from numpy import dtype

class HamamatsuHardware(HardwareComponent):
    
    name = "HamamatsuHardware"
    
    def setup(self):
        
        self.camera = self.add_logged_quantity('camera', dtype=str, si=False, ro=1, initial = 'No camera found' )
        self.temperature = self.add_logged_quantity('temperature', dtype=float, si=False, ro=1, unit = 'C')
        self.exposure_time = self.add_logged_quantity('exposure_time', dtype = float, si = False, ro = 0, unit = 'sec', initial = 0.01)
        self.acquisition_mode = self.add_logged_quantity('acquisition_mode', dtype = str, si = False, choices = ["fixed_length", "run_till_abort"])
        self.number_frames = self.add_logged_quantity("number_frames", dtype = int, si = False, ro = 0, initial = 0)
        self.subarrayh = self.add_logged_quantity("subarray_hsize", dtype=int, si = False, ro= 0, initial = 2048)
        self.subarrayv = self.add_logged_quantity("subarray_vsize", dtype=int, si = False, ro= 0, initial = 2048)
        self.submode = self.add_logged_quantity("subarray_mode", dtype = str, si = False, ro = 1, initial = 'ON')
        
    def connect(self):
        
        self.hamamatsu = HamamatsuDevice(camera_id=0) #maybe with more cameras we have to change
        
        self.camera.hardware_read_func = self.hamamatsu.getModelInfo
        self.temperature.hardware_read_func = self.hamamatsu.getTemperature
        self.submode.hardware_read_func = self.hamamatsu.setSubArrayMode
        
        self.subarrayh.hardware_set_func = self.hamamatsu.setSubarrayh
        self.subarrayv.hardware_set_func = self.hamamatsu.setSubarrayv
        self.exposure_time.hardware_set_func = self.hamamatsu.setExposure
        self.acquisition_mode.hardware_set_func = self.hamamatsu.setAcquisition
        self.number_frames.hardware_set_func = self.hamamatsu.setNumberImages
        
        self.read_from_hardware()
        
        
    def disconnect(self):
         
        if hasattr(self, 'hamamatsu'):
            self.hamamatsu.shutdown()         
            del self.hamamatsu
        
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None