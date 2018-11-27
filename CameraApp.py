""" Written by Michele Castriotta, Alessandro Zecchi, Andrea Bassi (Polimi).
   Code for creating the app class of ScopeFoundry for the Orca Flash 4V3
   
   11/18
"""

from ScopeFoundry import BaseMicroscopeApp
import os

class HamamatsuApp(BaseMicroscopeApp):
    
    name = 'HamamatsuApp'
    
    def __init__(self, *kwds): 
        """
        We need an __init__ since we want to put a new save directory 
        """
        super().__init__(*kwds) # *kwds is needed since in the main we pass as argument sys.argv, and without
                                # the *kwds this will give a problem
        self.settings['save_dir'] = "D:\\Data\\temp"
        self.settings.save_dir.hardware_set_func = self.setDirFunc #calls set dir func when the save_dir widget is changed
        
    
    def setup(self):
        
        from CameraHardware import HamamatsuHardware
        self.add_hardware(HamamatsuHardware(self))
        
        print("Adding Hardware Components")
        
        from CameraMeasurement import HamamatsuMeasurement
        self.add_measurement(HamamatsuMeasurement(self))
        
        print("Adding measurement components")
        
        self.ui.show()
        self.ui.activateWindow()
    
    def setDirFunc(self, val = None):
        """
        Gets called everytime we modify the directory.
        If it does not exist, we create a new one
        """
        
        if not os.path.isdir(self.settings['save_dir']):
            os.makedirs(self.settings['save_dir'])

if __name__ == '__main__':
    
    import sys
    app = HamamatsuApp(sys.argv)
    sys.exit(app.exec_())
    