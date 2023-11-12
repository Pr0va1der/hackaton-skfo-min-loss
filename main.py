import re

from PIL import Image, ImageDraw
from imageai.Detection import ObjectDetection
import os
import cv2
import json

from shapely.geometry import Polygon, box, Point
from tkinter import Tk, filedialog


def choose_file():
    root = Tk()
    root.withdraw()  # Скрываем основное окно

    file_path = filedialog.askopenfilename(title="Выберите файл")

    return file_path


def calculate_intersection_percentage(boxes, danger_zones):
    result_list = []

    for box_coords in boxes:
        box_polygon = box(*box_coords)
        min_distance = float('inf')  # Инициализируем минимальное расстояние как бесконечность
        nearest_zone_polygon = None

        for zone_id, zone_coords in danger_zones.items():
            # Преобразуем координаты опасной зоны в объект Polygon
            danger_zone_polygon = Polygon(zone_coords)

            # Находим центр опасной зоны
            zone_center = danger_zone_polygon.centroid.xy
            zone_center = zone_center[0][0], zone_center[1][0]

            # Находим расстояние от центра опасной зоны до центра бокса
            distance = box_polygon.centroid.distance(Point(zone_center))

            # Если расстояние меньше текущего минимального, обновляем значения
            if distance < min_distance:
                min_distance = distance
                nearest_zone_polygon = danger_zone_polygon

        # Пересекаются ли бокс и ближайшая опасная зона
        intersection = box_polygon.intersection(nearest_zone_polygon)

        # Проверяем процент пересечения
        intersection_area = intersection.area
        box_area = box_polygon.area

        percentage_intersection = (intersection_area / box_area) * 100

        result_list.append(percentage_intersection)
    return result_list


def find_people(path):
    exec_path = os.getcwd()
    detector = ObjectDetection()

    detector.setModelTypeAsYOLOv3()
    detector.setModelPath(os.path.join(exec_path, "yolov3.pt"))
    detector.loadModel()

    detections = detector.detectObjectsFromImage(
        input_image=os.path.join(exec_path, path),
        output_image_path=os.path.join(exec_path, "new_objects.jpg"),
        minimum_percentage_probability=10,
        display_percentage_probability=False,
        display_object_name=False
    )

    # print(detections)
    if not detections:
        print("No human on photo")
        image = Image.open(path)
        image.save("new_objects.jpg")
    # Открываем изображение для рисования
    image = Image.open(os.path.join(exec_path, "new_objects.jpg"))
    draw = ImageDraw.Draw(image)

    cordinates = []

    for detection in detections:
        if detection['name'] == "person":
            box = detection["box_points"]
            cordinates.append(box)
            draw.rectangle(box, outline="red", width=2)

    image.save("new_objects.jpg")

    return cordinates


def find_danger(path):
    camera_name = re.search(r'(.+)-\d+$', path.split("/")[-1].split(".")[0]).group(1)
    cords_data = None
    with open(f"danger/danger_{camera_name}.txt") as fp:
        cords_data = json.load(fp)
        fp.close()
    return cords_data


def main():
    path = choose_file()
    box_cords = find_people(path)
    danger_cords = find_danger(path)
    result = calculate_intersection_percentage(box_cords, danger_cords)
    is_dangerous = False

    for element in result:
        if element > 15:
            print(f"{True}, {element}")
        else:
            print(f"{False}, {element}")
    image = Image.open("new_objects.jpg")
    draw = ImageDraw.Draw(image)
    dict_of_tuples = {key: list(map(tuple, value)) for key, value in danger_cords.items()}
    for zone_id, zone_coords in dict_of_tuples.items():
        draw.polygon(zone_coords, outline='blue', width=2)
    image.show()
    image.save('new_objects.jpg')


if name == 'main':
    main()