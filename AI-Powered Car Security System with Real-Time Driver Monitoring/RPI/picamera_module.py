from picamera2 import Picamera2 
from abc import ABC,abstractclassmethod
import cv2 
class Camera_module(ABC):
    @abstractclassmethod
    def init_camera(self,conf): 
        pass 
    @abstractclassmethod
    def stop_camera(self):
        pass
    @abstractclassmethod
    def read_cam_frame(self):
        pass 
    @abstractclassmethod
    def get_cam_status(self):
        pass

class Picamera_module(Camera_module):
    def __init__(self):
        super()
        self.cam =None
        
    def init_camera(self,conf=None): 
        self.cam = Picamera2()
        conf = self.cam.create_video_configuration(main={"size":(426, 240)})
        self.cam.configure(conf)
        self.cam.start()
    def stop_camera(self): 
        if self.cam:
            self.cam.stop()  # Stops the camera capture
            self.cam.close()  # Close and release the camera
            self.cam = None
    def read_cam_frame(self):
        fr = self.cam.capture_array()
        fr = cv2.cvtColor(fr,cv2.COLOR_RGB2BGR)
        return fr
    def get_cam_status(self):
        return self.cam.is_open

if __name__ == '__main__': 
    import cv2 
    cam = Picamera_module()
    cam.init_camera()
    print ("status ... ") 
    print (cam.get_cam_status())
    while True: 
        frame = cam.read_cam_frame()
        cv2.imshow("feed",frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    cam.stop()
