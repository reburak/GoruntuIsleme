pip install opencv-python mediapipe pyautogui numpy screeninfo

# Hand-Controlled Mouse

This project allows users to control the mouse cursor using hand gestures detected through a webcam. The system uses OpenCV, MediaPipe, and PyAutoGUI to track hand movements and perform actions like moving the cursor, clicking, dragging, and scrolling.

## Features
- **Hand Tracking**: Uses MediaPipe Hands to detect and track hand movements.
- **Cursor Movement**: Maps hand movements to screen coordinates.
- **Click & Drag**: Detects gestures for left-clicking, right-clicking, and dragging.
- **Scrolling**: Allows scrolling through gestures.
- **Calibration System**: Adjusts tracking for improved accuracy.

## Installation
To install the required dependencies, run:

```sh
pip install opencv-python mediapipe pyautogui numpy screeninfo
```

### Additional Dependencies
- **Tkinter**: Pre-installed in most Python distributions. If needed:
  - Windows: `pip install tk`
  - Linux: `sudo apt-get install python3-tk`

## Usage
1. Run the script:
   ```sh
   python parmakkontrol.py
   ```
2. Click the **Start** button in the GUI to begin calibration.
3. Follow on-screen instructions to calibrate hand tracking.
4. Once calibrated, move your hand to control the cursor.
5. Perform gestures for clicking, dragging, and scrolling.

## Controls
- **Move Cursor**: Move your hand in front of the camera.
- **Left Click**: Touch index finger and thumb together.
- **Right Click**: Touch middle finger and thumb together.
- **Scroll**: Move index finger up/down.
- **Drag**: Hold left-click gesture while moving hand.

## Calibration Process
During calibration, the user must position their cursor on specific screen locations for a few seconds. This helps the system map hand movements accurately.

## Configuration
- **Sensitivity Adjustments**: Modify `self.movement_scale` in `HandMouseController` to fine-tune cursor movement.
- **Click Threshold**: Adjust `thumb_index_dist` and `thumb_middle_dist` to change click detection sensitivity.
- **Scroll Speed**: Modify `self.scroll_speed` in `HandMouseController`.

## Troubleshooting
- **Cursor not moving?** Ensure the camera is working and positioned correctly.
- **Gestures not detected?** Adjust lighting conditions for better hand visibility.
- **Calibration issues?** Restart the script and redo the calibration.

## Author
Developed by [Your Name].

## License
This project is open-source and available under the MIT License.

