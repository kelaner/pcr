import cv2
import glob
import os
import re
import pyttsx3
import shutil
import numpy as np
import paddlehub as hub


class Config:
    def __init__(self):
        pass

    src = "./output/1/"
    root_dir = "./output/temp/"
    qr_color = []
    color_dist = {
        '红码': {'Lower': np.array([0, 60, 60]), 'Upper': np.array([6, 255, 255])},
        '绿码': {'Lower': np.array([35, 43, 35]), 'Upper': np.array([90, 255, 255])},
        '黄码': {'Lower': np.array([26, 43, 46]), 'Upper': np.array([34, 255, 255])},
    }
    engine = pyttsx3.init()


def get_voice():
    Config.engine.setProperty('rate', 150)  # 设置语速
    Config.engine.setProperty('volume', 1.0)  # 设置音量
    voices = Config.engine.getProperty('voices')
    Config.engine.setProperty('voice', voices[0].id)


def change_temp():
    for i in os.listdir(Config.root_dir):
        full_path = os.path.join(Config.root_dir, i)
        aim_dir = "./output/1/"
        if not os.path.exists(aim_dir):
            os.mkdir(aim_dir)
        shutil.move(full_path, aim_dir)
        break


def clean_temp():
    for i in os.listdir(Config.src):
        path = os.path.join(Config.src, i)
        os.remove(path)


def read_path(file_path):
    for filename in os.listdir(file_path):
        img = cv2.imread(file_path + filename, 1)
        qr = img[450:650, 150:350]

        # 选取区域展示
        # img = img[:, :, [2, 1, 0]]
        # plt.subplot(1, 2, 1)
        # plt.imshow(img)
        # plt.axis('off')
        # plt.subplot(1, 2, 2)
        # plt.imshow(qr)
        # plt.axis('off')
        # plt.show()

        for i in Config.color_dist.keys():
            k = detect_color(qr, i)
            if k:
                Config.qr_color.append(i)


def detect_color(image, color):
    try:
        gs = cv2.GaussianBlur(image, (5, 5), 0)
        hsv = cv2.cvtColor(gs, cv2.COLOR_BGR2HSV)
        erode_hsv = cv2.erode(hsv, None, iterations=2)
        range_hsv = cv2.inRange(erode_hsv, Config.color_dist[color]['Lower'], Config.color_dist[color]['Upper'])
        contours = cv2.findContours(range_hsv.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        if len(contours) > 0:
            return True
        else:
            return False
    except:
        return None


def get_info():
    try:
        image_list = [cv2.imread(image_path) for image_path in glob.glob(f"{Config.src}*.jpg")]
        print(type(image_list[0]))
        if os.path.exists("./demo_result/"):
            for i in os.listdir("./demo_result/"):
                path = os.path.join("./demo_result/", i)
                os.remove(path)

        # 文字识别
        results = hub.Module(name="chinese_ocr_db_crnn_mobile").recognize_text(
            images=image_list,
            use_gpu=False, output_dir='demo_result',
            visualization=True, box_thresh=0.5, text_thresh=0.5)
    except:
        pass

    try:
        if not os.path.exists("demo_result.csv"):
            with open('demo_result.csv', 'w', encoding='utf-8-sig') as f:
                f.write('姓名,时间,检测日期,场所,健康码状态,24h,48h,72h,6天内,7天内\n')

        # 表格填充
        with open('demo_result.csv', 'a+', encoding='utf-8-sig') as f:
            name = re.compile(r'[\u4e00-\u9fa5]{2,4}（[\u4e00-\u9fa5]{2}）')
            time = re.compile(r'[0-9]{2}:[0-9]{2}:[0-9]{2}')
            dates = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}')
            place = re.compile(r'[\u4e00-\u9fa5]{4}：[\u4e00-\u9fa5]{2,}')
            for result in results:
                data = [i['text'] + "," if (
                        name.match(i['text'])
                        or time.match(i['text'])
                        or dates.search(i['text'])
                        or place.match(i['text'])) else ''
                        for i in result['data']]
                date = data.copy()
                for i in date:
                    if i == '':
                        data.remove(i)
                for i in range(len(data[0])):
                    if data[0][i] == '（':
                        data[0] = data[0][:i]
                        data[0] += ','
                        break
                # print(data)
                data[2] = data[2][5:15]
                data[2] += ','
                data[3] = data[3][5:]
                k = results.index(result)

                data.append(Config.qr_color[k] + ',')
                # print(data)
                f.write(''.join(data) + "\n")
                print(Config.qr_color[k])
                Config.engine.say(Config.qr_color[k])
                Config.engine.runAndWait()
    except:
        pass


if __name__ == '__main__':
    clean_temp()
    get_voice()
    # while True:
    change_temp()
    read_path(Config.src)
    get_info()
    clean_temp()