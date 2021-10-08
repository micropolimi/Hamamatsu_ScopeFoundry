""" 
   Written by Michele Castriotta, Alessandro Zecchi, Andrea Bassi (Polimi).
   Code for creating the measurement class of ScopeFoundry for the Orca Flash 4V3
   11/18
"""

from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import os
import time
        


class HamamatsuMeasurement(Measurement):
    
    name = "hamamatsu_image"
        
    def setup(self):
        
        "..."

        self.ui_filename = sibling_path(__file__, "form.ui")
        
    
        self.ui = load_qt_ui_file(self.ui_filename)
        self.settings.New('save_h5', dtype=bool, initial=False )
        self.settings.New('refresh_period', dtype=float, unit='s', spinbox_decimals = 4, initial=0.04, vmin = 0)
        self.settings.New('auto_range', dtype=bool, initial=True )
        self.settings.New('auto_levels', dtype=bool, initial=True )
        self.settings.New('level_min', dtype=int, initial=60 )
        self.settings.New('level_max', dtype=int, initial=150 )
        self.camera = self.app.hardware['HamamatsuHardware']
        
        
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
        self.settings.auto_levels.connect_to_widget(self.ui.autoLevels_checkBox)
        self.settings.auto_range.connect_to_widget(self.ui.autoRange_checkBox)
        self.settings.level_min.connect_to_widget(self.ui.min_doubleSpinBox) #spinBox doesn't work nut it would be better
        self.settings.level_max.connect_to_widget(self.ui.max_doubleSpinBox) #spinBox doesn't work nut it would be better
        
        # Set up pyqtgraph graph_layout in the UI
        self.imv = pg.ImageView()
        self.ui.plot_groupBox.layout().addWidget(self.imv)
        
        
    def update_display(self):
        """
        Displays the numpy array called self.image.  
        This function runs repeatedly and automatically during the measurement run,
        its update frequency is defined by self.display_update_period.
        """
        
        self.display_update_period = self.settings['refresh_period'] 
        
        # length = self.camera.hamamatsu.number_image_buffers
        length = self.camera.number_frames.val
        if hasattr(self, 'frame_index'):
            self.settings['progress'] = (self.frame_index +1) * 100/length 
        
        if hasattr(self, 'image'):
            self.imv.setImage(self.image,
                                autoLevels = self.settings.auto_levels.val,
                                autoRange = self.settings.auto_range.val,
                                levelMode = 'mono'
                                )
            
            if self.settings['auto_levels']:
                lmin,lmax = self.imv.getHistogramWidget().getLevels()
                self.settings['level_min'] = lmin
                self.settings['level_max'] = lmax
            else:
                self.imv.setLevels( min= self.settings['level_min'],
                                    max= self.settings['level_max'])
            
            
             
    def run(self):
        
        
        self.frame_index = -1
        self.eff_subarrayh = int(self.camera.subarrayh.val/self.camera.binning.val)
        self.eff_subarrayv = int(self.camera.subarrayv.val/self.camera.binning.val)
        
        self.camera.read_from_hardware()

        self.camera.hamamatsu.startAcquisition()
        
        
        
        if self.camera.acquisition_mode.val == "fixed_length":
            
            frame_index = 0
            
            if self.settings['save_h5']:
                self.initH5()
                print("\n \n ******* \n \n Saving :D !\n \n *******")
                
            while frame_index < self.camera.hamamatsu.number_image_buffers:
    
                # Get frames.
                #The camera stops acquiring once the buffer is terminated (in snapshot mode)
                [frames, dims] = self.camera.hamamatsu.getFrames()
                
                # Save frames.
                for aframe in frames:
                    
                    self.np_data = aframe.getData()  
                    self.image = np.reshape(self.np_data,(self.eff_subarrayv, self.eff_subarrayh)) 
                    if self.settings['save_h5']:
                        self.image_h5[frame_index,:,:] = self.image
                        self.h5file.flush() 
                                        
                    # if self.interrupt_measurement_called: # TODO remove
                    #     break # TODO remove
                    frame_index += 1
                    print(frame_index) #TODO remove
                    self.frame_index = frame_index 
                
                    if self.interrupt_measurement_called:
                        break    
                
                
        elif self.camera.acquisition_mode.val == "run_till_abort":
            
            save = True
            
            while not self.interrupt_measurement_called:
                
                [frame, dims] = self.camera.hamamatsu.getLastFrame()        
                self.np_data = frame.getData()
                self.image = np.reshape(self.np_data,(self.eff_subarrayv, self.eff_subarrayh))
                
                                    
                if self.settings['save_h5']:
                    
                    if save:
                        self.initH5()
                        save = False #at next cycle, we don't do initH5 again (we have already created the file)
                    
                    last_frame_index = self.camera.hamamatsu.buffer_index
                   
                    print("\n \n ******* \n \n Saving :D !\n \n *******")
                    j = 0
                    stalking_number = 0
                    remaining = False
                    while j < self.camera.number_frames.val: 
                        
                        self.get_and_save_Frame(j,last_frame_index)
                        last_frame_index = self.update_frame_index(last_frame_index)
                        
                        j+=1
                        
                        if not remaining:
                            # upgraded_last_frame_index = self.camera.hamamatsu.getTransferInfo()[0] # upgrades the transfer information
                            # The stalking_number represents the relative steps the camera has made in acquisition with respect to the saving.
                            stalking_number = stalking_number + self.camera.hamamatsu.backlog - 1
                                
                            if stalking_number + self.camera.hamamatsu.backlog > self.camera.hamamatsu.number_image_buffers: 
                                self.camera.hamamatsu.stopAcquisitionNotReleasing() #stop acquisition when we know that at next iteration, some images may be rewritten
                                remaining = True #if the buffer reach us, we execute the "while" without the "if not remaining" block.
                    
                        self.frame_index = j        
                    self.interrupt()
                    self.camera.hamamatsu.stopAcquisition()
       
            
        self.camera.hamamatsu.stopAcquisition()

        if self.settings['save_h5']:
            self.h5file.close() # close h5 file  
        self.settings['save_h5'] = False


    def create_saving_directory(self):
        if not os.path.isdir(self.app.settings['save_dir']):
            os.makedirs(self.app.settings['save_dir'])
        
    
    def initH5(self):
        """
        Initialization operations for the h5 file.
        """
        self.create_saving_directory()
        
        # file name creation
        timestamp = time.strftime("%y%m%d_%H%M%S", time.localtime())
        sample = self.app.settings['sample']
        #sample_name = f'{timestamp}_{self.name}_{sample}.h5'
        if sample == '':
            sample_name = '_'.join([timestamp, self.name])
        else:
            sample_name = '_'.join([timestamp, self.name, sample])
        fname = os.path.join(self.app.settings['save_dir'], sample_name + '.h5')
        
        # file creation
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self, fname = fname)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        
        
        img_size = self.image.shape
        length = self.camera.hamamatsu.number_image_buffers
        self.image_h5 = self.h5_group.create_dataset( name  = 't0/c0/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      )
        
        self.image_h5.dims[0].label = "z"
        self.image_h5.dims[1].label = "y"
        self.image_h5.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5.attrs['element_size_um'] =  [1,1,1] # required for compatibility with imageJ
        

   
    def get_and_save_Frame(self, saveindex, lastframeindex):
        """
        Get the data at the lastframeindex, and 
        save the reshaped data into an h5 file.
        saveindex is an index representing the position of the saved image
        in the h5 file. 
        Update the progress bar.
        """
           
        frame = self.camera.hamamatsu.getRequiredFrame(lastframeindex)[0]
        self.np_data = frame.getData()
        self.image = np.reshape(self.np_data,(self.eff_subarrayv, self.eff_subarrayh))
        self.image_h5[saveindex,:,:] = self.image # saving to the h5 dataset
        self.h5file.flush() # maybe is not necessary
        
    
    def update_frame_index(self, last_frame_index):
        """
        Update the index of the image to fetch from buffer. 
        If we reach the end of the buffer, we reset the index.
        """
        last_frame_index += 1
        
        if last_frame_index > self.camera.hamamatsu.number_image_buffers - 1: #if we reach the end of the buffer
            last_frame_index = 0 #reset
        
        return last_frame_index