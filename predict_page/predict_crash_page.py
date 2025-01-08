from tool.layout_parser import parse_layout_appium
from llm.model import chatgpt
import pandas as pd
import os
import json


def get_messages(t_prompt: str, p_prompts: list, q_prompt: str):
    messages = [{"role": "system", "content": t_prompt}]
    for p_prompt in p_prompts:
        messages.append({"role": "user", "content": p_prompt})
    messages.append({"role": "user", "content": q_prompt})
    return messages


def read_page_prompt(page_csv_path: str):
    df = pd.read_csv(page_csv_path)
    all_pages = []
    idx2row = {}
    for idx, row in df.iterrows():
        show_idx = idx + 1
        cur_prompt = row["prompt"].replace("$PAGE_IDX$", str(show_idx))
        all_pages.append(cur_prompt)
        idx2row.setdefault(show_idx, row)
    p_prompt = "\n".join(all_pages[:45])
    return p_prompt, idx2row


def predict(app_name: str, crash_desc: str):
    t_prompt = open("../predict_page/task_prompt2.txt", "r").read()
    q_prompt = open("../predict_page/ques_prompt.txt", "r").read()
    page_csv_path = "../Data/Temp/page_prompts/" + app_name + ".csv"
    if not os.path.exists(page_csv_path):
        print("not exist:", page_csv_path)
        return {}
    p_prompt, idx2row = read_page_prompt(page_csv_path)
    if len(idx2row.keys()) == 0:
        print("empty:", page_csv_path)
        return {}
    q_prompt = q_prompt.replace("$issue$", crash_desc)
    ask_msg = get_messages(t_prompt, [p_prompt], q_prompt)
    try_time = 1
    valid = False
    res = {}
    while try_time <= 3:
        try_time += 1
        response = chatgpt(ask_msg)
        valid, res = parse_response(response)
        if valid:
            break
        print("try again:", try_time)
    if not valid or len(res.keys()) == 0:
        return {}
    res.setdefault("xml", idx2row[int(res["Answer"])]["xml"])
    res.setdefault("crash_page_id", idx2row[int(res["Answer"])]["page_id"])
    res.setdefault("row", idx2row[int(res["Answer"])])
    res.setdefault("ori_res", response)
    return res


def parse_response(response: str):
    try:
        res = json.loads(response)
        for k in ["Reason", "Answer", "Confidence"]:
            if k not in res.keys():
                return False, {}
        # if not isinstance(res["Answer"], int):
        #     return False, {}
        if isinstance(res["Answer"], list):
            res["Answer"] = res["Answer"][0]
        elif not isinstance(res["Answer"], int):
            return False, {}
        return True, res
    except Exception as e:
        return False, {}


def perform_all_data():
    all_res = {"app": [], "crash": [], "ori_res": [], "page": [], "show_xml": [], "show_img": []}
    data_path = "../Data/Test/ReCDroid_all.csv"
    for _, line in pd.read_csv(data_path).iterrows():
        print(line["app"], line["crash"])
        res = predict(line["app"], line["crash"])
        if len(res.keys()) == 0:
            continue
        all_res["app"].append(line["app"])
        all_res["crash"].append(line["crash"])
        all_res["ori_res"].append(res["ori_res"])
        all_res["page"].append(res["row"]["prompt"])
        all_res["show_xml"].append(res["row"]["show_xml"])
        all_res["show_img"].append(res["row"]["show_img"])
    df = pd.DataFrame(all_res)
    df.to_csv("predict_recdroid.csv", index=False)


if __name__ == '__main__':
    # predict("1.newsblur_s",
    #         "Attempting to register or login with an invalid server address (e.g., xx) crashes the app.")
    perform_all_data()
