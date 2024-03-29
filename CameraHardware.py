""" Written by Michele Castriotta, Alessandro Zecchi, Andrea Bassi (Polimi).
   Code for creating the hardware class of ScopeFoundry for the Orca Flash 4V3.
   
   11/18
"""

from ScopeFoundry import HardwareComponent
from Hamamatsu_ScopeFoundry.CameraDevice import HamamatsuDevice

class HamamatsuHardware(HardwareComponent):
    
    name = "HamamatsuHardware"
    
    def setup(self):
        
        self.camera = self.add_logged_quantity('camera', dtype=str, si=False, 
                                               ro=1, initial = 'No camera found' )
        
        self.temperature = self.add_logged_quantity('temperature ' + chr(176) + 'C', dtype=str, si=False, ro=1)
                                                    
        
        self.exposure_time = self.add_logged_quantity('exposure_time', dtype = float, si = False, ro = 0, 
                                                        spinbox_step = 0.01, spinbox_decimals = 6, initial = 0.01, unit = 's', reread_from_hardware_after_write = True,
                                                        vmin = 0, vmax = 10)
        
        self.internal_frame_rate = self.add_logged_quantity('internal_frame_rate', dtype = float, si = False, ro = 1,
                                                            initial = 0, unit = 'fps', reread_from_hardware_after_write = True)
        
        self.acquisition_mode = self.add_logged_quantity('acquisition_mode', dtype = str, si = False, ro = 0, 
                                                         choices = ["fixed_length", "run_till_abort"], initial = "run_till_abort", reread_from_hardware_after_write = True)
        
        self.number_frames = self.add_logged_quantity("number_frames", dtype = int, si = False, ro = 0, 
                                                      initial = 200, vmin = 1, reread_from_hardware_after_write = True)
        
        #For subarray we have imposed float, since otherwise I cannot modify the step (I should modify the logged quantities script, but I prefer left it untouched)
        self.subarrayh = self.add_logged_quantity("subarray_hsize", dtype=float, si = False, ro= 0,
                                                   spinbox_step = 4, spinbox_decimals = 0, initial = 2048, vmin = 4, vmax = 2048, reread_from_hardware_after_write = True)
        
        self.subarrayv = self.add_logged_quantity("subarray_vsize", dtype=float, si = False, ro= 0, 
                                                  spinbox_step = 4, spinbox_decimals = 0, initial = 2048, vmin = 4, vmax = 2048, reread_from_hardware_after_write = True)
        
        self.submode = self.add_logged_quantity("subarray_mode", dtype=str, si = False, ro = 1, 
                                                initial = 'ON')
        
        self.subarrayh_pos = self.add_logged_quantity('subarrayh_pos', dtype = float, si = False, ro = 0,
                                                      spinbox_step = 4, spinbox_decimals = 0, initial = 0, vmin = 0, vmax = 2044, reread_from_hardware_after_write = True,
                                                      description = "The default value 0 corresponds to the first pixel starting from the left")
        
        self.subarrayv_pos = self.add_logged_quantity('subarrayv_pos', dtype = float, si = False, ro = 0,
                                                      spinbox_step = 4, spinbox_decimals = 0, initial = 0, vmin = 0, vmax = 2044, reread_from_hardware_after_write = True,
                                                      description = "The default value 0 corresponds to the first pixel starting from the top")
        
        self.optimal_offset = self.add_logged_quantity('optimal_offset', dtype = bool, si = False, ro = 0, 
                                                       initial = True)
        
        self.binning = self.add_logged_quantity('binning', dtype = int, ro = 0,
                                                choices = [1, 2, 4], initial = 1, reread_from_hardware_after_write = True )
        
        self.trsource = self.add_logged_quantity('trigger_source', dtype=str, si=False, ro=0, 
                                                 choices = ["internal", "external"], initial = 'internal', reread_from_hardware_after_write = True)
        
        self.trmode = self.add_logged_quantity('trigger_mode', dtype=str, si=False, ro=0, 
                                               choices = ["normal", "start"], initial = 'normal', reread_from_hardware_after_write = True)
        
        self.trpolarity = self.add_logged_quantity('trigger_polarity', dtype=str, si=False, ro=0, 
                                                   choices = ["positive", "negative"], initial = 'positive', reread_from_hardware_after_write = True)
        
        self.tractive = self.add_logged_quantity('trigger_active', dtype=str, si=False, ro=0, 
                                                   choices = ["edge", "syncreadout"], initial = 'edge', reread_from_hardware_after_write = True)
        
        self.trglobal = self.add_logged_quantity('trigger_global_exposure', dtype=str, si=False, ro=0, 
                                                   choices = ["delayed", "global_reset"], initial = 'delayed', reread_from_hardware_after_write = True)
        
 
    
    def connect(self):
        """
        The initial connection does not update the value in the device,
        since there is no set_from_hardware function, so the device has
        as initial values the values that we initialize in the HamamatsuDevice
        class. I'm struggling on how I can change this. There must be some function in
        ScopeFoundry
        """
        
        
        self.hamamatsu = HamamatsuDevice(camera_id=0, frame_x=self.subarrayh.val, frame_y=self.subarrayv.val, acquisition_mode=self.acquisition_mode.val, 
                                           number_frames=self.number_frames.val, exposure=self.exposure_time.val, 
                                           trsource=self.trsource.val, trmode=self.trmode.val, trpolarity=self.trpolarity.val,
                                           tractive=self.tractive.val,
                                           subarrayh_pos=self.subarrayh_pos.val, subarrayv_pos = self.subarrayv_pos.val,
                                           binning = self.binning.val, hardware = self) #maybe with more cameras we have to change
        
        self.readOnlyWhenOpt()
        self.camera.hardware_read_func = self.hamamatsu.getModelInfo
        self.temperature.hardware_read_func = self.hamamatsu.getTemperature
        self.submode.hardware_read_func = self.hamamatsu.setSubArrayMode
        self.exposure_time.hardware_read_func = self.hamamatsu.getExposure
        self.acquisition_mode.hardware_read_func = self.hamamatsu.getAcquisition
        self.number_frames.hardware_read_func = self.hamamatsu.getNumberImages
        self.trsource.hardware_read_func = self.hamamatsu.getTriggerSource
        self.trmode.hardware_read_func = self.hamamatsu.getTriggerMode
        self.trpolarity.hardware_read_func = self.hamamatsu.getTriggerPolarity
        self.tractive.hardware_read_func = self.hamamatsu.getTriggerActive        
        self.trglobal.hardware_read_func = self.hamamatsu.getTriggerGlobalExposure
        self.subarrayh.hardware_read_func = self.hamamatsu.getSubarrayH
        self.subarrayv.hardware_read_func = self.hamamatsu.getSubarrayV
        self.subarrayh_pos.hardware_read_func = self.hamamatsu.getSubarrayHpos
        self.subarrayv_pos.hardware_read_func = self.hamamatsu.getSubarrayVpos
        self.internal_frame_rate.hardware_read_func = self.hamamatsu.getInternalFrameRate
        self.binning.hardware_read_func = self.hamamatsu.getBinning
        
        self.subarrayh.hardware_set_func = self.hamamatsu.setSubarrayH
        self.subarrayv.hardware_set_func = self.hamamatsu.setSubarrayV
        self.subarrayh_pos.hardware_set_func = self.hamamatsu.setSubarrayHpos
        self.subarrayv_pos.hardware_set_func = self.hamamatsu.setSubarrayVpos
        self.exposure_time.hardware_set_func = self.hamamatsu.setExposure
        self.acquisition_mode.hardware_set_func = self.hamamatsu.setAcquisition
        self.number_frames.hardware_set_func = self.hamamatsu.setNumberImages
        self.trsource.hardware_set_func = self.hamamatsu.setTriggerSource
        self.trmode.hardware_set_func = self.hamamatsu.setTriggerMode
        self.trpolarity.hardware_set_func = self.hamamatsu.setTriggerPolarity
        self.tractive.hardware_set_func = self.hamamatsu.setTriggerActive 
        self.trglobal.hardware_set_func = self.hamamatsu.setTriggerGlobalExposure
        self.binning.hardware_set_func = self.hamamatsu.setBinning
        
        self.optimal_offset.hardware_set_func = self.readOnlyWhenOpt
        
        self.read_from_hardware() #read from hardware at connection
        

   
    def disconnect(self):
        
        if hasattr(self, 'hamamatsu'):
            self.hamamatsu.stopAcquisition()
            self.hamamatsu.shutdown()             
            del self.hamamatsu
            
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
    
    def readOnlyWhenOpt(self, value = None):
        #Done for avoiding the changing of the subarray position in optimal offset mode
        #The "value" argument has no meaning, but I have to put at least one argument
        if self.optimal_offset.val:
            self.subarrayh_pos.change_readonly(True)
            self.subarrayv_pos.change_readonly(True)
            self.hamamatsu.setSubarrayHpos(self.hamamatsu.calculateOptimalPos(self.subarrayh.val))
            self.hamamatsu.setSubarrayVpos(self.hamamatsu.calculateOptimalPos(self.subarrayv.val))
        else:
            self.subarrayh_pos.change_readonly(False)
            self.subarrayv_pos.change_readonly(False)

            