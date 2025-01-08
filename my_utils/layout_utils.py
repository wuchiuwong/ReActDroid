import os.path

from Levenshtein import distance
import re
import cv2
import numpy as np
from my_utils.str_utils import *


def is_bound_same(b1: list, b2: list):
    for i in range(len(b1)):
        for j in range(len(b1[i])):
            if b1[i][j] != b2[i][j]:
                return False
    return True


def convert_4_bound(in_bound: list):
    return [in_bound[0], in_bound[2]]


def is_b1_in_b2(b1: list, b2: list):
    if len(b1) == 4:
        b1 = convert_4_bound(b1)
    if len(b2) == 4:
        b2 = convert_4_bound(b2)
    return b2[0][0] <= b1[0][0] and b2[1][0] >= b1[1][0] and b2[0][1] <= b1[0][1] and b2[1][1] >= b1[1][1]


def get_bound_center(b: list):
    if len(b) == 4:
        b = convert_4_bound(b)
    b1_x = (b[0][0] + b[1][0]) / 2
    b1_y = (b[0][1] + b[1][1]) / 2
    return (b1_x, b1_y)


def is_b1_center_in_b2(b1: list, b2: list):
    (b1_x, b1_y) = get_bound_center(b1)
    if len(b2) == 4:
        b2 = convert_4_bound(b2)
    return b2[0][0] <= b1_x and b2[1][0] >= b1_x and b2[0][1] <= b1_y and b2[1][1] >= b1_y


def is_point_in_bound(point, bound):
    return point[0] > bound[0][0] and point[0] < bound[1][0] and point[1] > bound[0][1] and point[1] < bound[1][1]


def is_bound_intersect_old(b1: list, b2: list):
    flag1 = is_point_in_bound(b1[0], b2) or is_point_in_bound(b1[1], b2)
    if flag1:
        return True
    p1 = [b1[1][0], b1[0][1]]
    p2 = [b1[0][0], b1[1][1]]
    flag2 = is_point_in_bound(p1, b2) or is_point_in_bound(p2, b2)
    if flag2:
        return True
    c1 = get_bound_center(b1)
    if is_point_in_bound(c1, b2):
        return True
    c2 = get_bound_center(b2)
    if is_point_in_bound(c2, b1):
        return True
    return False


def is_bound_intersect(b1: list, b2: list):
    points1 = [b1[0], [b1[1][0], b1[0][1]], [b1[0][0], b1[1][1]], b1[1]]
    for point in points1:
        if is_point_in_bound(point, b2):
            return True
    points2 = [b2[0], [b2[1][0], b2[0][1]], [b2[0][0], b2[1][1]], b2[1]]
    for point in points2:
        if is_point_in_bound(point, b1):
            return True
    return False


def get_distance(center1, center2, y_scale=0.5, right_punish=1.5, below_punish=1.5):
    if center1[0] >= center2[0]:
        x_dis = center1[0] - center2[0]
    else:
        x_dis = (center1[0] - center2[0]) * right_punish
    if center1[1] >= center2[1]:
        y_dis = center1[1] - center2[1]
    else:
        y_dis = (center1[1] - center2[1]) * below_punish
    return x_dis * x_dis + y_dis * y_dis * y_scale


def get_bound_distance(bound1: list, bound2: list):
    center1 = get_bound_center(bound1)
    center2 = get_bound_center(bound2)
    return get_distance(center1, center2, y_scale=1, right_punish=1, below_punish=1)


def get_bound_lou(bound1: list, bound2: list):
    left_column_max = max(bound1[0][0], bound2[0][0])
    right_column_min = min(bound1[1][0], bound2[1][0])
    up_row_max = max(bound1[0][1], bound2[0][1])
    down_row_min = min(bound1[1][1], bound2[1][1])
    if left_column_max >= right_column_min or down_row_min <= up_row_max:
        return 0
    else:
        S1 = (bound1[1][0] - bound1[0][0]) * (bound1[1][1] - bound1[0][1])
        S2 = (bound2[1][0] - bound2[0][0]) * (bound2[1][1] - bound2[0][1])
        S_cross = (down_row_min - up_row_max) * (right_column_min - left_column_max)
        return S_cross / (S1 + S2 - S_cross)


def get_view_refer_name(view_info):
    # Priority 1: for EditText, return its resource id for name, or neighbor text
    if "edittext" in view_info["class"].lower():
        return get_edittext_name(view_info)

    # Priority 2: for checkbox, radiobutton, switch, return its neighbor text for name
    if "checkbox" in view_info["class"].lower() or "radiobutton" in view_info["class"].lower() \
            or "switch" in view_info["class"].lower():
        return get_checktext_name(view_info)

    # Priority 3: case layout, text from child
    if "layout" in view_info["class"].lower() or "spinner" in view_info["class"].lower():
        return get_layout_name(view_info)

    return get_general_name(view_info)


def get_edittext_name(view_info):
    # add 1115: use content_description
    if isinstance(view_info["content_description"], str) and len(view_info["content_description"]) > 1:
        return {"name": only_ascii_clip(view_info["content_description"]), "from": "content_description",
                "from_id": view_info["view_id"]}

    # EditText 1: for EditText, return its resource id for name, or neighbor text
    if isinstance(view_info["resource_id"], str) and len(view_info["resource_id"]) > 1:
        clean_id = clean_resource_id(view_info["resource_id"])
        keywords = ["email", "name", "pass", "time", "date"]
        has_keyword = False
        for keyword in keywords:
            if keyword in clean_id:
                has_keyword = True
                break
        has_sibling_text = len(view_info["sibling_text"]) > 0
        # use_flag1 = len(clean_id.split()) >= 2 and len(clean_id.split()) <= 3
        use_flag1 = len(clean_id.split()) >= 1 and len(clean_id.split()) <= 3
        use_flag2 = (not has_sibling_text) and (len(clean_id.split()) == 1 or len(clean_id.split()) >= 4)
        # print(clean_id, use_flag1, use_flag2)
        if (use_flag1 or use_flag2 or has_keyword) and clean_id != "none":
            return {"name": clean_id, "from": "resource_id", "from_id": view_info["view_id"]}

    # EditText 2: return not none sibling text
    if len(view_info["sibling_text"]) > 0:
        return {"name": view_info["sibling_text"], "from": "sibling_text", "from_id": view_info["sibling_text_id"]}

    # EditText 3: no idea what to return, return neighbor text
    if len(view_info["neighbor_text"]) > 0:
        return {"name": view_info["neighbor_text"], "from": "neighbor_text", "from_id": view_info["neighbor_text_id"]}
    elif isinstance(view_info["text"], str) and len(view_info["text"]) > 1:
        return {"name": only_ascii_clip(view_info["text"]), "from": "text", "from_id": view_info["view_id"]}
    else:
        return {"name": "none", "from": "unknown", "from_id": None}


def get_checktext_name(view_info):
    # checktext 1: for checkbox, radiobutton, switch, return its neighbor text for name
    if len(view_info["sibling_text"]) > 0:
        return {"name": view_info["sibling_text"], "from": "sibling_text", "from_id": view_info["sibling_text_id"]}

    # checktext 2: no idea what to return, return neighbor text
    if len(view_info["neighbor_text"]) > 0:
        return {"name": view_info["neighbor_text"], "from": "neighbor_text", "from_id": view_info["neighbor_text_id"]}
    else:
        return {"name": "none", "from": "unknown", "from_id": None}


def get_layout_name(view_info):
    # add 1115: use content_description
    if isinstance(view_info["content_description"], str) and len(view_info["content_description"]) > 1:
        process_cont = only_ascii_clip(view_info["content_description"])
        if "Navigate up" in process_cont:
            process_cont = "Navigate up"
        return {"name": process_cont, "from": "content_description", "from_id": view_info["view_id"]}

    # layout 1: case layout, text from child
    if len(view_info["warp_text"]) > 0:
        return {"name": view_info["warp_text"], "from": "warp_text", "from_id": view_info["warp_text_id"]}

    # layout 2: case layout, text from child
    if isinstance(view_info["resource_id"], str) and len(view_info["resource_id"]) > 1:
        clean_id = clean_resource_id(view_info["resource_id"])
        if len(clean_id.split(" ")) >= 1 and len(clean_id.split(" ")) <= 4:
            # return view_info["resource_id"].lower()
            return {"name": clean_id, "from": "resource_id", "from_id": view_info["view_id"]}

    # layout 3: no idea what to return, return neighbor text
    if len(view_info["neighbor_text"]) > 0:
        return {"name": view_info["neighbor_text"], "from": "neighbor_text", "from_id": view_info["neighbor_text_id"]}
    else:
        return {"name": "none", "from": "unknown", "from_id": None}


def get_general_name(view_info):
    # Priority 1: text from self
    if isinstance(view_info["text"], str) and len(view_info["text"]) > 1:
        return {"name": only_ascii_clip(view_info["text"]), "from": "text", "from_id": view_info["view_id"]}

    if isinstance(view_info["content_description"], str) and len(view_info["content_description"]) > 1:
        if view_info["content_description"] == "Navigate up" and view_info.get("sibling_text", "") == 'Add new plant':
            return {"name": only_ascii_clip(view_info["sibling_text"]), "from": "sibling_text",
                    "from_id": view_info["sibling_text_id"]}
        return {"name": only_ascii_clip(view_info["content_description"]), "from": "content_description",
                "from_id": view_info["view_id"]}

    # Priority 2: view's resource id longer than 2 words, it may be a meaningful identifier
    if isinstance(view_info["resource_id"], str) and len(view_info["resource_id"]) > 1:
        clean_id = clean_resource_id(view_info["resource_id"])
        if view_info["resource_id"].split("/")[-1] == "fab":
            return {"name": "Next", "from": "resource_id", "from_id": view_info["view_id"]}
        if len(clean_id.split(" ")) >= 1 and len(clean_id.split(" ")) <= 4:
            # return view_info["resource_id"].lower()
            return {"name": clean_id, "from": "resource_id", "from_id": view_info["view_id"]}

    # Priority 3: return not none sibling text
    if len(view_info["sibling_text"]) > 0:
        return {"name": view_info["sibling_text"], "from": "sibling_text", "from_id": view_info["sibling_text_id"]}

    # Priority 4: return only one child_text
    if len(view_info["warp_text"]) > 0:
        return {"name": view_info["warp_text"], "from": "warp_text", "from_id": view_info["warp_text_id"]}

    # Priority 5: no idea what to return, return neighbor text
    # to avoid noise, drop such case in train set
    if len(view_info["neighbor_text"]) > 0:
        return {"name": view_info["neighbor_text"], "from": "neighbor_text", "from_id": view_info["neighbor_text_id"]}
    else:
        return {"name": "none", "from": "unknown", "from_id": None}


def get_gray_area(img_path, div_x=18, div_y=32, gray_thres=130):
    if not os.path.exists(img_path):
        return [[0 for _ in range(1080 // div_x)] for _ in range(1920 // div_y)]
    img = cv2.imread(img_path)
    if not isinstance(img, np.ndarray):
        return [[0 for _ in range(1080 // div_x)] for _ in range(1920 // div_y)]
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    y_shape = gray_img.shape[0]
    x_shape = gray_img.shape[1]
    gray_img_reshape = gray_img.reshape(y_shape * x_shape)
    global_bc = np.bincount(gray_img_reshape)
    global_mode = np.argmax(global_bc)
    if global_mode <= gray_thres:
        return [[0 for _ in range(x_shape // div_x)] for _ in range(y_shape // div_y)]
    mode_stat = []
    for y in range(y_shape // div_y):
        mode_stat.append([])
        for x in range(x_shape // div_x):
            area = gray_img[y * div_y: (y + 1) * div_y, x * div_x: (x + 1) * div_x].reshape(div_y * div_x)
            bc = np.bincount(area)
            mode = np.argmax(bc)
            mode_stat[y].append(mode)
    gray_area1 = gray_area_type1(mode_stat)
    if len(gray_area1) > 0:
        return gray_area1
    gray_area2 = gray_area_type2(mode_stat)
    if len(gray_area2) > 0:
        return gray_area2
    return [[0 for _ in range(x_shape // div_x)] for _ in range(y_shape // div_y)]


def gray_area_type1(mode_stat: list, gray_thres=130):
    # type 1: gray column
    is_gray_column = []
    for x in range(len(mode_stat[0])):
        grey_count = 0
        for y in range(len(mode_stat)):
            if mode_stat[y][x] <= gray_thres:
                grey_count += 1
        if grey_count / len(mode_stat) >= 0.9:
            is_gray_column.append(1)
        else:
            is_gray_column.append(0)
    right_gray_column_stat = 0
    for i in range(1, len(is_gray_column)):
        if is_gray_column[-i] == 1:
            right_gray_column_stat += 1
        else:
            break
    if right_gray_column_stat >= 0.25 * len(is_gray_column) and right_gray_column_stat <= 0.6 * len(is_gray_column):
        return [is_gray_column.copy() for _ in range(len(mode_stat))]
    else:
        return []


def gray_area_type2(mode_stat: list, gray_thres=130):
    # type 2: gray row
    is_gray_row = []
    for y in range(len(mode_stat)):
        grey_count = 0
        for x in range(len(mode_stat[0])):
            if mode_stat[y][x] <= gray_thres:
                grey_count += 1
        if grey_count / len(mode_stat[0]) >= 0.9:
            is_gray_row.append(1)
        else:
            is_gray_row.append(0)
    top_gray_row_stat = 0
    for i in range(len(is_gray_row)):
        if is_gray_row[i] == 1:
            top_gray_row_stat += 1
        else:
            break
    bottom_gray_row_stat = 0
    for i in range(1, len(is_gray_row)):
        if is_gray_row[-i] == 1:
            bottom_gray_row_stat += 1
        else:
            break
    flag1 = (top_gray_row_stat + bottom_gray_row_stat) >= 0.5 * len(is_gray_row)
    flag2 = (top_gray_row_stat + bottom_gray_row_stat) <= 0.8 * len(is_gray_row)
    flag3 = top_gray_row_stat >= 0.2 * len(is_gray_row) and bottom_gray_row_stat >= 0.2 * len(is_gray_row)
    if flag1 and flag2 and flag3:
        return [[is_gray_row[i] for _ in range(len(mode_stat[0]))] for i in range(len(mode_stat))]
    else:
        return []


def is_in_gray_area(bound: list, gray_area: list, div_x=18, div_y=32):
    (b_x, b_y) = get_bound_center(bound)
    y = int(b_y / div_y)
    x = int(b_x / div_x)
    return gray_area[y][x]


def get_activity_name(ori_activity: str):
    exclude_words = ["activity", "fragment", "acti", "frag"]
    activity = ori_activity.split(".")[-1]
    activity = re.sub(r'([a-z])([A-Z])', r'\1 \2', activity).lower()
    activity = re.sub(r"[^a-z0-9]", " ", activity)
    activity = re.sub(r"\s+", " ", activity).strip()
    activity_tokens = [t for t in activity.split(" ") if t not in exclude_words]
    return " ".join(activity_tokens)


def flit_by_name(refer_name: str):
    exclude_words = ["http://", "https://", "version", "github"]
    for exclude_word in exclude_words:
        if exclude_word in refer_name.lower():
            return True
    return False


def exclude_by_name(view_name: str):
    exclude_whole = ["prev", "deckpicker add", "next month", "plant date", "medium", "open navigation drawer"]
    if view_name.lower() in exclude_whole:
        return True

    exclude_words = ["language", "github", "http", "opoc filesystem item image", "consumption", "default car",
                     "authentication", "totp", "login credentials", " url", "opensourced ", " sdk", "uiiiii", "badge"]
    for exclude_word in exclude_words:
        if exclude_word in view_name.lower():
            return True
    return False


if __name__ == '__main__':
    get_gray_area("../Data/Temp/cur_screen.png")
