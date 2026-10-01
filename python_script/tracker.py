# -*- coding: utf-8 -*-
import json
import os
import sys
import cv2
import numpy as np
import pyautogui

pyautogui.FAILSAFE = False


def nothing(x):
  pass


# Archivo para guardar la calibración de la cámara/pantalla
CONFIG_FILE = "calibration_config.json"


def load_config():
  if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
      return json.load(f)
  return None


def save_config(config):
  with open(CONFIG_FILE, "w") as f:
    json.dump(config, f)


def run_screen_calibration(cap):
  """Calibración interactiva de las 4 esquinas de la pantalla."""
  screen_w, screen_h = pyautogui.size()

  # Crear ventana transparente o completa para guiar al usuario
  cv2.namedWindow(
      "Calibracion de Pantalla", cv2.WINDOW_NORMAL
  )
  cv2.setWindowProperty(
      "Calibracion de Pantalla", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
  )

  # Las 4 esquinas donde aparecerá el cuadrado guía
  corners = [
      ("Esquina Superior Izquierda", 50, 50),
      ("Esquina Superior Derecha", screen_w - 100, 50),
      ("Esquina Inferior Derecha", screen_w - 100, screen_h - 100),
      ("Esquina Inferior Izquierda", 50, screen_h - 100),
  ]

  calibration_data = {"x_min": 0, "x_max": 640, "y_min": 0, "y_max": 480}
  captured_points = []

  print(
      "Iniciando calibracion de esquinas. Apunta con el fibron y presiona ESPACIO"
      " en cada punto."
  )

  for name, cx, cy in corners:
    point_captured = False
    last_x, last_y = 0, 0

    while not point_captured:
      ret, frame = cap.read()
      if not ret:
        break
      frame = cv2.flip(frame, 1)
      h, w, _ = frame.shape

      # Crear una pantalla negra simulando el guide o mostrar la camara con la instruccion
      display_frame = frame.copy()

      # Dibujar texto de instruccion
      cv2.putText(
          display_frame,
          f"Manten el fibron en: {name}",
          (30, 50),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.7,
          (0, 255, 0),
          2,
      )
      cv2.putText(
          display_frame,
          "Presiona ESPACIO para capturar",
          (30, 90),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.6,
          (255, 255, 255),
          2,
      )

      # Detectar color verde actual (o usar valores por defecto/cargados)
      hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
      # Rango verde estandar o predeterminado
      lower_green = np.array([35, 100, 100])
      upper_green = np.array([85, 255, 255])
      mask = cv2.inRange(hsv, lower_green, upper_green)
      contours, _ = cv2.findContours(
          mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
      )

      if contours:
        c = max(contours, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        if radius > 10:
          cv2.circle(
              display_frame, (int(x), int(y)), int(radius), (0, 0, 255), 2
          )
          last_x, last_y = x, y

      cv2.imshow("Calibracion de Pantalla", display_frame)

      key = cv2.waitKey(1) & 0xFF
      if key == ord(" "):  # Presionar Barra Espaciadora para guardar el punto
        if last_x > 0 and last_y > 0:
          captured_points.append((last_x, last_y))
          print(f"Punto {name} capturado en camara: {last_x}, {last_y}")
          point_captured = True

  cv2.destroyWindow("Calibracion de Pantalla")

  if len(captured_points) == 4:
    # Guardar los extremos obtenidos por la camara
    calibration_data["x_min"] = min(
        captured_points[0][0], captured_points[3][0]
    )
    calibration_data["x_max"] = max(
        captured_points[1][0], captured_points[2][0]
    )
    calibration_data["y_min"] = min(
        captured_points[0][1], captured_points[1][1]
    )
    calibration_data["y_max"] = max(
        captured_points[2][1], captured_points[3][1]
    )
    save_config(calibration_data)
    print("¡Calibración de pantalla guardada con éxito!")


def main():
  cap = cv2.VideoCapture(0)
  cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
  cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

  screen_width, screen_height = pyautogui.size()

  # Si se pasa un argumento '--calibrate', ejecuta la calibración de esquinas
  if len(sys.argv) > 1 and sys.argv[1] == "--calibrate":
    run_screen_calibration(cap)
    return

  # Cargar configuracion previa si existe
  config = load_config()
  x_min = config["x_min"] if config else 50
  x_max = config["x_max"] if config else 590
  y_min = config["y_min"] if config else 50
  y_max = config["y_max"] if config else 430

  cv2.namedWindow("Calibrador de Color")
  cv2.createTrackbar("H Min", "Calibrador de Color", 35, 179, nothing)
  cv2.createTrackbar("S Min", "Calibrador de Color", 100, 255, nothing)
  cv2.createTrackbar("V Min", "Calibrador de Color", 100, 255, nothing)
  cv2.createTrackbar("H Max", "Calibrador de Color", 85, 179, nothing)
  cv2.createTrackbar("S Max", "Calibrador de Color", 255, 255, nothing)
  cv2.createTrackbar("V Max", "Calibrador de Color", 255, 255, nothing)

  prev_x, prev_y = 0, 0
  smooth_factor = 5

  while True:
    ret, frame = cap.read()
    if not ret:
      break

    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    h_min = cv2.getTrackbarPos("H Min", "Calibrador de Color")
    s_min = cv2.getTrackbarPos("S Min", "Calibrador de Color")
    v_min = cv2.getTrackbarPos("V Min", "Calibrador de Color")
    h_max = cv2.getTrackbarPos("H Max", "Calibrador de Color")
    s_max = cv2.getTrackbarPos("S Max", "Calibrador de Color")
    v_max = cv2.getTrackbarPos("V Max", "Calibrador de Color")

    lower_color = np.array([h_min, s_min, v_min])
    upper_color = np.array([h_max, s_max, v_max])

    mask = cv2.inRange(hsv, lower_color, upper_color)
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if contours:
      c = max(contours, key=cv2.contourArea)
      ((x, y), radius) = cv2.minEnclosingCircle(c)

      if radius > 15:
        cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)

        # Mapeo preciso usando los límites calibrados
        target_x = np.interp(x, (x_min, x_max), (0, screen_width))
        target_y = np.interp(y, (y_min, y_max), (0, screen_height))

        current_x = prev_x + (target_x - prev_x) / smooth_factor
        current_y = prev_y + (target_y - prev_y) / smooth_factor

        pyautogui.moveTo(current_x, current_y)
        prev_x, prev_y = current_x, current_y

    cv2.imshow("Camara Tracking", frame)
    cv2.imshow("Mascara", mask)

    if cv2.waitKey(1) & 0xFF == ord("q"):
      break

  cap.release()
  cv2.destroyAllWindows()


if __name__ == "__main__":
  main()