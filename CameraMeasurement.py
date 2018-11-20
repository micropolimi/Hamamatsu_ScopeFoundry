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
        
        # coonect ui widgets of live settings
        self.settings.autoLevels.connect_to_widget(self.ui.autoLevels_checkBox)
        self.settings.level_min.connect_to_widget(self.ui.min_doubleSpinBox) #spinBox doesn't work nut it would be better
        self.settings.level_max.connect_to_widget(self.ui.max_doubleSpinBox) #spinBox doesn't work nut it would be better
        
        # Set up pyqtgraph graph_layout in the UI
        self.imv = pg.ImageView()
        self.ui.plot_groupBox.layout().addWidget(self.imv)
        
        # Image intialization
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
        
        
        #print(self.camera.hamamatsu.getPropertyValue("internal_frame_rate"))
        try:
            
            self.camera.read_from_hardware()
            self.camera.hamamatsu.startAcquisition()
            
            index = 0
            
            if self.camera.acquisition_mode.val == "fixed_length":
            
                if self.settings['save_h5']:
                    self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
                    self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
                    img_size=self.image.shape
                    length=self.camera.hamamatsu.number_image_buffers
                    self.image_h5 = self.h5_group.create_dataset(name  = 't0/c0/image', 
                                                                  shape = [ length, img_size[0], img_size[1]],
                                                                  dtype = self.image.dtype)
                    #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
                    self.image_h5.attrs['element_size_um'] =  [1,1,1]
                    
                
            
                
                #for i in range(self.camera.hamamatsu.number_image_buffers):
                while index < self.camera.hamamatsu.number_image_buffers:
                    
                    """Il ciclo sopra nonha tanto senso, perche nel caso in cui lui acquisisca
                     piu immagini in un colpo, ho dei cicli inutilizzati (quelli in cui il maxbacklog == 0)
                     Cambiare e fare in modo da rendere il  codice sensato
                    """
        
                    # Get frames.
                    #The camera stops acquiring once the buffer is terminated (in snapshot mode)
                    [frames, dims] = self.camera.hamamatsu.getFrames()
                    
                    # Save frames.
                    for aframe in frames:
                        
                        self.np_data = aframe.getData()  
                        self.image = np.reshape(self.np_data,(int(self.camera.subarrayv.val), int(self.camera.subarrayh.val))).T
                        if self.settings['save_h5']:
                            self.image_h5[index,:,:] = self.image
                            self.h5file.flush()
                                            
                        if self.interrupt_measurement_called: #this does not work
                            break
                        index+=1
                        print(index)
                    
                    if self.interrupt_measurement_called:
                        break    
                    #index = index + len(frames)
                        #np_data.tofile(bin_fp)
                    self.settings['progress'] = index*100./self.camera.hamamatsu.number_image_buffers
                    
            else:
                
                while not self.interrupt_measurement_called:
                    
                    [frame, dims] = self.camera.hamamatsu.getLastFrame()
                                                          
                    self.np_data = frame.getData()
                    self.image = np.reshape(self.np_data,(int(self.camera.subarrayv.val), int(self.camera.subarrayh.val))).T
                    # print (i, len(frames))    
                    
        finally:
            
            self.camera.hamamatsu.stopAcquisition()
            if self.settings['save_h5']:
                self.h5file.close()        

    def setautoLevels(self, autoLevels):
        self.autoLevels = autoLevels
        
    def setminLevel(self, level_min):
        self.level_min = level_min
        
    def setmaxLevel(self, level_max):
        self.level_max = level_max