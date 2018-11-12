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

    