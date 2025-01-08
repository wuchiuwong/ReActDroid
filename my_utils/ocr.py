import logging
from PIL import Image
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from paddleocr import PaddleOCR, draw_ocr
import json
from tqdm import tqdm


class OCR:
    def __init__(self):
        self.ocr_model = PaddleOCR(use_angle_cls=True, lang="en", show_log=False, use_gpu=True)

    def perform_on_dir(self, img_dir):
        all_res = {}
        for f in tqdm(os.listdir(img_dir)):
            if ".png" not in f:
                continue
            ocr_res = self.perform_ocr(img_dir + "/" + f)
            all_res.setdefault(f, ocr_res)
        save_path = img_dir + "/ocr_res.json"
        save_file = open(save_path, "w")
        json.dump(all_res, save_file, indent=4)

    def perform_ocr(self, img_path: str):
        if not os.path.exists(img_path):
            return []
        img_name = img_path.split("/")[-1]
        img_dir = img_path.replace(img_name, "/")
        if os.path.exists(img_dir + "ocr_res.json"):
            ocr_res = json.load(open(img_dir + "ocr_res.json", "r"))
            if img_name in ocr_res.keys():
                return ocr_res[img_name]
        result = self.ocr_model.ocr(img_path, cls=True)
        res = []
        if len(result) == 1:
            for line in result[0]:
                cur_item = dict()
                cur_bound = line[0]
                if len(cur_bound) == 4:
                    cur_item.setdefault("bound", [cur_bound[0], cur_bound[2]])
                else:
                    cur_item.setdefault("bound", cur_bound)
                cur_item.setdefault("text", line[1][0])
                cur_item.setdefault("score", line[1][1])
                res.append(cur_item)
        else:
            for line in result:
                cur_item = dict()
                cur_bound = line[0]
                if len(cur_bound) == 4:
                    cur_item.setdefault("bound", [cur_bound[0], cur_bound[2]])
                else:
                    cur_item.setdefault("bound", cur_bound)
                cur_item.setdefault("text", line[1][0])
                cur_item.setdefault("score", line[1][1])
                res.append(cur_item)
        return res

    def perform_ocr_and_draw(self, img_path):
        result = self.ocr_model.ocr(img_path, cls=True)
        image = Image.open(img_path).convert('RGB')
        boxes = [line[0] for line in result[0]]
        txts = [line[1][0] for line in result[0]]
        scores = [line[1][1] for line in result[0]]
        im_show = draw_ocr(image, boxes, txts, scores)
        im_show = Image.fromarray(im_show)
        im_show.save('../temp/ocr.jpg')


if __name__ == '__main__':
    a = OCR()
    # a.perform_ocr_and_draw("../data/test/droidbot_res/Anki-Android_2.6/states/screen_2023-08-08_043736.png")

    # open("../Data/Temp/cur_screen.png")
    # a.perform_ocr("../Data/Temp/cur_screen.png")
    for dir_name in os.listdir("../Data/FaxRes/"):
        # if "." not in dir_name or ".py" in dir_name:
        #     continue
        if not dir_name.isdigit() or ".py" in dir_name:
            continue
        print("../Data/FaxRes/" + dir_name)
        a.perform_on_dir("../Data/FaxRes/" + dir_name)