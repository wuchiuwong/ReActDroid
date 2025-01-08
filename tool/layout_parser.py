import json
import re
import os
from PIL import Image, ImageStat
from lxml import etree
from lxml.etree import Element, SubElement, ElementTree
import shutil
# from my_utils.ocr import OCR
from Levenshtein import distance
from my_utils.layout_utils import *
import pandas as pd
from my_utils.str_utils import process_xpath


# ocr_obj = OCR()


def parse_layout_appium(xml_path: str, quick=True):
    xml_source = open(xml_path, "r", encoding="UTF-8", errors="ignore").read()
    if "<hierarchy" not in xml_source:
        return {}
    full_activity_name = xml_path.split("/")[-1].split("_")[0]
    img_path = xml_path.replace(".xml", ".png")
    abs_img_path = img_path.replace("../", "D:/PycharmProjects/ReActReproduce/")
    activity_name = get_activity_name(full_activity_name)
    gray_area = get_gray_area(img_path)
    if quick:
        ocr_res = []
    else:
        # ocr_res = ocr_obj.perform_ocr(img_path)
        ocr_res = []
    id2view, id2child, clickable_bounds, all_texts, is_scrollable = get_basic_info(xml_source, ocr_res, gray_area)
    # print(clickable_bounds)
    if not_care_page(full_activity_name, id2view):
        return {}
    set_context_info(id2view, all_texts)
    clickable_views = get_clickable_views(id2view, clickable_bounds, all_texts)
    page_info = derive_final_res(id2view, clickable_views, all_texts, activity_name, abs_img_path)
    page_info.setdefault("is_scrollable", is_scrollable)
    flag1 = len(page_info["simple_info"]["button"]) > 0 or len(page_info["simple_info"]["input"]) > 0
    flag2 = len(page_info["text_on_screen"]) == 1 and "Bluetooth" in page_info["text_on_screen"][0]
    if flag1 or flag2:
        return page_info
    else:
        return {}


def get_clickable_views(id2view: dict, clickable_bounds: dict, all_texts: dict):
    check_views = set()
    clickable_views = {"sure": {}, "not_sure_in_gray": {}, "exclude": {}, "not_sure_invisible": {},
                       "not_sure_bound_inter": {}}
    unsort_view_ids = []
    for view_id, bound_info in clickable_bounds.items():
        bound_width = bound_info["bound"][1][0] - bound_info["bound"][0][0]
        bound_height = bound_info["bound"][1][1] - bound_info["bound"][0][1]
        area = abs(bound_width * bound_height) * 1920 + bound_info["bound"][0][1] + 0.0001 * bound_info["bound"][0][0]
        # area = abs(bound_width * bound_height)
        if bound_info["bound"][1][1] == 1794:
            area = area * 2
        unsort_view_ids.append([view_id, area])
    unsort_view_ids.sort(key=lambda x: x[1])
    clickable_view_ids = [x[0] for x in unsort_view_ids]
    for view_id in clickable_view_ids:
        view_info = id2view[view_id]
        view_bound_info = clickable_bounds[view_id]
        name_info = get_view_refer_name(view_info)
        view_info.setdefault("name_info", name_info)
        if name_info["name"] == "Custom steps" and view_info["bounds"][0][1] > 1000:
            name_info["name"] = "Custom steps2"
        # print(name_info["name"], view_info["bounds"])
        if view_bound_info["warp_other_bound"] > 2:
            # print("exclude:", view_id, name_info["name"], view_info["bounds"], view_bound_info["warp_other_bound"])
            clickable_views["exclude"].setdefault(view_id, view_info)
            check_views.add(view_id)
            continue
        if "CheckBox" in view_info["class"] and "mail" in name_info["name"]:
            clickable_views["exclude"].setdefault(view_id, view_info)
            check_views.add(view_id)
            continue
        if exclude_by_name(name_info["name"]):
            # print("exclude:", view_id, name_info["name"])
            clickable_views["exclude"].setdefault(view_id, view_info)
            check_views.add(view_id)
            continue
        if view_bound_info["in_gray_area"] > 0:
            # print("not_sure_in_gray:", view_id, name_info["name"])
            clickable_views["not_sure_in_gray"].setdefault(view_id, view_info)
            check_views.add(view_id)
            continue
        name_from_id = name_info["from_id"]
        if name_from_id in all_texts.keys() and not all_texts[name_from_id]['visible']:
            # print("not_sure_invisible:", view_id,  name_info["name"])
            clickable_views["not_sure_invisible"].setdefault(view_id, view_info)
            check_views.add(view_id)
            continue
        if name_from_id in all_texts.keys() and all_texts[name_from_id]['visible'] and all_texts[name_from_id][
            'match_ocr'] and view_bound_info["warp_other_bound"] <= 1:
            # print("sure:", view_id, name_info["name"])
            clickable_views["sure"].setdefault(view_id, view_info)
            check_views.add(view_id)
            continue
    sure_clickbounds = [view_info["bounds"] for view_info in clickable_views["sure"].values()]
    for view_id in clickable_view_ids:
        if view_id in check_views:
            continue
        view_info = id2view[view_id]
        cur_view_bound = view_info["bounds"]
        inter_with_sure = False
        for sure_clickbound in sure_clickbounds:
            if is_bound_intersect(cur_view_bound, sure_clickbound):
                # print(cur_view_bound, sure_clickbound)
                inter_with_sure = True
                break
        short_class = view_info["class"].split(".")[-1].lower()
        is_float = "image" in short_class or "float" in short_class
        if not inter_with_sure or is_float:
            # print("sure2:", view_id, view_info["name_info"]["name"])
            clickable_views["sure"].setdefault(view_id, view_info)
            sure_clickbounds.append(view_info["bounds"])
            check_views.add(view_id)
        else:
            # print("not_sure_bound_inter:", view_id, view_info["name_info"]["name"])
            clickable_views["not_sure_bound_inter"].setdefault(view_id, view_info)
            check_views.add(view_id)
    return clickable_views


# def load_ocr_res(img_path: str):
#     img_dir = "/".join(img_path.split("/")[:-1])
#     img_name = img_path.split("/")[-1]
#     ocr_path = os.path.join(img_dir, "ocr_res.json")
#     if not os.path.exists(ocr_path):
#         o = OCR()
#         o.perform_on_dir(img_dir)
#     ocr_json = json.load(open(ocr_path, "r"))
#     ocr_res = ocr_json[img_name]
#     for v in ocr_res:
#         if len(v["bound"]) == 4:
#             v["bound"] = convert_4_bound(v["bound"])
#     return ocr_res


def not_care_page(full_activity_name: str, id2view: dict):
    if "com.android.launcher" in full_activity_name:
        return True
    all_views = list(id2view.values())
    if len(all_views) < 2:
        return True
    if all_views[1]["package"] == "com.android.browser" or all_views[1]["package"][:4] == "fax.":
        return True
    return False


def get_basic_info(xml_source: str, ocr_res: list, gray_area: list):
    id2view = {}
    id2child = {}
    clickable_bounds = {}
    xml_source = "<hierarchy" + xml_source.split("<hierarchy", 1)[1]
    xml_source = xml_source.replace("&#", "")
    xml_parser = etree.XML(xml_source)
    root_tree = xml_parser.getroottree()
    root_node = root_tree.getroot()
    get_view_recursion(root_node, root_tree, "/hierarchy", id2view, id2child)
    all_texts = {}
    is_scrollable = False
    scrollable_areas = []
    for view_id, view_info in id2view.items():
        clickable_flag1 = view_info["clickable"] or view_info["long_clickable"]
        if "content_description" in view_info.keys():
            clickable_flag2 = "01" in view_info["content_description"] and "2023" in view_info["content_description"]
            # print(view_info["content_description"], clickable_flag2)
        else:
            clickable_flag2 = False
        if clickable_flag1 or clickable_flag2:
            # print(view_id)
            # print(view_info["bounds"])
            clickable_bounds.setdefault(view_id, {"bound": view_info["bounds"],
                                                  "in_gray_area": is_in_gray_area(view_info["bounds"], gray_area)})
        # if isinstance(view_info["text"], str) and len(only_ascii(view_info["text"])) > 0 and "edittext" not in \
        #         view_info["class"].lower():
        #     all_texts.setdefault(view_id, check_text_by_ocr(view_info, ocr_res))
        if isinstance(view_info["text"], str) and len(only_ascii(view_info["text"])) > 0:
            temp_text_info = check_text_by_ocr(view_info, ocr_res)
            temp_text_info.setdefault("from_view", view_info["class"].split(".")[-1])
            all_texts.setdefault(view_id, temp_text_info)
        if "listview" in view_info["class"].lower() or "recyclerview" in view_info["class"].lower():
            if view_info["scrollable"] == "true":
                is_scrollable = True
                scrollable_areas.append(view_info["bounds"])
    for view_id, bound_info in clickable_bounds.items():
        warp_other_bound = 0
        for t_id, t_bound_info in clickable_bounds.items():
            if view_id == t_id:
                continue
            if is_b1_in_b2(t_bound_info["bound"], bound_info["bound"]):
                warp_other_bound += 1
        bound_info.setdefault("warp_other_bound", warp_other_bound)
    for view_id, view_info in id2view.items():
        warp_in_scrollable = False
        for scrollable_bound in scrollable_areas:
            if is_b1_in_b2(view_info["bounds"], scrollable_bound):
                warp_in_scrollable = True
                break
        view_info.setdefault("warp_in_scrollable", warp_in_scrollable)
    for _, text_info in all_texts.items():
        in_clickable_bound = False
        text_bound = text_info["bound"]
        for _, bound_info in clickable_bounds.items():
            if not bound_info["warp_other_bound"] and is_b1_center_in_b2(text_bound, bound_info["bound"]):
                in_clickable_bound = True
                break
        text_info.setdefault("in_clickable_bound", in_clickable_bound)
    return id2view, id2child, clickable_bounds, all_texts, is_scrollable


def check_text_by_ocr(view_info: dict, ocr_res: list):
    view_bound = view_info["bounds"]
    if len(ocr_res) == 0:
        match_ocr = True
        text_visible = True
    else:
        text_visible = False
        match_ocr = False
    for ocr_item in ocr_res:
        # print(view_info["text"], view_bound, ocr_item["bound"], is_b1_center_in_b2(ocr_item["bound"], view_bound), is_bound_intersect(ocr_item["bound"], view_bound))
        if is_b1_center_in_b2(ocr_item["bound"], view_bound):
            text_visible = True
            if ocr_item["score"] < 0.9 or is_str_match(view_info["text"], ocr_item["text"]):
                match_ocr = True
            break
    in_list = "listview" in view_info["xpath"].lower() or "recyclerview" in view_info["xpath"].lower()
    in_edittext = "edittext" in view_info["xpath"].lower()
    text_info = {"text": only_ascii(view_info["text"]), "bound": view_info["bounds"], "visible": text_visible,
                 "match_ocr": match_ocr, "in_list": in_list, "in_edittext": in_edittext}
    return text_info


def set_context_info(id2view: dict, all_texts: dict):
    for view_id, view_info in id2view.items():
        # get warp text
        cur_bound = view_info["bounds"]
        cur_center = get_bound_center(cur_bound)
        warp_text = ""
        warp_text_id = None
        for text_id, text_info in all_texts.items():
            if not text_info['visible']:
                continue
            if is_b1_in_b2(text_info["bound"], cur_bound):
                warp_text = text_info["text"]
                warp_text_id = text_id
                break
        view_info.setdefault("warp_text", only_ascii_clip(warp_text))
        view_info.setdefault("warp_text_id", warp_text_id)
        # get nearby text (distance over 400000 will be drop)
        neighbor_text = ""
        neighbor_text_dis = 400000
        neighbor_text_id = None
        for text_id, text_info in all_texts.items():
            if not text_info['visible'] or text_info['in_clickable_bound']:
                continue
            text_center = get_bound_center(text_info["bound"])
            dis = get_distance(text_center, cur_center)
            if dis > 10 and dis < neighbor_text_dis and (not is_point_in_bound(text_center, cur_bound)):
                neighbor_text = text_info["text"]
                neighbor_text_dis = dis
                neighbor_text_id = text_id
        view_info.setdefault("neighbor_text", only_ascii_clip(neighbor_text))
        view_info.setdefault("neighbor_text_dis", neighbor_text_dis)
        view_info.setdefault("neighbor_text_id", neighbor_text_id)
    for view_id, view_info in id2view.items():
        # get sibling text
        sibling_text = ""
        sibling_text_id = None
        cur_parent = view_info["parent_id"]
        up_time = 0
        while sibling_text == "" and up_time < 3 and cur_parent in id2view.keys():
            if id2view[cur_parent]["warp_text"] != "" and id2view[cur_parent]["warp_text"] != view_info["text"]:
                sibling_text = id2view[cur_parent]["warp_text"]
                sibling_text_id = id2view[cur_parent]["warp_text_id"]
                break
            else:
                cur_parent = id2view[cur_parent]["parent_id"]
                up_time += 1
        view_info.setdefault("sibling_text", only_ascii_clip(sibling_text))
        view_info.setdefault("sibling_text_id", sibling_text_id)


def get_view_recursion(view_node, root_tree, parent_id, id2view: dict, id2child: dict):
    attribs = view_node.attrib
    if "package" in attribs.keys():
        if "com.android" in attribs["package"] or attribs["package"] == "android":
            return -1
    cur_child = []
    view_id = ""
    if "clickable" in attribs.keys():
        cur_view_info = {}
        cur_view_info.setdefault("class", attribs["class"])
        cur_clickable = (attribs["clickable"] == "true")
        cur_view_info.setdefault("clickable", cur_clickable)
        cur_view_info.setdefault("package", attribs["package"])
        cur_view_info.setdefault("scrollable", attribs["scrollable"])
        cur_long_clickable = (attribs["long-clickable"] == "true")
        cur_view_info.setdefault("long_clickable", cur_long_clickable)
        # cur_view_info.setdefault("text", attribs["text"])
        if attribs["text"] == None or len(attribs["text"].strip()) == 0:
            cur_view_info.setdefault("text", "")
        else:
            cur_view_info.setdefault("text", attribs["text"])
        # cur_view_info.setdefault("content_description", attribs["content-desc"])
        if "content-desc" not in attribs.keys() or len(attribs["content-desc"].strip()) == 0:
            cur_view_info.setdefault("content_description", "")
        else:
            cur_view_info.setdefault("content_description", attribs["content-desc"])
        if "resource-id" not in attribs.keys() or len(attribs["resource-id"].strip()) == 0:
            cur_view_info.setdefault("resource_id", "")
        else:
            cur_view_info.setdefault("resource_id", attribs["resource-id"])
        cur_view_info.setdefault("parent_id", parent_id)
        bounds_str = str(attribs["bounds"])
        bounds_str = bounds_str.replace("][", ",")[1:-1]
        b = [int(bi) for bi in bounds_str.split(",")]
        bounds_arr = [[b[0], b[1]], [b[2], b[3]]]
        cur_view_info.setdefault("bounds", bounds_arr)
        cur_view_info.setdefault("children", cur_child)
        view_id = root_tree.getpath(view_node)
        cur_view_info.setdefault("xpath", view_id)
        cur_view_info.setdefault("view_id", view_id)
        id2child.setdefault(view_id, cur_child)
        id2view.setdefault(view_id, cur_view_info)
    children_node = view_node.getchildren()
    if len(children_node) == 0:
        return view_id
    for child in children_node:
        child_id = get_view_recursion(child, root_tree, view_id, id2view, id2child)
        if child_id != "":
            cur_child.append(child_id)
    return view_id


def derive_final_res(id2view, clickable_views, all_texts, activity_name, abs_img_path):
    # page_info.setdefault("clickable_views", clickable_views)
    # page_info.setdefault("text_on_screen", text_on_screen)xl
    # page_info.setdefault("simple_info", simple_info)
    # page_info.setdefault("activity_name", get_activity_name(layout["foreground_activity"]))
    page_type = get_page_type(id2view)
    page_info = {"activity_name": activity_name, "img_path": abs_img_path, "page_type": page_type,
                 "page_title": get_page_title(all_texts, page_type), "all_texts": all_texts}
    text_on_screen = []
    text_not_click = []
    for text_info in all_texts.values():
        clean_text = only_ascii_clip(text_info["text"])
        if len(clean_text) > 1:
            if not text_info['in_edittext']:
                text_on_screen.append(only_ascii_clip(text_info["text"]))
            if text_info['visible'] and (not text_info['in_clickable_bound']) and (not text_info['in_list']):
                text_not_click.append(only_ascii_clip(text_info["text"], 5))
    text_not_click = list(set(text_not_click))
    page_info.setdefault("text_on_screen", text_on_screen)
    page_info.setdefault("text_not_click", text_not_click)
    xpath_clickable_views = {}
    simple_info = {"button": {}, "input": {}}
    actions = {}
    for view_id, view_info in clickable_views["sure"].items():
        cur_xpath = view_info["xpath"]
        # cur_xpath = view_id
        xpath_clickable_views.setdefault(cur_xpath, view_info)
        view_name = view_info["name_info"]["name"]
        if flit_by_name(view_name):
            continue
        if view_name != "none" and len(view_name) > 1:
            if "edittext" in view_info["class"].lower():
                if view_name not in ["time", "date"]:
                    simple_info["input"].setdefault(cur_xpath, view_name)
                    actions.setdefault("Input[" + view_name + "]",
                                       {"xpath": cur_xpath, "name": view_name, "bound": view_info["bounds"],
                                        "warp_in_scrollable": view_info["warp_in_scrollable"]})
            else:
                simple_info["button"].setdefault(cur_xpath, view_name)
                if view_info["clickable"] or "2023" in view_info["name_info"]["name"]:
                    actions.setdefault("Click[" + view_name + "]",
                                       {"xpath": cur_xpath, "name": view_name, "bound": view_info["bounds"],
                                        "warp_in_scrollable": view_info["warp_in_scrollable"]})
                if view_info["long_clickable"]:
                    if view_name.lower() not in ["more options", "navigate up", "done"]:
                        actions.setdefault("Long press[" + view_name + "]",
                                           {"xpath": cur_xpath, "name": view_name, "bound": view_info["bounds"],
                                            "warp_in_scrollable": view_info["warp_in_scrollable"]})
        # if view_name == "none" and "imagebutton" in view_info["class"].lower() and view_info[
        #     "clickable"] and "fab" not in view_info["resource_id"]:
        #     actions.setdefault("Click[Next]", {"xpath": cur_xpath, "name": "Next", "bound": view_info["bounds"],
        #                                        "warp_in_scrollable": view_info["warp_in_scrollable"]})

    page_info.setdefault("clickable_views", xpath_clickable_views)
    page_info.setdefault("simple_info", simple_info)
    page_info.setdefault("actions", actions)
    for view_type, view_dict in clickable_views.items():
        cur_views = []
        for view_id, view_info in view_dict.items():
            cur_views.append(view_info["name_info"]["name"] + ", " + str(view_info["bounds"]))
        page_info.setdefault(view_type, cur_views)
    return page_info


def get_page_title(all_texts: dict, page_type: str):
    text_center = []
    if page_type == "normal":
        for text_id, text_info in all_texts.items():
            cur_center = get_bound_center(text_info["bound"])
            cur_pos = 1920 * cur_center[1] + cur_center[0]
            cur_text_clean = re.sub(r"[^a-z0-9A-Z]", " ", text_info["text"])
            cur_clean_len = len(cur_text_clean.split())
            cur_text_size = text_info["bound"][1][1] - text_info["bound"][0][1]
            flag1 = cur_clean_len >= 1 and cur_clean_len <= 4
            flag2 = text_info['visible'] and text_info['match_ocr'] and (not text_info["in_clickable_bound"])
            # flag2 = text_info['visible'] and text_info['match_ocr']
            # flag3 = cur_center[0] >= 108 and cur_center[0] <= 432
            flag3 = cur_center[0] >= 108 and cur_center[0] <= 600
            flag4 = cur_center[1] >= 80 and cur_center[1] <= 288
            flag5 = cur_text_size >= 60 and cur_text_size <= 160
            flag6 = cur_text_clean.lower() != "all decks"
            # print(cur_text_clean, flag1, flag2, flag3, flag4, flag5, text_info["bound"])
            if flag1 and flag2 and flag3 and flag4 and flag5 and flag6:
                text_center.append([cur_pos, text_id])
        if len(text_center) == 0:
            return ""
        text_center.sort(key=lambda x: x[0])
        first_text_id = text_center[0][1]
        title = re.sub(r"[^a-zA-Z0-9]", " ", all_texts[first_text_id]["text"]).strip()
        return title
    elif page_type == "dialog":
        for text_id, text_info in all_texts.items():
            cur_center = get_bound_center(text_info["bound"])
            cur_pos = 1920 * cur_center[1] + cur_center[0]
            cur_text_clean = re.sub(r"[^a-z0-9A-Z]", " ", text_info["text"])
            cur_clean_len = len(cur_text_clean.split())
            cur_text_size = text_info["bound"][1][1] - text_info["bound"][0][1]
            if cur_clean_len > 5:
                cur_text_clean = " ".join(cur_text_clean.split(" ")[:5]) + "..."
            flag1 = text_info['visible'] and text_info['match_ocr'] and (not text_info["in_clickable_bound"])
            flag2 = cur_text_size >= 55 and cur_text_size <= 85
            if flag1 and flag2:
                text_center.append([cur_pos, cur_text_clean])
        if len(text_center) == 0:
            return ""
        text_center.sort(key=lambda x: x[0])
        return text_center[0][1]
    elif page_type == "option menu":
        all_options = []
        for text_id, text_info in all_texts.items():
            if text_info['visible'] and text_info['match_ocr'] and text_info["in_clickable_bound"]:
                cur_text_clean = re.sub(r"[^a-z0-9A-Z]", " ", text_info["text"])
                cur_clean_len = len(cur_text_clean.split())
                cur_text_size = text_info["bound"][1][1] - text_info["bound"][0][1]
                if cur_clean_len > 3:
                    cur_text_clean = " ".join(cur_text_clean.split(" ")[:3]) + "..."
                if cur_text_size >= 55 and cur_text_size <= 85:
                    all_options.append(cur_text_clean)
        if len(all_options) == 0:
            return ""
        all_options_strs = ", ".join(all_options)
        return all_options_strs
    else:
        return ""


def get_page_type(id2view: dict):
    view_keys = list(id2view.keys())
    view_keys.sort(key=lambda x: len(x))
    first_view = id2view[view_keys[0]]
    page_width = first_view["bounds"][1][0] - first_view["bounds"][0][0]
    page_height = first_view["bounds"][1][1] - first_view["bounds"][0][1]
    page_center = get_bound_center(first_view["bounds"])
    if page_width < 1070 and page_height < 1300:
        if page_center[0] >= 520 and page_center[0] <= 560:
            # In the screen center, is dialog
            return "dialog"
        else:
            return "option menu"
    return "normal"


def parse_all_page():
    res = {"page_json": [], "page_img": [], "text_on_screen": [], "button": [], "input": []}
    keys = ["sure", "not_sure_in_gray", "exclude", "not_sure_invisible", "not_sure_bound_inter"]
    for k in keys:
        res.setdefault(k, [])
    state_dir = "D:/PycharmProjects/ReviewReproduce/data/FaxRes/AnkiDroid/"
    for f in os.listdir(state_dir):
        if ".xml" not in f:
            continue
        page_xml = state_dir + f
        print(state_dir + f)
        page_info = parse_layout_appium(page_xml)
        if len(page_info.keys()) == 0:
            continue
        res["page_json"].append('=HYPERLINK("{}","{}")'.format(page_xml, "show"))
        res["page_img"].append('=HYPERLINK("{}","{}")'.format(page_info["img_path"], "show"))
        res["text_on_screen"].append("\n".join(page_info["text_on_screen"]))
        res["button"].append("\n".join(list(page_info["simple_info"]["button"].values())))
        res["input"].append("\n".join(list(page_info["simple_info"]["input"].values())))
        for k in keys:
            res[k].append("\n".join(page_info[k]))
    df = pd.DataFrame(res)
    df.to_csv("../temp/test_page_info.csv", index=False)


def check_page_is_same(page_info1: dict, page_info2: dict, thres_action=0.9, thres_text=0.9):
    if "activity" not in page_info1.keys() or "activity" not in page_info2.keys():
        return False
    if page_info1["activity"] != page_info2["activity"]:
        return False
    if set(page_info1["actions"].keys()) == set(page_info2["actions"].keys()):
        if len(page_info1["actions"].keys()) > 3:
            return True
    if page_info1["is_scrollable"] and page_info2["is_scrollable"]:
        action_key1 = set(page_info1["actions"].keys())
        action_key2 = set(page_info2["actions"].keys())
        # print("action_key1:", len(action_key1), action_key1)
        # print("action_key2:", len(action_key2), action_key2)
        # print("inter size:", len(action_key1.intersection(action_key2)))
        if action_key1.issubset(action_key2):
            return True
    # if page_info1["page_name"] != page_info2["page_name"]:
    #     return False

    action_size1 = len(page_info1["actions"].keys())
    action_size2 = len(page_info2["actions"].keys())
    min_size = min(action_size1, action_size2)
    max_size = max(action_size1, action_size2)
    if max_size > 0 and min_size / max_size <= thres_action:
        return False
    action_set1 = set()
    for action_keys, action_info in page_info1["actions"].items():
        action_set1.add(process_xpath(action_info["xpath"]))
    action_set2 = set()
    for action_keys, action_info in page_info2["actions"].items():
        action_set2.add(process_xpath(action_info["xpath"]))
    inter_action_size = len(action_set1.intersection(action_set2))
    union_action_size = len(action_set1.union(action_set2))
    if inter_action_size >= 3:
        if union_action_size > 0 and inter_action_size / union_action_size >= thres_action:
            # text_set1 = set(page_info1["text_on_screen"])
            # text_set2 = set(page_info2["text_on_screen"])
            # inter_text_size = len(text_set1.intersection(text_set2))
            # union_text_size = len(text_set1.intersection(text_set2))
            # if union_text_size > 0 and inter_text_size / union_text_size >= thres_text:
            #     return True
            # else:
            #     return False
            return True
        else:
            return False
    else:
        text_set1 = set(page_info1["text_on_screen"])
        text_set2 = set(page_info2["text_on_screen"])
        inter_text_size = len(text_set1.intersection(text_set2))
        union_text_size = len(text_set1.union(text_set2))
        same_flag1 = union_action_size > 0 and inter_action_size / union_action_size >= thres_action
        same_flag2 = union_text_size > 0 and inter_text_size / union_text_size >= thres_text
        if same_flag1 and same_flag2:
            return True
        else:
            return False


if __name__ == '__main__':
    # path = "../Data/AppState/Amaze/Main Activity#7.xml"
    # path = "../Data/Temp/backup/10-22_16-15-16.xml"
    # path = "../Data/FaxRes/17.transistor_s/org.y20k.transistor.MainActivity_1.xml"
    # path = "../Data/Temp/backup/11-15_21-14-23.xml"
    # res2 = parse_layout_appium(path)
    # # print(res2)
    # print(res2["page_title"])
    # print(res2["text_on_screen"])
    # for action_key, ori_info in res2["actions"].items():
    #     print(action_key, ori_info["bound"], ori_info["warp_in_scrollable"])
    #     print(ori_info["xpath"])

    # path = "../Data/Temp/backup/12-05_17-18-48.xml"
    # path = "../Data/AppState/ankidroid-Anki-Android-9914/AnkiDroid#5.xml"
    # res1 = parse_layout_appium(path)
    # res1.setdefault("activity", "a1")
    # for action_key, ori_info in res1["actions"].items():
    #     print(action_key, ori_info["bound"], ori_info["warp_in_scrollable"])
    #     print(ori_info["xpath"])
    # path = "../Data/AppState/ankidroid-Anki-Android-9914/AnkiDroid#14.xml"
    path = "../Data/Temp/backup/12-13_21-58-09.xml"
    res2 = parse_layout_appium(path)
    res2.setdefault("activity", "a1")
    for action_key, ori_info in res2["actions"].items():
        print(action_key, ori_info["bound"], ori_info["warp_in_scrollable"])
        print(ori_info["xpath"])

