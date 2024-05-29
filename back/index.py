import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk
import svgwrite
from svgwrite import Drawing
from PIL import Image, ImageTk
import numpy as np
import binascii

message = 'Я вас любил: любовь ещё, быть может, В душе моей угасла не совсем; Но пусть она вас больше не тревожит;Я не хочу печалить вас ничем.Я вас любил безмолвно, безнадежно,То робостью, то ревностью томим;Я вас любил так искренно, так нежно, Как дай вам Бог любимой быть другим.'

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

def text_to_bits(text, encoding='utf-16', errors='surrogatepass'):
    bits = bin(int(binascii.hexlify(text.encode(encoding, errors)), 16))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))

def text_from_bits(bits, encoding='utf-16', errors='surrogatepass'):
    n = int(bits, 2)
    return int2bytes(n).decode(encoding, errors)

def int2bytes(i):
    hex_string = '%x' % i
    n = len(hex_string)
    return binascii.unhexlify(hex_string.zfill(n + (n & 1)))

def create_polyline(line):
    """Создает ломаную линию из прямой линии.

    Args:
        line: элемент прямой линии в дереве SVG.

    Returns:
        Элемент ломаной линии в дереве SVG.
    """

    x1, y1, x2, y2 = line.attrib["x1"], line.attrib["y1"], line.attrib["x2"], line.attrib["y2"]
    num_segments = max([int(x1), int(y1), int(x2), int(y2)]) * 35  # Количество сегментов ломаной линии

    polyline = ET.Element("polyline")

    for i in range(num_segments + 1):
        if "points" not in polyline.attrib:
            polyline.attrib["points"] = f"{(int(int(x1) + (i / num_segments) * (int(x2) - int(x1))))}," +  f"{(int(int(y1) + (i / num_segments) * (int(y2) - int(y1))))} "
    
        else:
            polyline.attrib["points"] += f"{(int(int(x1) + (i / num_segments) * (int(x2) - int(x1))))}," + f"{(int(int(y1) + (i / num_segments) * (int(y2) - int(y1))))} "

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
    bitsOld = [int(bit) for bit in bin(int.from_bytes(message.encode(), "big"))[2:]]
    bits = text_to_bits(message)
    print(bits)

    # Встраиваем биты в наименее значимые биты координат
    points = polyline.attrib["points"].split()
    newPoints = ''
    for i, bit in enumerate(bits):
        point = points[i].split(",")
        point[0] = str(int(point[0]) + int(bit))
        newPoints += f'{point[0]},{point[1]} '
    polyline.attrib["points"] = newPoints
    return polyline

def decodeMessage(polygons, messageLength):
    """Встраивает сообщение в координаты промежуточных узлов ломаной.

    Args:
        svg: SVG.

    Returns:
        Раскодированное сообщение.
    """
    lsbMessage = ''
    bitsLength = 16 * messageLength
    bitsCount = 0
    for polygon in polygons:
        points = polygon.attrib["points"].split()
        for point in points:
            pointSplited = point.split(',')
            byte = [int(bit) for bit in bin(int.from_bytes(pointSplited[0].encode(), "big"))[2:]]
            lsb = byte[len(byte) - 1]
            lsbMessage += str(lsb)
            bitsCount += 1
            if(bitsCount == bitsLength):
                break
        if(bitsCount == bitsLength):
                break
    decodedMessage = text_from_bits(lsbMessage)
    return decodedMessage


# # Создать окно tkinter
# root = tk.Tk()

# # Создать экземпляр кастомного виджета отображения SVG
# svg_canvas = SvgCanvas(root)
# svg_canvas.pack()

# # Загрузить SVG-изображение
# svg_path = "table.png"
# svg_canvas.load_svg(svg_path)

# # Запустить главное окно
# root.mainloop()

# Загружаем SVG-файл
tree = ET.parse("svgviewer-output.svg")
print(tree)
svg = tree.getroot()

# Находим все прямые линии в SVG 
lines = svg.findall("line")
# Преобразуем прямые линии в ломаные и внедряем сообщение
colAdded = False
for line in lines:
    polyline = create_polyline(line)
    #embed_message(polyline, "нигер")
    line.attrib.pop('x1')
    line.attrib.pop('y1')
    line.attrib.pop('x2')
    line.attrib.pop('y2')
    line.tag = 'polygon'
    if (not colAdded):
        line.attrib['col'] = len(message)
        colAdded = not colAdded
    newPolyline = embed_message(polyline, message)
    line.attrib['points'] = polyline.attrib['points']
    # Надо в svg как-то запихнуть все polyline  0,0 -> 00000000 00110100 00100000
    # разбиваем количество символов в сообщении на количество линий. Получаем примерно одинаковые по длине подсообщения и запихиваем их в координаты полигона

polygons = svg.findall("polygon")
# + 1, потому что иначе декодирование не работает (хз почему) УДАЛИТЬ ОБЯЗАТЕЛЬНО!!!
decodedMessage = decodeMessage(polygons, polygons[0].attrib.pop('col') + 1)
# Сохраняем обновленный SVG
tree.write("output.svg")