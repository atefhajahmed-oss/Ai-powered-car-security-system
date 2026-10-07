import cv2
from abc import ABC, abstractclassmethod

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

class WebCamera_module(Camera_module):
    def __init__(self):
        super().__init__()
        self.cam = None
        
    def init_camera(self, conf=None): 
        print("Initializing webcam...")
        try:
            # Try different backends
            backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
            for backend in backends:
                try:
                    self.cam = cv2.VideoCapture(0 + backend)
                    if self.cam.isOpened():
                        break
                except:
                    continue
                    
            if not self.cam or not self.cam.isOpened():
                raise Exception("Could not open webcam with any backend")
            
            # Set camera properties for better performance
            self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cam.set(cv2.CAP_PROP_FPS, 30)
            
            # Try reading a test frame
            for _ in range(5):  # Try a few times to get a frame
                ret, frame = self.cam.read()
                if ret and frame is not None:
                    print("Webcam initialized successfully")
                    return
                    
            raise Exception("Could not read frame from webcam")
                
        except Exception as e:
            print(f"Failed to initialize webcam: {str(e)}")
            if self.cam is not None:
                self.cam.release()
            self.cam = None
            raise
            
    def stop_camera(self): 
        if self.cam is not None:
            self.cam.release()
            self.cam = None
            
    def read_cam_frame(self):
        if self.cam is None or not self.cam.isOpened():
            return None
            
        for _ in range(3):  # Try up to 3 times to read a frame
            ret, frame = self.cam.read()
            if ret and frame is not None:
                return frame
        return None
        
    def get_cam_status(self):
        return self.cam is not None and self.cam.isOpened()

if __name__ == '__main__': 
    # Test the webcam module
    try:
        print("Testing webcam module...")
        cam = WebCamera_module()
        cam.init_camera()
        print("Camera status:", cam.get_cam_status())
        
        while True:
            frame = cam.read_cam_frame()
            if frame is None:
                print("Could not read frame")
                continue
                
            cv2.imshow("Webcam Test", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except Exception as e:
        print(f"Test failed: {str(e)}")
    finally:
        if 'cam' in locals():
            cam.stop_camera()
        cv2.destroyAllWindows()
