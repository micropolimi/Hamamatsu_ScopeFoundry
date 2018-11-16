""" Written by Michele Castriotta, Alessandro Zecchi, Andrea Bassi (Polimi).
   Code for creating the app class of ScopeFoundry for the Orca Flash 4V3
   
   11/18
"""

from ScopeFoundry import BaseMicroscopeApp

class HamamatsuApp(BaseMicroscopeApp):
    
    name = 'HamamatsuApp'
    
    def setup(self):
        
        from CameraHardware import HamamatsuHardware
        self.add_hardware(HamamatsuHardware(self))
        
        print("Adding Hardware Components")
        
        from CameraMeasurement import HamamatsuMeasurement
        self.add_measurement(HamamatsuMeasurement(self))
        
        print("Adding measurement components")
        
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
    
    import sys
    app = HamamatsuApp(sys.argv)
    sys.exit(app.exec_())
    