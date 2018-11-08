from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time

class HamamatsuMeasurement(Measurement):
    
    name = "hamamatsu_plot"
    
    def setup(self):
        "..."
        self.ui_filename = sibling_path(__file__, "form.ui")
    
        self.ui = load_qt_ui_file(self.ui_filename)
        
        self.settings.New('save_h5', dtype=bool, initial=False)
        self.settings.New('refresh_period', dtype=float, unit='s', initial=0.1)
        
        self.camera = self.app.hardware['HamamatsuHardware']
        
        self.display_update_period = self.settings.refresh_period.val
        
        self.np_data = np.empty([2048,2048])
        
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
        
        # Set up pyqtgraph graph_layout in the UI
        self.imv = pg.ImageView()
        self.ui.plot_groupBox.layout().addWidget(self.imv)

        # Create PlotItem object (a set of axes)  
        
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        #self.optimize_plot_line.setData(self.buffer) 
        self.imv.setImage(np.reshape(self.np_data,(2048, 2048)).T)
        
        
    def run(self):
        
        self.camera.hamamatsu.startAcquisition()
        
        print(self.camera.hamamatsu.number_frames)
              
        for i in range(self.camera.hamamatsu.number_frames):

            # Get frames.
            [frames, dims] = self.camera.hamamatsu.getFrames()
    
            # Save frames.
            for aframe in frames:
                self.np_data = aframe.getData()
                
            print (i, len(frames))    
                #np_data.tofile(bin_fp)

        self.camera.hamamatsu.stopAcquisition()
        
        