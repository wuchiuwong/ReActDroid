import os

from my_utils.str_utils import get_activity_name
from tool.layout_parser import parse_layout_appium
from tool.memory import Memory
import pandas as pd


def process_fax_res(fax_res_dir: str, memory: Memory, crash_info: dict, debug=False):
    page_groups = group_fax_res(fax_res_dir)
    crash_info.setdefault("crash_page_id", "unknown")
    id2path = {}
    path2id = {}
    id2actions = {}
    path2prompt = {}
    for xml_path, xml_group in page_groups.items():
        memory.reset_page_visit()
        page_info = get_page_info(xml_path)
        if len(page_info.keys()) == 0:
            continue
        page_info.setdefault("page_xml", xml_path)
        page_info.setdefault("page_img", xml_path.replace(".xml", ".png"))
        base_page_id = memory.get_page_id(page_info, init_by_static=True, do_update=False)
        if base_page_id not in id2path:
            if debug:
                print(xml_path.split("/")[-1], "is a new page:", base_page_id)
            path2prompt.setdefault(xml_path, gen_page_prompt(page_info))
            id2path.setdefault(base_page_id, [xml_path.split("/")[-1]])
            path2id.setdefault(xml_path.split("/")[-1], base_page_id)
            cur_actions = list(page_info["actions"].keys())
            id2actions.setdefault(base_page_id, ", ".join(cur_actions))
        else:
            if debug:
                print(xml_path.split("/")[-1], "is a founded page:", base_page_id, id2path[base_page_id])
            id2path[base_page_id].append(xml_path.split("/")[-1])
        # if xml_path.split("/")[-1] == crash_info["xml_path"]:
        #     crash_info["crash_page_id"] = base_page_id
        for sub_xml, click_pos in xml_group.items():
            memory.reset_page_visit()
            sub_page_info = get_page_info(sub_xml)
            if len(sub_page_info.keys()) > 0:
                sub_page_info.setdefault("page_xml", sub_xml)
                sub_page_info.setdefault("page_img", sub_xml.replace(".xml", ".png"))
                sub_page_id = memory.get_page_id(sub_page_info, init_by_static=True, do_update=False)
                if sub_page_id not in id2path:
                    if debug:
                        print("\t", sub_xml.split("/")[-1], "is a new page:", sub_page_id)
                    path2id.setdefault(sub_xml.split("/")[-1], sub_page_id)
                    path2prompt.setdefault(sub_xml, gen_page_prompt(sub_page_info))
                    id2path.setdefault(sub_page_id, [sub_xml.split("/")[-1]])
                    cur_actions = list(sub_page_info["actions"].keys())
                    id2actions.setdefault(sub_page_id, ", ".join(cur_actions))
                else:
                    if debug:
                        print("\t", sub_xml.split("/")[-1], "is a founded page:", id2path[sub_page_id])
                    id2path[base_page_id].append(sub_xml.split("/")[-1])
                # if sub_xml.split("/")[-1] == crash_info["xml_path"]:
                #     crash_info["crash_page_id"] = sub_page_id
                action_id, action_info = memory.get_action_by_pos(base_page_id, click_pos)
                memory.stg.update_previous_page(sub_page_id, base_page_id)
                if len(action_info.keys()) > 0:
                    action_info["dst_page"] = sub_page_id
                    action_info["dst_page_name"] = sub_page_info["page_name"]
                    if debug:
                        print("\t", click_pos, "found action:", action_id, action_info["bound"])
                else:
                    if debug:
                        print("\t", click_pos, "can not found action")
    show_res = {"xml": [], "show_xml": [], "show_img": [], "prompt": [], "page_id": []}
    for xml, prompt in path2prompt.items():
        xml = xml.split("/")[-1]
        xml_path = fax_res_dir + xml
        img_path = xml_path.replace(".xml", ".png")
        show_res["xml"].append(xml)
        show_res["show_xml"].append('=HYPERLINK("{}","{}")'.format(xml_path, "show"))
        show_res["show_img"].append('=HYPERLINK("{}","{}")'.format(img_path, "show"))
        show_res["prompt"].append(prompt)
        show_res["page_id"].append(path2id[xml])
    page_df = pd.DataFrame(show_res)
    page_df.to_csv("../Data/Temp/page_prompts/" + fax_res_dir.split("/")[-1] + ".csv", index=False)
    res = {"id2path": id2path, "id2actions": id2actions, "path2id": path2id, "path2prompt": path2prompt}
    return res
    # all_actions = memory.get_available_actions("Amaze#2")
    # for action_key, action_info in all_actions.items():
    #     print(action_key)
    #     print(action_info)

def group_fax_res(fax_res_dir):
    page_groups = {}
    if not os.path.exists(fax_res_dir):
        return page_groups
    for file in os.listdir(fax_res_dir):
        if "-" in file.split("/")[-1] and ".xml" in file:
            name_parts = file.split("_")
            # base_file = fax_res_dir + "/" + name_parts[0] + "_" + name_parts[1] + ".xml"
            base_file = fax_res_dir + "/" + "_".join(name_parts[:-1]) + ".xml"
            pos_part = name_parts[-1].replace(".xml", "")
            click_posx = int(pos_part.split("-")[0])
            click_posy = int(pos_part.split("-")[1])
            click_pos = [click_posx, click_posy]
            if base_file not in page_groups.keys():
                page_groups.setdefault(base_file, {})
            page_groups[base_file].setdefault(fax_res_dir + "/" + file, click_pos)
    return page_groups


def get_page_info(xml_path: str):
    activity_name = xml_path.split(".")[-2].split("_")[0]
    page_info = parse_layout_appium(xml_path)
    if len(page_info.keys()) == 0:
        return {}
    activity_name = get_activity_name(activity_name)
    if "page_title" in page_info.keys() and len(page_info["page_title"]) > 0:
        if page_info["page_type"] == "dialog":
            page_name = "dialog (" + page_info["page_title"] + ")"
        elif page_info["page_type"] == "option menu":
            page_name = "menu (" + page_info["page_title"] + ")"
        else:
            page_name = page_info["page_title"]
    else:
        if page_info["page_type"] == "dialog":
            page_name = "dialog of " + activity_name
        elif page_info["page_type"] == "option menu":
            page_name = "menu of " + activity_name
        else:
            page_name = activity_name
    page_info.setdefault("page_name", page_name)
    page_info.setdefault("activity", xml_path.split(".")[-2].split("_")[0])
    return page_info


def show_all_page_prompts():
    data_path = "../Data/Test/ReCDroid_all.csv"
    for _, line in pd.read_csv(data_path).iterrows():
        crash_info = {"crash_desc": line["crash"], "crash_page": line["page_name"], "xml_path": line["xml_path"],
                      "app_pkg": line["app_pkg"].strip(), "app_acti": line["app_acti"].strip(), "app_name": line["app"]}
        m = Memory(crash_info, "")
        fax_dir = "D:/PycharmProjects/ReActReproduce/Data/FaxRes/" + line["app"] + "/"
        if not os.path.exists(fax_dir):
            print("not find fax_dir:", fax_dir)
            continue
        fax_res = process_fax_res(fax_dir, m, crash_info)
        path2prompt = fax_res["path2prompt"]
        show_res = {"xml": [], "show_xml": [], "show_img": [], "prompt": []}
        for xml, prompt in path2prompt.items():
            xml = xml.split("/")[-1]
            xml_path = fax_dir + xml
            img_path = xml_path.replace(".xml", ".png")
            show_res["xml"].append(xml)
            show_res["show_xml"].append('=HYPERLINK("{}","{}")'.format(xml_path, "show"))
            show_res["show_img"].append('=HYPERLINK("{}","{}")'.format(img_path, "show"))
            show_res["prompt"].append(prompt)
        page_df = pd.DataFrame(show_res)
        page_df.to_csv("../Data/Temp/page_prompts/" + line["app"] + ".csv", index=False)


# def gen_page_prompt(page_info: dict):
#     text_not_click = page_info["text_not_click"]
#     print(text_not_click)
#     simple_info_button = page_info["simple_info"]["button"]
#     print(simple_info_button)
#     simple_info_input = page_info["simple_info"]["input"]
#     print(simple_info_input)
#     print("#" * 20)

def gen_page_prompt(page_info: dict):
    # name of page 2: user
    # displayed text on page 2: 'get started'
    # buttons on page 2: 'sign in'
    # input boxs on page 2: 'email', 'password'
    page_prompt = "#" * 3 + " page $PAGE_IDX$ " + "#" * 3 + "\n"
    page_prompt += "name of page $PAGE_IDX$: " + page_info["page_name"] + "\n"
    if len(page_info["text_not_click"]) > 0:
        page_prompt += "displayed text on page $PAGE_IDX$: " + quote_text(page_info["text_not_click"]) + "\n"
    buttons = list(page_info["simple_info"]["button"].values())
    if len(buttons) > 0:
        page_prompt += "buttons on page $PAGE_IDX$: " + quote_text(buttons) + "\n"
    inputs = list(page_info["simple_info"]["input"].values())
    if len(inputs) > 0:
        page_prompt += "input boxs on page $PAGE_IDX$: " + quote_text(inputs) + "\n"
    # print(page_prompt)
    return page_prompt.strip()


def quote_text(text_list: list):
    text_list2 = ["\'" + t + "\'" for t in set(text_list)]
    return ", ".join(text_list2)




if __name__ == '__main__':
    app_info = {"app_pkg": "", "app_acti": "", "app_name": "Amaze"}
    m = Memory(app_info, "")
    crash_info = {"xml_path": ""}
    process_fax_res("../Data/FaxRes/1.newsblur_s", m, crash_info, debug=True)
    # show_all_page_prompts()