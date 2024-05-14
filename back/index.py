import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk
import svgwrite
from svgwrite import Drawing
from PIL import Image, ImageTk
import numpy as np

class SvgCanvas(tk.Canvas):
    def __init__(self, master, *kwargs):
        super().__init__(master, *kwargs)
        self.svg_image = None

    def load_svg(self, svg_path):
        # Загрузить SVG-изображение из файла
        image = Image.open(svg_path)
        self.svg_image = ImageTk.PhotoImage(image)

        # Отобразить SVG-изображение в виджете
        self.create_image(0, 0, image=self.svg_image, anchor=tk.NW)


def create_polyline(line):
    """Создает ломаную линию из прямой линии.

    Args:
        line: элемент прямой линии в дереве SVG.

    Returns:
        Элемент ломаной линии в дереве SVG.
    """

    x1, y1, x2, y2 = line.attrib["x1"], line.attrib["y1"], line.attrib["x2"], line.attrib["y2"]
    num_segments = 5  # Количество сегментов ломаной линии

    polyline = ET.Element("polyline")

    for i in range(num_segments + 1):
        if "points" not in polyline.attrib:
            polyline.attrib["points"] = " ".join([
            f"{(int(int(x1) + (i / num_segments) * (int(x2) - int(x1))))}",
            f"{(int(int(y1) + (i / num_segments) * (int(y2) - int(y1))))}"
        ]) + " "
        else:
            polyline.attrib["points"] += " ".join([
                f"{(int(int(x1) + (i / num_segments) * (int(x2) - int(x1))))}",
                f"{(int(int(y1) + (i / num_segments) * (int(y2) - int(y1))))}"
            ]) + " "

    polyline.attrib["points"] = polyline.attrib["points"].strip()

    return polyline


def embed_message(polyline, message):
    """Встраивает сообщение в координаты промежуточных узлов ломаной.

    Args:
        polyline: элемент ломаной линии в дереве SVG.
        message: сообщение для встраивания.

    Returns:
        Элемент ломаной линии в дереве SVG с внедренным сообщением.
    """

    # Преобразуем сообщение в биты
    bits = [int(bit) for bit in bin(int.from_bytes(message.encode(), "big"))[2:]]
    print(bits)

    # Встраиваем биты в наименее значимые биты координат
    points = polyline.attrib["points"].split()
    for i, bit in enumerate(bits):
        point = points[i].split(",")
        point[0] = str(int(point[0]) + bit)
        polyline.attrib["points"] = " ".join(points)

    return polyline


# Создать окно tkinter
root = tk.Tk()

# Создать экземпляр кастомного виджета отображения SVG
svg_canvas = SvgCanvas(root)
svg_canvas.pack()

# Загрузить SVG-изображение
svg_path = "table.png"
svg_canvas.load_svg(svg_path)

# Запустить главное окно
root.mainloop()

# Загружаем SVG-файл
tree = ET.parse("output.svg")
print(tree)
svg = tree.getroot()

# Находим все прямые линии в SVG 
lines = svg.findall("line")

# Преобразуем прямые линии в ломаные и внедряем сообщение
for line in lines:
    polyline = create_polyline(line)
    #embed_message(polyline, "нигер")
    svg.remove(line)
    svg.insert(line.index, polyline)
    svg.replace(line, polyline)

# Сохраняем обновленный SVG
tree.write("output.svg")