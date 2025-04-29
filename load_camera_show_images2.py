import sys
import time
import numpy as np
import imagingcontrol4 as ic4

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QTimer

ic4.Library.init()

class ImageWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Viewer - FPS: 0.00")
        
        # QLabel to display the image
        self.image_label = QLabel(self)
        self.setCentralWidget(self.image_label)
        
        # Enable resizing and moving
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint)

        # Set initial window size to 640x640 pixels
        self.resize(640, 640)

        # Initialize FPS tracking
        self.frame_count = 0
        self.start_time = time.time()
        self.fps_update_interval = 1  # Update FPS every second
        self.last_fps_update_time = time.time()

    def update_image(self, image_data):
        """
        Update the window with the new image and resize it to fit the window.
        Also updates the FPS counter in the window title.

        :param image_data: A NumPy array (H x W or H x W x 3), or QImage.
        """
        if isinstance(image_data, np.ndarray):
            height, width = image_data.shape[:2]
            if len(image_data.shape) == 2:  # Grayscale image
                qimage = QImage(image_data.data, width, height, QImage.Format_Grayscale8)
            elif len(image_data.shape) == 3 and image_data.shape[2] == 3:  # RGB image
                qimage = QImage(image_data.data, width, height, 3 * width, QImage.Format_RGB888)
            else:
                raise ValueError("NumPy array must be either grayscale (H x W) or RGB (H x W x 3)")
            pixmap = QPixmap.fromImage(qimage)
        else:
            raise ValueError("Image data must be a NumPy array.")

        # Get the current size of the window and scale the image only if the window size changed
        window_size = self.size()
        scaled_pixmap = pixmap.scaled(window_size.width(), window_size.height(), Qt.KeepAspectRatio)

        # Set the pixmap in the QLabel
        self.image_label.setPixmap(scaled_pixmap)

        # Update FPS counter
        self.frame_count += 1
        current_time = time.time()
        elapsed_time = current_time - self.last_fps_update_time
        if elapsed_time >= self.fps_update_interval:
            fps = self.frame_count / elapsed_time
            self.setWindowTitle(f"Image Viewer - FPS: {fps:.2f}")
            self.frame_count = 0
            self.last_fps_update_time = current_time

def format_device_info(device_info: ic4.DeviceInfo) -> str:
    return f"Model: {device_info.model_name} Serial: {device_info.serial}"

def print_device_list():
    print("Enumerating all attached video capture devices...")

    device_list = ic4.DeviceEnum.devices()

    if len(device_list) == 0:
        print("No devices found")
        return

    print(f"Found {len(device_list)} devices:")

    for device_info in device_list:
        print(format_device_info(device_info))

print_device_list()

class CameraHandler:
    def __init__(self):
        self.grabber = ic4.Grabber()
        self.sink = ic4.SnapSink()
        
        # Open the first available video capture device
        first_device_info = ic4.DeviceEnum.devices()[0]
        self.grabber.device_open(first_device_info)

        # # Set the resolution to 5472x3648
        self.grabber.device_property_map.set_value(ic4.PropId.WIDTH, 5472)
        self.grabber.device_property_map.set_value(ic4.PropId.HEIGHT, 3648)
        # Configure the device to output images in the Mono8 pixel format
        self.grabber.device_property_map.set_value(ic4.PropId.PIXEL_FORMAT, ic4.PixelFormat.Mono8)
        # Configure the exposure time to 5ms (5000µs)
        self.grabber.device_property_map.set_value(ic4.PropId.EXPOSURE_AUTO, "Off")
        self.grabber.device_property_map.set_value(ic4.PropId.EXPOSURE_TIME, 6250.0)
        # Enable GainAuto
        # grabber.device_property_map.set_value(ic4.PropId.GAIN_AUTO, "Continuous")

        self.grabber.device_property_map.set_value(ic4.PropId.BINNING_HORIZONTAL,2)
        self.grabber.device_property_map.set_value(ic4.PropId.BINNING_VERTICAL,2)

        # Configure the grabber
        self.grabber.device_property_map.set_value(ic4.PropId.WIDTH, 2736)
        self.grabber.device_property_map.set_value(ic4.PropId.HEIGHT, 1824)
        self.grabber.device_property_map.set_value(ic4.PropId.PIXEL_FORMAT, ic4.PixelFormat.Mono8)
        max_framerate = int(self.grabber.device_property_map.find(ic4.PropId.ACQUISITION_FRAME_RATE).maximum)
        self.grabber.device_property_map.set_value(ic4.PropId.ACQUISITION_FRAME_RATE, max_framerate)
        self.grabber.stream_setup(self.sink, setup_option=ic4.StreamSetupOption.ACQUISITION_START)

    def get_image(self):
        return self.sink.snap_single(1000).numpy_wrap().squeeze()

def main():
    app = QApplication(sys.argv)
    
    # Create the main window
    window = ImageWindow()
    window.show()

    # Create the camera handler
    camera_handler = CameraHandler()

    # Create a timer to update the image every 50ms for faster refresh
    def update_frame():
        try:
            np_img = camera_handler.get_image()
            window.update_image(np_img)
        except ic4.IC4Exception as ex:
            print(ex.message)

    timer = QTimer()
    timer.timeout.connect(update_frame)
    timer.start(1)  # Update every 50ms (20 FPS target)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
