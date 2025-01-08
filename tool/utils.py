import re
import cv2
import time
import numpy as np
import os


last_check = 0



# def check_is_confirm_button(view: dict, debug=False):
#     confirm_button = ["save", "add", "create", "done", "ok", "confirm", "sign", "next", "unlock", "setup", "search",
#                       "login"]
#     confirm_button = set(confirm_button)
#     confirm_words = ["log in"]
#     refer_name = view["refer_name"].lower()
#     view_class = view["class"]
#     refer_name_words = set(refer_name.split())
#     is_confirm_button = len(refer_name_words.intersection(confirm_button)) > 0 or refer_name in confirm_words
#     is_button = view_class[-8:].lower() == "textview" or (view_class[-6:].lower() in ["button", "layout"])
#     view_bounds = view["bounds"]
#     view_centerx = (view_bounds[0][0] + view_bounds[1][0]) / 2
#     view_centery = (view_bounds[0][1] + view_bounds[1][1]) / 2
#     if view_centerx < 250 and view_centery < 150:
#         return False
#     if debug:
#         print("refer_name:", refer_name)
#         print("refer_name_words:", refer_name_words)
#         print("intersection:", len(refer_name_words.intersection(confirm_button)))
#     return is_confirm_button and is_button

def clean_resource_id(resource_id: str):
    resource_id = re.sub(r'([a-z])([A-Z])', r'\1 \2', resource_id).lower()
    resource_id = re.sub("[^a-z]", " ", resource_id).strip()
    useless_words = ["edittext", "button", "none", "view", "textview", "action", "fab"]
    words = resource_id.strip().split(" ")
    use_word = []
    for word in words:
        word_char = set(word)
        # drop word that maybe abbreviation from edittext/button, like: edit, edt, ed, text...
        use_flag = True
        for useless_word in useless_words:
            inter_with_useless_word = word_char.intersection(set(useless_word))
            if len(word_char) <= len(inter_with_useless_word):
                use_flag = False
                break
        if use_flag:
            use_word.append(word)
    if len(use_word) == 0:
        return "none"
    else:
        return " ".join(use_word)

def check_crash():
    # print("checking crash")
    log_file = open("../Data/Temp/log/log_out.txt", "r", encoding="UTF-8", errors="ignore")
    log_lines = log_file.readlines()
    log_file.close()
    # for i in range(1,20):
    #     line = log_lines[-i]
    #     if len(line.strip()) > 0:
    #         print(line.strip())
    #         break
    for line in log_lines[-200:]:
        if re.match(r".*?AndroidRuntime: FATAL EXCEPTION: .*", line):
            print(line)
            return True
        # if re.match(r".*?AndroidRuntime: FATAL EXCEPTION: main.*", line):
        #     print(line)
        #     return True
        if re.match(r".*?getText\(\) = Unfortunately, .*? has stopped.*", line):
            print(line)
            return True
        if re.match(r".*?W DropBoxManagerService: Dropping: data_app_crash.*?", line):
            print(line)
            return True
        if re.match(r".*?UiObject: getText\(\) = .*? isn't responding\..*?", line):
            print(line)
            return True
    return False


def check_img_same(img_path1: str, img_path2: str):
    if not os.path.exists(img_path1) or not os.path.exists(img_path2):
        return True
    img1 = cv2.imread(img_path1)
    img2 = cv2.imread(img_path2)
    hash1 = pHash(img1)
    hash2 = pHash(img2)
    n3 = cmpHash(hash1, hash2)
    if n3 > 13:
        return False
    else:
        return True

def pHash(img):
    img = cv2.resize(img, (32, 32))  # , interpolation=cv2.INTER_CUBIC
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 将灰度图转为浮点型，再进行dct变换
    dct = cv2.dct(np.float32(gray))
    # opencv实现的掩码操作
    dct_roi = dct[0:8, 0:8]

    hash = []
    avreage = np.mean(dct_roi)
    for i in range(dct_roi.shape[0]):
        for j in range(dct_roi.shape[1]):
            if dct_roi[i, j] > avreage:
                hash.append(1)
            else:
                hash.append(0)
    return hash


def cmpHash(hash1, hash2):
    # Hash值对比
    # 算法中1和0顺序组合起来的即是图片的指纹hash。顺序不固定，但是比较的时候必须是相同的顺序。
    # 对比两幅图的指纹，计算汉明距离，即两个64位的hash值有多少是不一样的，不同的位数越小，图片越相似
    # 汉明距离：一组二进制数据变成另一组数据所需要的步骤，可以衡量两图的差异，汉明距离越小，则相似度越高。汉明距离为0，即两张图片完全一样
    n = 0
    # hash长度不同则返回-1代表传参出错
    if len(hash1) != len(hash2):
        return -1
    # 遍历判断
    for i in range(len(hash1)):
        # 不相等则n计数+1，n最终为相似度
        if hash1[i] != hash2[i]:
            n = n + 1
    return n

def get_input_content(edit_id: str, default_cont: str, default_input: str, input_cont: dict):
    for key, content in input_cont.items():
        if key in edit_id:
            return content
    if "all" in input_cont.keys():
        return input_cont["all"]
    if "name" in edit_id or "email" in edit_id:
        return "foo@bar.123"
    if default_cont.isdigit():
        return "1145141919810893"
    return default_input


# def get_input_content_old(edit_id: str, default_cont: str, app_pck: str, use_cont: str):
#     name_map, pass_map = get_account()
#     if "name" in edit_id or "email" in edit_id:
#         if app_pck in name_map.keys():
#             return name_map[app_pck]
#         else:
#             return "foo@bar.123"
#     if "password" in edit_id:
#         if app_pck in pass_map.keys():
#             return pass_map[app_pck]
#     if default_cont.isdigit():
#         return "1145141919810893"
#     return use_cont

def get_account():
    name_map = {"com.example.terin.asu_flashcardapp": "lu@gml.com", "com.fsck.k9.debug": "dingzhen1919810@outlook.com"}
    pass_map = {"com.example.terin.asu_flashcardapp": "12331986", "com.fsck.k9.debug": "zaq13edc"}
    return name_map, pass_map

def check_crash_strict(stack_trace: str, thres=3):
    global last_check
    tgt_trace = clean_trace_line(stack_trace.split("\n")[:thres])
    # print(tgt_trace)
    log_file = open("../Data/Temp/log/log_out.txt", "r", encoding="UTF-8", errors="ignore")
    # ori_log_lines = log_file.readlines()
    log_lines = []
    for line in log_file.readlines():
        if len(line.strip()) > 0:
            log_lines.append(line)
    log_file.close()
    check_begin = max(0, len(log_lines)-100)
    for line_idx in range(check_begin, len(log_lines) - thres):
        cur_block = log_lines[line_idx: line_idx + thres]
        cur_trace_str = clean_trace_line(cur_block)
        if cur_trace_str == tgt_trace:
            print("target crash has trigger!")
            print("".join(cur_block))
            return 2
        line = log_lines[line_idx]
        if re.match(r".*?AndroidRuntime: FATAL EXCEPTION: .*", line):
            print("find a crash but not target")
            print(line)
            return 1
        # if re.match(r".*?AndroidRuntime: FATAL EXCEPTION: main.*", line):
        #     print(line)
        #     return True
        if re.match(r".*?getText\(\) = Unfortunately, .*? has stopped.*", line):
            print("find a crash but not target")
            print(line)
            return 1
        if re.match(r".*?W DropBoxManagerService: Dropping: data_app_crash.*?", line):
            print("find a crash but not target")
            print(line)
            return 1
        if re.match(r".*?UiObject: getText\(\) = .*? isn't responding\..*?", line):
            print("find a crash but not target")
            print(line)
            return 1
    last_check = 1
    return 0


def clean_trace_line(lines):
    process_res = ""
    for line in lines:
        process_res += re.sub("\d+", "#", line).strip()
    process_res2 = re.sub("[^A-Za-z#.:$]", "", process_res)
    return process_res2

def check_is_confirm_button(view_key: str):
    if "[" not in view_key or "Input[" in view_key:
        return False
    refer_name = view_key.split("[")[1].split("]")[0].lower()
    # confirm_names = ["save", "add", "create", "done", "ok", "confirm", "sign", "next", "unlock", "setup", "search", "login"]
    # confirm_names = ["save", "add", "create", "done", "ok", "sign", "next", "unlock", "setup", "search", "login"]
    confirm_names = ["save", "add", "create", "done", "ok", "sign", "next", "unlock", "setup", "login"]
    confirm_names = set(confirm_names)
    confirm_words = ["log in"]
    refer_name_words = set(refer_name.split())
    is_confirm_button = len(refer_name_words.intersection(confirm_names)) > 0 or refer_name in confirm_words
    return is_confirm_button

def check_is_back(view_key: str):
    if "[" not in view_key or "Input[" in view_key:
        return False
    refer_name = view_key.split("[")[1].split("]")[0].lower()
    back_names = ["back", "cancel", "exit", "previous"]
    back_names = set(back_names)
    back_words = ["navigate up"]
    refer_name_words = set(refer_name.split())
    is_back_button = len(refer_name_words.intersection(back_names)) > 0 or refer_name in back_words
    return is_back_button


if __name__ == '__main__':
    # print(check_crash())
    # img1 = "MuMu20221124235303.png"
    # img2 = "MuMu20221124235317.png"
    # img1 = "../Data/Temp/cur_screen.png"
    # img2 = "MuMu20221124235442.png"
    # img1 = cv2.imread(img1)
    # img2 = cv2.imread(img2)
    # hash1 = pHash(img1)
    # hash2 = pHash(img2)
    # n3 = cmpHash(hash1, hash2)
    # print('感知哈希算法相似度pHash：', n3)
    # start_time = time.time()
    # for i in range(100):
    #     img_similarity(img1, img2)
    # print(time.time()-start_time)
    # for f in os.listdir("../Data/ReCDriod/traces/"):
    #     trace_lines = open("../Data/ReCDriod/traces/" + f, "r").readlines()
    #     if len(trace_lines) == 0:
    #         print("Empty:", f)
    #         continue
    #     first_line = trace_lines[0].strip()
    #     # if not first_line[:1].isdigit():
    #     #     print(f)
    #     if len(trace_lines) > 0:
    #         print(f)
    #         print(clean_trace_line(first_line))
    trace_cont = open("../Data/MyData/traces/15_SecUSo-privacy-friendly-food-tracker-55.txt", "r").read()
    check_crash_strict(trace_cont)