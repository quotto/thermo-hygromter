import i2clcda
import time
import adafruit_dht
import board
import subprocess
import os
import threading
import traceback
import math

BACKLIGHT = i2clcda.LCD_BACKLIGHT_ON
BACKLIGHT_TOGGLE_INTERVAL_SECONDS=0.1
MOTION_DETECT_EVENT_GAP_SECONDS=60
# 動体検知されない間もLCDバックライトONにする閾値
THRESHOLD_BACKLIGHT_OFF=math.floor(MOTION_DETECT_EVENT_GAP_SECONDS/BACKLIGHT_TOGGLE_INTERVAL_SECONDS)

dht_Device = adafruit_dht.DHT22(board.D26)

lock = threading.Lock()

def display_info():
  global BACKLIGHT
  try:
    result=subprocess.run('vcgencmd measure_temp', shell=True, encoding='utf-8', stdout=subprocess.PIPE).stdout.split('=')
    temp=result[1].replace("\n","")

    print("temp: {}'C".format(dht_Device.temperature))
    print("humidity: {} %".format(dht_Device.humidity,temp))
    print("cpu temp: {}".format(temp))

    i2clcda.lcd_string("{}'C | CPU".format(dht_Device.temperature),i2clcda.LCD_LINE_1,BACKLIGHT)
    i2clcda.lcd_string("{} % | {}".format(dht_Device.humidity,temp),i2clcda.LCD_LINE_2,BACKLIGHT)
  except RuntimeError:
    print (traceback.format_exc())

def toggle_backlight():
  global BACKLIGHT
  print('Start toggle backlight thread')
  file_not_found_count = 0
  while True:
    if os.path.exists('/tmp/motion_detect'):
      with lock:
        file_not_found_count=0
        BACKLIGHT = i2clcda.LCD_BACKLIGHT_ON
        os.remove('/tmp/motion_detect')
        print('backlight on')
        display_info()

    else:
      file_not_found_count += 1
      if file_not_found_count == THRESHOLD_BACKLIGHT_OFF:
        with lock:
          BACKLIGHT = i2clcda.LCD_BACKLIGHT_OFF
          print('backlight off')
          display_info()
    time.sleep(BACKLIGHT_TOGGLE_INTERVAL_SECONDS)


def main():
  print('Start main')
  while True:
    with lock:
      display_info()
    time.sleep(20)

if __name__ == '__main__':
  try:
    i2clcda.lcd_init()

    thread_main = threading.Thread(target=main)
    thread_toggle_backlight = threading.Thread(target=toggle_backlight)
    thread_main.start()
    thread_toggle_backlight.start()

    thread_main.join()
    thread_toggle_backlight.join()
  except KeyboardInterrupt:
    pass
  finally:
    i2clcda.lcd_init(i2clcda.LCD_BACKLIGHT_OFF)
