""" Written by Michele Castriotta, Alessandro Zecchi, Andrea Bassi (Polimi).
   Code for creating the measurement class of ScopeFoundry for the Orca Flash 4V3
   
   11/18
"""

from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time


class HamamatsuMeasurement(Measurement):
    
    name = "hamamatsu_image"
    
    def setup(self):
        "..."

        self.ui_filename = sibling_path(__file__, "form.ui")
    
        self.ui = load_qt_ui_file(self.ui_filename)
        
        self.settings.New('save_h5', dtype=bool, initial=False)
        self.settings.New('refresh_period', dtype=float, unit='s', spinbox_decimals = 4, initial=0.001)
        self.settings.New('autoLevels', dtype=bool, initial=True, hardware_set_func=self.setautoLevels)
        self.settings.New('level_min', dtype=int, initial=60, hardware_set_func=self.setminLevel)
        self.settings.New('level_max', dtype=int, initial=150, hardware_set_func=self.setmaxLevel)
        self.settings.New('threshold', dtype=int, initial=500, hardware_set_func=self.setThreshold)
        self.camera = self.app.hardware['HamamatsuHardware']
        
        self.display_update_period = self.settings.refresh_period.val
        self.autoLevels = self.settings.autoLevels.val
        self.level_min = self.settings.level_min.val
        self.level_max = self.settings.level_max.val
        
        #self.img = pg.gaussianFilter(np.random.normal(size=(400, 600)), (5, 5)) * 20 + 100
        
    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
                
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        
        # connect ui widgets of live settings
        self.settings.autoLevels.connect_to_widget(self.ui.autoLevels_checkBox)
        self.settings.level_min.connect_to_widget(self.ui.min_doubleSpinBox) #spinBox doesn't work nut it would be better
        self.settings.level_max.connect_to_widget(self.ui.max_doubleSpinBox) #spinBox doesn't work nut it would be better
        
        # Set up pyqtgraph graph_layout in the UI
        self.imv = pg.ImageView()
        self.ui.plot_groupBox.layout().addWidget(self.imv)
        
        # Image initialization
        self.image = np.zeros([int(self.camera.subarrayh.val),int(self.camera.subarrayv.val)],dtype=np.uint16)
        
        # Create PlotItem object (a set of axes)  
        
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        #self.optimize_plot_line.setData(self.buffer) 

        #self.imv.setImage(np.reshape(self.np_data,(self.camera.subarrayh.val, self.camera.subarrayv.val)).T)
        #self.imv.setImage(self.image, autoLevels=False, levels=(100,340))
        
        #levels should not be sent when autoLevels is True, otherwise the image is displayed with them
        if self.autoLevels == False:
            self.imv.setImage(self.image, autoLevels=self.autoLevels, levels=(self.level_min, self.level_max))
        else:
            self.imv.setImage(self.image, autoLevels=self.autoLevels)
            
    def run(self):
        
        self.image = np.empty([int(self.camera.subarrayh.val),int(self.camera.subarrayv.val)],dtype=np.uint16)
        self.image[0,0]=1 #........
        #print(self.camera.hamamatsu.getPropertyValue("internal_frame_rate"))
        try:
            
            self.camera.read_from_hardware()
            self.camera.hamamatsu.startAcquisition()
            
            index = 0
            
            if self.camera.acquisition_mode.val == "fixed_length":
            
                if self.settings['save_h5']:
                    self.initH5()
                    
                #for i in range(self.camera.hamamatsu.number_image_buffers):
                while index < self.camera.hamamatsu.number_image_buffers:
        
                    # Get frames.
                    #The camera stops acquiring once the buffer is terminated (in snapshot mode)
                    [frames, dims] = self.camera.hamamatsu.getFrames()
                    
                    # Save frames.
                    for aframe in frames:
                        
                        self.np_data = aframe.getData()  
                        self.image = np.reshape(self.np_data,(int(self.camera.subarrayv.val), int(self.camera.subarrayh.val))).T # T is faster. Why?
                        if self.settings['save_h5']:
                            self.image_h5[index,:,:] = self.image # saving to the h5 dataset
                            self.h5file.flush() # maybe is not necessary
                                            
                        if self.interrupt_measurement_called:
                            break
                        index+=1
                        print(index)
                    
                    if self.interrupt_measurement_called:
                        break    
                    #index = index + len(frames)
                        #np_data.tofile(bin_fp)
                    self.settings['progress'] = index*100./self.camera.hamamatsu.number_image_buffers
                    
            elif self.camera.acquisition_mode.val == "run_till_abort":
                
                save = 0
                
                while not self.interrupt_measurement_called:
                    
                    [frame, dims] = self.camera.hamamatsu.getNewestFrame()        
                    self.np_data = frame.getData()
                    self.image = np.reshape(self.np_data,(int(self.camera.subarrayv.val), int(self.camera.subarrayh.val))).T
                    
                    if self.settings['save_h5']:
                        
                        if save == 0:
                            self.initH5()
                            save = 1 #at next cycle, we dont do initH5 again (we have already created the file)
                        
                        total = np.sum(self.np_data)
                        frames = []
                        newest_frame_index = self.camera.hamamatsu.buffer_index
                        
                        if total > self.settings['threshold']*self.camera.hamamatsu.frame_x*self.camera.hamamatsu.frame_y:
                            print("\n \n ******* \n \n Saving :D !\n \n *******")
                            j = 0
                            
                            while(len(frames)) < self.camera.number_frames.val: #we want 200 frames
                                upgraded_newest_frame_index, upgraded_frame_number = self.camera.hamamatsu.getTransferInfo() #we upgrade the transfer information
                                
                                if newest_frame_index < upgraded_newest_frame_index: #acquisition has not reached yet the end of the buffer    
                                
                                    for i in range(newest_frame_index, upgraded_newest_frame_index + 1):
                                        
                                        if j < self.camera.number_frames.val:
                                            frames.append(self.camera.hamamatsu.getRequiredFrame(i)[0])
                                            self.np_data = frames[-1].getData() #-1 takes the last element
                                            self.image = np.reshape(self.np_data,(int(self.camera.subarrayv.val), int(self.camera.subarrayh.val))).T
                                            self.image_h5[j,:,:] = self.image # saving to the h5 dataset
                                            j+=1
                                
                                else: #acquisition has reached the end of the buffer
                                    
                                    for i in range(newest_frame_index, self.camera.hamamatsu.number_image_buffers + 1):
                                        #put elements in new_frames until the end of buffer
                                        if j < self.camera.number_frames.val:
                                            frames.append(self.camera.hamamatsu.getRequiredFrame(i)[0])
                                            self.np_data = frames[-1].getData()
                                            self.image = np.reshape(self.np_data,(int(self.camera.subarrayv.val), int(self.camera.subarrayh.val))).T
                                            self.image_h5[j,:,:] = self.image # saving to the h5 dataset
                                            j+=1
                                    
                                    for i in range(upgraded_newest_frame_index):
                                        #put elements in new_frames until the new index
                                        if j < self.camera.number_frames.val:
                                            frames.append(self.camera.hamamatsu.getRequiredFrame(i)[0])
                                            self.np_data = frames[-1].getData()
                                            self.image = np.reshape(self.np_data,(int(self.camera.subarrayv.val), int(self.camera.subarrayh.val))).T
                                            self.image_h5[j,:,:] = self.image # saving to the h5 dataset
                                            j+=1
                                
                                newest_frame_index = upgraded_newest_frame_index
                                
                            self.interrupt()
                        
            
#             elif self.camera.acquisition_mode.val == "Threshold_h5":
#                 
#                 if self.settings['save_h5']:
#                     self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
#                     self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
#                     img_size=self.image.shape
#                     length=400
#                     self.image_h5 = self.h5_group.create_dataset(name  = 't0/c0/image', 
#                                                                   shape = ( length, img_size[0], img_size[1]),
#                                                                   dtype = self.image.dtype,
#                                                                   )
#                     """
#                     THESE NAMES MUST BE CHANGED
#                     """
#                     self.image_h5.dims[0].name = "z"
#                     self.image_h5.dims[1].label = "x"
#                     self.image_h5.dims[2].label = "y"
#                     #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
#                     self.image_h5.attrs['element_size_um'] =  [1,1,1]
#                 
#                 len_frames = 0
#                 
#                 while not self.interrupt_measurement_called:
#                     
#                     frames, len_frames = self.camera.hamamatsu.getNewestFrameThreshold()
#                     if self.interrupt_measurement_called:
#                         break
#                     j=0
#                     for aframe in frames:
#                         
#                         self.np_data = aframe.getData()
#                         self.image = np.reshape(self.np_data,(int(self.camera.subarrayv.val), int(self.camera.subarrayh.val))).T
#                             
#                         if self.interrupt_measurement_called:
#                             break
#                         j+=1
                    
        finally:
            
            self.camera.hamamatsu.stopAcquisition()
            if self.settings['save_h5']:
                self.h5file.close() # close connection     

    def setautoLevels(self, autoLevels):
        self.autoLevels = autoLevels
        
    def setminLevel(self, level_min):
        self.level_min = level_min
        
    def setmaxLevel(self, level_max):
        self.level_max = level_max
        
    def setThreshold(self, threshold):
        self.threshold = threshold
        
    def initH5(self):
        
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        img_size=self.image.shape
        length=self.camera.hamamatsu.number_image_buffers
        self.image_h5 = self.h5_group.create_dataset(name  = 't0/c0/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype,
                                                      )
        """
        THESE NAMES MUST BE CHANGED
        """
        self.image_h5.dims[0].label = 'z'
        self.image_h5.dims[1].label = "x"
        self.image_h5.dims[2].label = "y"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5.attrs['element_size_um'] =  [1,1,1]