from ScopeFoundry import HardwareComponent
import CameraDevice
from CameraDevice import HamamatsuDeviceMR, dcam, DCAMERR_NOERROR, DCAMException


class HamamatsuHardware(HardwareComponent):
    
    name = "HamamatsuHardware"
    
    def setup(self):
        
        self.camera = self.add_logged_quantity('camera', dtype=str, si=False, 
                                               ro=1, initial = 'No camera found' )
        
        self.temperature = self.add_logged_quantity('temperature', dtype=float, si=False, ro=1, 
                                                    unit = 'Celsius')
        
        self.exposure_time = self.add_logged_quantity('exposure_time', dtype = float, si = False, ro = 0, 
                                                       spinbox_decimals = 6, unit = 'sec', initial = 0.01, reread_from_hardware_after_write = True, vmin = 0)
        
        self.acquisition_mode = self.add_logged_quantity('acquisition_mode', dtype = str, ro = 0, 
                                                         choices = ["fixed_length", "run_till_abort"], initial = "fixed_length")
        
        self.number_frames = self.add_logged_quantity("number_frames", dtype = int, si = False, ro = 0, 
                                                      initial = 1, vmin = 0)
        
        #For subarray we have imposed float, since otherwise I cannot modify the step (I should modify the logged quantities script, but I prefer left it untouched)
        self.subarrayh = self.add_logged_quantity("subarray_hsize", dtype=float, si = False, ro= 0,
                                                   spinbox_step = 4, spinbox_decimals = 0, initial = 2048, vmin = 4, vmax = 2048)#, reread_from_hardware_after_write = True)
        
        self.subarrayv = self.add_logged_quantity("subarray_vsize", dtype=float, si = False, ro= 0, 
                                                  spinbox_step = 4, spinbox_decimals = 0, initial = 2048, vmin = 4, vmax = 2048)#, reread_from_hardware_after_write = True)
        
        self.submode = self.add_logged_quantity("subarray_mode", dtype=str, si = False, ro = 1, 
                                                initial = 'ON')
        
        self.trsource = self.add_logged_quantity('trigger_source', dtype=str, si=False, ro=0, 
                                                 choices = ["internal", "external"], initial = 'internal', reread_from_hardware_after_write = True)
        
        self.trmode = self.add_logged_quantity('trigger_mode', dtype=str, si=False, ro=0, 
                                               choices = ["normal", "start"], initial = 'normal', reread_from_hardware_after_write = True)
        
        self.trpolarity = self.add_logged_quantity('trigger_polarity', dtype=str, si=False, ro=0, 
                                                   choices = ["positive", "negative"], initial = 'positive', reread_from_hardware_after_write = True)
        
    
    def connect(self):
        """
        The initial connection does not update the value in the device,
        since there is no set_from_hardware function, so the device has
        as initial values the values that we initialize in the HamamatsuDevice
        class. I'm struggling on how I can change this. There must be some function in
        ScopeFoundry
        """
        
        #self.trsource.change_readonly(True)
        #self.trmode.change_readonly(True)
        #self.trpolarity.change_readonly(True)
        #self.acquisition_mode.change_readonly(True) #if we change from run_till_abort to fixed_length while running it crashes
        self.hamamatsu = HamamatsuDeviceMR(camera_id=0, frame_x=self.subarrayh.val, frame_y=self.subarrayv.val, acquisition_mode=self.acquisition_mode.val, 
                                           number_frames=self.number_frames.val, exposure=self.exposure_time.val, 
                                           trsource=self.trsource.val, trmode=self.trmode.val, trpolarity=self.trpolarity.val ) #maybe with more cameras we have to change  
        
        self.camera.hardware_read_func = self.hamamatsu.getModelInfo
        self.temperature.hardware_read_func = self.hamamatsu.getTemperature
        self.submode.hardware_read_func = self.hamamatsu.setSubArrayMode
        self.exposure_time.hardware_read_func = self.hamamatsu.getExposure
        self.trsource.hardware_read_func = self.hamamatsu.getTriggerSource
        self.trmode.hardware_read_func = self.hamamatsu.getTriggerMode
        self.trpolarity.hardware_read_func = self.hamamatsu.getTriggerPolarity
        
        #self.subarrayh.hardware_read_func = self.hamamatsu.getSubarrayH
        #self.subarrayv.hardware_read_func = self.hamamatsu.getSubarrayV
        
        self.subarrayh.hardware_set_func = self.hamamatsu.setSubarrayH
        self.subarrayv.hardware_set_func = self.hamamatsu.setSubarrayV
        self.exposure_time.hardware_set_func = self.hamamatsu.setExposure
        self.acquisition_mode.hardware_set_func = self.hamamatsu.setAcquisition
        self.number_frames.hardware_set_func = self.hamamatsu.setNumberImages
        self.trsource.hardware_set_func = self.hamamatsu.setTriggerSource
        self.trmode.hardware_set_func = self.hamamatsu.setTriggerMode
        self.trpolarity.hardware_set_func = self.hamamatsu.setTriggerPolarity
        
        
        self.read_from_hardware() #read from harrdware at connection
#         self.subarrayh.update_value(2048)
#         self.subarrayv.update_value(2048)
#         self.exposure_time.update_value(0.01)
#         self.acquisition_mode.update_value("fixed_length")
#         self.number_frames.update_value(2)

        
        
    def disconnect(self):
        
        #self.trsource.change_readonly(False)
        #self.trmode.change_readonly(False)
        #self.trpolarity.change_readonly(False)
        
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