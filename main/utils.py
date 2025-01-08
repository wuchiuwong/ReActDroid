import json

import pandas as pd
import os
import subprocess
import re


def get_package_and_entry(app_name):
    pkg_map = {"AnkiDroid": "com.ichi2.anki", "Amaze": "com.amaze.filemanager"}
    acti_map = {"AnkiDroid": ".IntentHandler", "Amaze": ".ui.activities.MainActivity"}
    return pkg_map[app_name], acti_map[app_name]


def get_crash_info(app_name, crash_idx):
    crash_data = pd.read_csv("../Data/Test/" + app_name + ".csv")
    line = crash_data.loc[crash_idx]
    crash_info = {"crash_desc": line["crash"], "crash_page": line["page_name"], "xml_path": line["xml_path"]}
    return crash_info


def get_crash_info_recdroid(app_idx):
    crash_data = pd.read_csv("../Data/Test/ReCDroid.csv")
    crash_data = crash_data.fillna("")
    line = crash_data.loc[app_idx]
    crash_info = {"crash_desc": line["crash"], "crash_page": line["page_name"], "xml_path": line["xml_path"],
                  "app_pkg": line["app_pkg"].strip(), "app_acti": line["app_acti"].strip(), "app_name": line["app"]}
    print(crash_info)
    return crash_info


def get_crash_info_recdroid2(app_idx):
    crash_data = pd.read_csv("../Data/Test/ReCDroid2.csv")
    crash_data = crash_data.fillna("")
    line = crash_data.loc[app_idx]
    crash_info = {"crash_desc": line["crash"], "crash_page": line["page_name"], "xml_path": line["xml_path"],
                  "app_pkg": line["app_pkg"].strip(), "app_acti": line["app_acti"].strip(), "app_name": line["app"]}
    print(crash_info)
    return crash_info


def get_crash_info_recdroid_all(app_idx):
    crash_data = pd.read_csv("../Data/Test/ReCDroid_all.csv")
    crash_data = crash_data.fillna("")
    line = crash_data.loc[app_idx]
    crash_info = {"crash_desc": line["crash"], "crash_page": "", "xml_path": "", "app_pkg": line["app_pkg"].strip(),
                  "app_acti": line["app_acti"].strip(), "app_name": line["app"]}
    input_cont = load_input(str(line["app"]))
    crash_info.setdefault("input_cont", input_cont)
    return crash_info


def get_crash_info_andror2(app_idx):
    crash_data = pd.read_csv("../Data/Test/AndroR2.csv")
    crash_data = crash_data.fillna("")
    line = crash_data.loc[app_idx]
    crash_info = {"crash_desc": line["crash"], "crash_page": line["page_name"], "xml_path": line["xml_path"],
                  "app_pkg": line["app_pkg"].strip(), "app_acti": line["app_acti"].strip(), "app_name": line["app"]}
    print(crash_info)
    return crash_info


def get_crash_info_review(app_idx):
    crash_data = pd.read_csv("../Data/Test/app_reviews.csv")
    crash_data = crash_data.fillna("")
    line = crash_data.loc[app_idx]
    crash_info = {"crash_desc": line["crash"], "app_pkg": line["app_pkg"].strip(), "app_acti": line["app_acti"].strip(),
                  "app_name": line["app"], "app_path": line["app_path"]}
    print(crash_info)
    return crash_info


def get_crash_info_andror2_all(app_idx):
    crash_data = pd.read_csv("../Data/Test/AndroR2_all.csv")
    crash_data = crash_data.fillna("")
    line = crash_data.loc[app_idx]
    crash_info = {"crash_desc": line["crash"], "crash_page": "", "xml_path": "", "app_pkg": line["app_pkg"].strip(),
                  "app_acti": line["app_acti"].strip(), "app_name": str(line["app"])}
    input_cont = load_input(str(line["app"]))
    crash_info.setdefault("input_cont", input_cont)
    return crash_info


def get_crash_info_mydata_all(app_idx):
    crash_data = pd.read_csv("../Data/Test/mydata_all.csv")
    crash_data = crash_data.fillna("")
    line = crash_data.loc[app_idx]
    crash_info = {"crash_desc": line["crash"], "crash_page": "", "xml_path": "", "app_pkg": line["app_pkg"].strip(),
                  "app_acti": line["app_acti"].strip(), "app_name": str(line["app"])}
    input_cont = load_input(str(line["app"]))
    crash_info.setdefault("input_cont", input_cont)
    return crash_info


def get_crash_info_mydata(app_idx):
    crash_data = pd.read_csv("../Data/Test/mydata.csv")
    crash_data = crash_data.fillna("")
    line = crash_data.loc[app_idx]
    crash_info = {"crash_desc": line["crash"], "crash_page": line["page_name"], "xml_path": line["xml_path"],
                  "app_pkg": line["app_pkg"].strip(), "app_acti": line["app_acti"].strip(), "app_name": line["app"]}
    print(crash_info)
    return crash_info


def get_crash_info_mydata2(app_idx):
    crash_data = pd.read_csv("../Data/Test/mydata2.csv")
    crash_data = crash_data.fillna("")
    line = crash_data.loc[app_idx]
    crash_info = {"crash_desc": line["crash"], "crash_page": line["page_name"], "xml_path": line["xml_path"],
                  "app_pkg": line["app_pkg"].strip(), "app_acti": line["app_acti"].strip(), "app_name": line["app"]}
    print(crash_info)
    return crash_info


def install_app(app_pkg: str, app_name: str, app_dir="ReCDroid"):
    app_path = "../Data/Apps/" + app_dir + "/" + app_name
    uninstall_cmd = "adb -s emulator-5554 uninstall " + app_pkg
    os.system(uninstall_cmd)
    install_cmd = "adb -s emulator-5554 install -g " + app_path
    # install_cmd = "adb -s emulator-5554 install " + app_path
    os.system(install_cmd)
    if app_pkg == "com.fsck.k9.debug":
        print("%%% push com.fsck.k9.debug")
        push_cmd = "adb -s emulator-5554 root | adb -s emulator-5554 remount | adb  -s emulator-5554 push ../Data/Temp/com.fsck.k9.debug/ /data/data/"
        os.system(push_cmd)



def perform_logcat():
    os.system("adb -s emulator-5554 logcat -c")
    log_out = open("../Data/Temp/logcat/log_out.txt", "wb")
    log_err = open("../Data/Temp/logcat/log_err.txt", "wb")
    log_proc = subprocess.Popen("adb -s emulator-5554 logcat *:E", stdout=log_out, stderr=log_err, shell=True)


def check_crash():
    # print("checking crash")
    log_file = open("../Data/Temp/logcat/log_out.txt", "r", encoding="UTF-8", errors="ignore")
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


def make_input():
    # open("../Data/Test/ReCDroid_all.csv")
    df = pd.read_csv("../Data/Test/mydata_all.csv")
    for _, row in df.iterrows():
        app = str(row["app"])
        f = open("../Data/Temp/input/" + app + ".json", "w")


def load_input(app_name: str):
    content = open("../Data/Temp/input/" + app_name + ".json", "r").read()
    if len(content.strip()) == 0:
        return {}
    else:
        return json.loads(content)


if __name__ == '__main__':
    # get_crash_info("AnkiDroid", 0)
    # print(get_crash_info_recdroid(0))
    # make_input()
    print(load_input("10.olam1__s"))
