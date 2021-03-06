# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Main script to run the object detection routine."""
import argparse
import sys
import time

import pygame
from PIL import Image
import pygame
import pygame.camera
from pygame.locals import *


# 物体検出モジュール
from object_detector import ObjectDetector
from object_detector import ObjectDetectorOptions
import utils

# モータ制御モジュール
from control_value import ControlValue_v1

# シリアル通信モジュール
import serial



import time

def run(model: str, camera_id: int, width: int, height: int, num_threads: int,
        enable_edgetpu: bool, offimage: bool, offserial: bool) -> None:
  """Continuously run inference on images acquired from the camera.

  Args:
    model: Name of the TFLite object detection model.
    camera_id: The camera id to be passed to OpenCV.
    width: The width of the frame captured from the camera.
    height: The height of the frame captured from the camera.
    num_threads: The number of CPU threads to run the model.
    enable_edgetpu: True/False whether the model is a EdgeTPU model.
    offimage: True/False Whether to show the image.
    offserial: True/False Whether to show the erial.
  """


  counter, fps = 0, 0
  start_time = time.time()



  pygame.init()
  pygame.camera.init()
  camlist = pygame.camera.list_cameras()
  if camlist:
      cam = pygame.camera.Camera(camlist[0],(640,360))

      
  cam.start()

  size = width, height = 640, 360
  if not offimage:
    screen = pygame.display.set_mode(size)


  row_size = 20  # pixels
  left_margin = 24  # pixels
  text_color = (0, 0, 255)  # red
  font_size = 1
  font_thickness = 1
  fps_avg_frame_count = 10

  # Initialize the object detection model
  options = ObjectDetectorOptions(
      label_allow_list=['person'],
      num_threads=num_threads,
      score_threshold=0.3,
      max_results=1,
      enable_edgetpu=enable_edgetpu)
  detector = ObjectDetector(model_path=model, options=options)

  ORIGIN = (0, 0)

  if not offserial:
    ser = serial.Serial('/dev/ttyUSB0',19200)

  # Continuously capture images from the camera and run inference

  ConVa = ControlValue_v1()
  ConVa.set_velocity(2,5)
  while 1:

    time0 = time.time()
    for event in pygame.event.get():
      if event.type == pygame.QUIT: sys.exit()

    counter += 1

    image = cam.get_image()
    time1 = time.time()
    print("撮像---->",(time1-time0)*1000)

    
    image = pygame.surfarray.array3d(image)


    # Run object detection estimation using the model.
    detections = detector.detect(image)
    time2 = time.time()
    print("計算---->",(time2-time1)*1000)

    # Draw keypoints and edges on input image
    image, detectpoints = utils.visualize(image, detections)
    
    

    # Calculate the FPS
    if counter % fps_avg_frame_count == 0:
      end_time = time.time()
      fps = fps_avg_frame_count / (end_time - start_time)
      start_time = time.time()

    # Show the FPS
    fps_text = 'FPS = {:.1f}'.format(fps)
    text_location = (left_margin, row_size)

    print(fps_text)

    if not offimage:
      surf = pygame.surfarray.make_surface(image)
      screen.blit(surf, ORIGIN)
      pygame.display.flip()
    

    topleft,bottomright = detectpoints
    print(topleft,bottomright)
    ConVa.cal_center(topleft,bottomright,width, height)

    
    ConVa.detect_mode()
    
    maxv,b_v1,b_v2,b_v3 = ConVa.get_control_value()
    print(maxv,b_v1,b_v2,b_v3)

    if not offserial:
      ser.write((maxv).to_bytes(1, byteorder='little', signed=True))
      ser.write((b_v1).to_bytes(1, byteorder='little', signed=True))
      ser.write((b_v3).to_bytes(1, byteorder='little', signed=True))
      ser.write((b_v2).to_bytes(1, byteorder='little', signed=True))





def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      '--model',
      help='Path of the object detection model.',
      required=False,
      default='efficientdet_lite0.tflite')
  parser.add_argument(
      '--cameraId', help='Id of camera.', required=False, type=int, default=0)
  parser.add_argument(
      '--frameWidth',
      help='Width of frame to capture from camera.',
      required=False,
      type=int,
      default=640)
  parser.add_argument(
      '--frameHeight',
      help='Height of frame to capture from camera.',
      required=False,
      type=int,
      default=480)
  parser.add_argument(
      '--numThreads',
      help='Number of CPU threads to run the model.',
      required=False,
      type=int,
      default=4)
  parser.add_argument(
      '--enableEdgeTPU',
      help='Whether to run the model on EdgeTPU.',
      action='store_true',
      required=False,
      default=False)
  parser.add_argument(
      '--offimage',
      help='Whether to off the image.',
      required=False,
      action='store_true'
      )
  parser.add_argument(
      '--offserial',
      help='Whether to off the serial.',
      required=False,
      action='store_true'
      )
  args = parser.parse_args()

  run(args.model, int(args.cameraId), args.frameWidth, args.frameHeight,
      int(args.numThreads), bool(args.enableEdgeTPU), bool(args.offimage), bool(args.offserial))


if __name__ == '__main__':
  main()

