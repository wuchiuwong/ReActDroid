import shutil

from appium import webdriver
import time
from appium.webdriver.common.mobileby import MobileBy
from appium.webdriver.common.touch_action import TouchAction
import os
import re
import logging
from tool.utils import clean_resource_id, check_crash, get_input_content, check_crash_strict
from tool.layout_parser import parse_layout_appium


class EmulatorEnv:
    def __init__(self, app_info: dict):
        self.init_appium(app_info)
        if "input_cont" in app_info.keys():
            self.input_cont = app_info["input_cont"]
        else:
            self.input_cont = {}

    def init_appium(self, app_info: dict):
        desired_caps = {}
        desired_caps['platformName'] = 'Android'
        desired_caps['platformVersion'] = '7.0'
        # desired_caps['platformVersion'] = '5.0'
        # desired_caps['deviceName'] = '127.0.0.1:5554'
        desired_caps['deviceName'] = 'emulator-5554'
        desired_caps['appPackage'] = app_info["app_pkg"]
        self.app_pkg = app_info["app_pkg"]
        desired_caps['appActivity'] = app_info["app_acti"]
        self.app_acti = app_info["app_acti"]
        self.sort_relaunch = app_info.get("sort_relaunch", False)
        desired_caps['noReset'] = True
        # desired_caps['dontStopAppOnReset'] = "True"
        desired_caps['autoGrantPermissions'] = True
        desired_caps['newCommandTimeout'] = 6000
        desired_caps['automationName'] = 'UiAutomator2'

        # desired_caps['platformName'] = 'Android'
        # desired_caps['platformVersion'] = '6.0'
        # desired_caps['deviceName'] = '127.0.0.1:7555'
        # desired_caps['appPackage'] = app_info["app_pkg"]
        # desired_caps['appActivity'] = app_info["app_acti"]
        # desired_caps['noReset'] = True
        # desired_caps['autoGrantPermissions'] = True
        # desired_caps['newCommandTimeout'] = 6000
        # desired_caps['automationName'] = 'UiAutomator2'
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
        self.driver.orientation = "PORTRAIT"
        self.driver.update_settings({'waitForIdleTimeout': 100})

    def get_current_screen(self):
        temp_img_path = "../Data/Temp/cur_screen.png"
        temp_xml_path = "../Data/Temp/cur_screen.xml"
        backup_path = "../Data/Temp/backup/" + time.strftime("%m-%d_%H-%M-%S", time.localtime())
        shutil.copy(temp_img_path, backup_path + ".png")
        shutil.copy(temp_xml_path, backup_path + ".xml")
        try:
            self.driver.get_screenshot_as_file(temp_img_path)
        except Exception as e:
            # print(e)
            f = open(temp_img_path, "w")
        screen_xml = self.driver.page_source
        with open(temp_xml_path, "w", encoding="UTF-8") as f:
            f.write(screen_xml)
            f.close()
        cur_screen_info = {"activity": self.driver.current_activity, "xml_path": temp_xml_path,
                           "img_path": temp_img_path, "package": self.driver.current_package, "page_source": screen_xml}
        return cur_screen_info

    def perform_action(self, tgt_action: dict):
        if tgt_action["type"] == "Click":
            return self.click_view_by_xpath(tgt_action["xpath"])
        elif tgt_action["type"] == "Long press":
            return self.long_click_view_by_xpath(tgt_action["xpath"])
        elif tgt_action["type"] == "Input":
            return self.send_view_text(tgt_action["xpath"], "HelloWorld!")
        elif tgt_action["type"] == "system_back":
            self.system_back()
            # self.driver.press_keycode(4)
            return True
        elif tgt_action["type"] == "fill_info":
            return self.fill_and_confirm(tgt_action["xpath"])
        else:
            logging.info("undefine action")
        return False

    def get_view_by_xpath(self, xpath: str):
        ele = self.driver.find_element(MobileBy.XPATH, xpath)
        return ele

    def click_view_by_xpath(self, view_xpath: str):
        try:
            ele = self.get_view_by_xpath(view_xpath)
            ele.click()
            time.sleep(0.2)
            return True
        except Exception as e:
            print(e)
            return False

    def long_click_view_by_xpath(self, view_xpath: str):
        try:
            ele = self.get_view_by_xpath(view_xpath)
            TouchAction(self.driver).long_press(ele).perform()
            time.sleep(0.2)
            return True
        except Exception as e:
            print(e)
            return False

    def send_view_text(self, xpath, default_input="HelloWorld!"):
        cur_time = time.time()
        try:
            ele = self.driver.find_element(MobileBy.XPATH, xpath)
        except Exception as e:
            print(xpath)
            print(e)
            return False
        ele_id = ele.get_attribute("resourceId")
        if ele_id == None or type(ele_id) != type("a"):
            ele_id = "none"
        else:
            ele_id = ele_id.split("/")[-1]
        ele_id = clean_resource_id(ele_id)
        default_cont = ele.text
        if ":" in default_cont and ele_id == "time":
            return True
        if "/" in default_cont and ele_id == "date":
            return True
        # content = get_input_content(ele_id, default_cont, self.app_pkg, default_input)

        cur_time = time.time()
        content = get_input_content(ele_id, default_cont, default_input, self.input_cont)
        # content = default_input
        is_password = "pass" in ele_id.split() or "password" in ele_id.split()
        is_search = "search" in ele_id.split()
        if "\'" in content or "\"" in content or " " in content:
            logging.info("use appium send key!")
            ele.send_keys(content)
        else:
            logging.info("use adb cmd!")
            ele.click()
            move_cmd = "adb -s emulator-5554 shell input keyevent KEYCODE_MOVE_END"
            # move_cmd = "adb shell input keyevent KEYCODE_MOVE_END"
            os.system(move_cmd)
            if not is_password:
                ori_content_len = len(ele.text) + 1
            else:
                ori_content_len = 20
            del_cmd = "adb -s emulator-5554 shell input keyevent" + " KEYCODE_DEL" * ori_content_len
            # del_cmd = "adb shell input keyevent" + " KEYCODE_DEL" * ori_content_len
            os.system(del_cmd)
            input_cmd = "adb -s emulator-5554 shell input text \"" + content + "\""
            # input_cmd = "adb shell input text \"" + content + "\""
            os.system(input_cmd)
            time.sleep(0.2)
        if is_search:
            if self.app_pkg == "com.amaze.filemanager":
                enter_cmd = "adb -s emulator-5554 shell input tap 1000 1700"
                print(enter_cmd)
                os.system(enter_cmd)
            else:
                enter_cmd = "adb -s emulator-5554 shell input keyevent KEYCODE_ENTER"
                # enter_cmd = "adb shell input keyevent KEYCODE_ENTER"
                os.system(enter_cmd)
        cur_time = time.time()
        return True

    def system_back(self):
        # before_state = self.get_cur_state()
        self.driver.press_keycode(4)
        time.sleep(0.3)
        # after_state = self.get_cur_state()
        # if after_state == before_state:
        #     logging.info("try back one more time!")
        #     self.driver.press_keycode(4)
        #     time.sleep(0.2)

    def relaunch_app(self):
        if self.sort_relaunch:
            self.launch_by_cmd()
        else:
            self.driver.launch_app()
            time.sleep(2)

    # def fill_and_confirm(self, view_xpath, input_content="HelloWorld!"):
    #     try:
    #         screen_info = self.get_screen_info()
    #         edittext_xpaths = get_edittexts_on_page(screen_info["page_source"])
    #         for edittext_xpath in edittext_xpaths:
    #             self.send_view_text(edittext_xpath, input_content)
    #         ele = self.get_view_by_xpath(view_xpath)
    #         ele.click()
    #         time.sleep(1)
    #         return True
    #     except Exception as e:
    #         print(e)
    #         return False

    def rotate_screen(self):
        try:
            self.driver.orientation = "LANDSCAPE"
            time.sleep(0.8)
            # if check_crash():
            #     return
            self.driver.orientation = "PORTRAIT"
            time.sleep(0.8)
        except Exception as e:
            print(e)
            return

    def scroll_down(self):
        self.driver.swipe(1000, 1300, 1000, 600, 500)
        time.sleep(0.2)

    def scroll_up(self):
        self.driver.swipe(1000, 600, 1000, 1300, 500)
        time.sleep(0.2)

    def click_view_scroll(self, view_text: str):
        # print("### click_view_scroll")
        for _ in range(4):
            self.scroll_up()
        try_times = 1
        while try_times <= 4:
            screen_info = self.get_current_screen()
            if self.app_pkg != screen_info["package"]:
                # print("### activity out of app:", screen_info["package"], screen_info["activity"])
                return False
            # old: click view by text
            # print("target view_text:", view_text)
            # page_info = parse_layout_appium(screen_info["xml_path"])
            # page_text = page_info["all_texts"]
            # for _, text_info in page_text.items():
            #     # print(text_info["text"])
            #     if view_text == text_info["text"]:
            #         click_x = (text_info["bound"][0][0] + text_info["bound"][1][0]) // 2
            #         click_y = (text_info["bound"][0][1] + text_info["bound"][1][1]) // 2
            #         self.driver.tap([(click_x, click_y)])
            #         return True
            # try_times += 1
            # new: click view by key
            page_info = parse_layout_appium(screen_info["xml_path"])
            page_actions = page_info["actions"]
            for action_key, action_info in page_actions.items():
                # print(text_info["text"])
                if view_text.lower() == action_info["name"].lower():
                    self.click_view_by_xpath(action_info["xpath"])
                    return True
            try_times += 1
            self.scroll_down()
        return False


    def launch_by_cmd(self):
        launch_cmd = "adb -s emulator-5554 shell am start " + self.app_pkg + "/" + self.app_acti
        launch_p = os.popen(launch_cmd)
        launch_res = launch_p.read()
        time.sleep(1)


if __name__ == '__main__':
    app_info = {"app_pkg": "com.amaze.filemanager",
                "app_acti": ".activities.MainActivity"}
    e = EmulatorEnv(app_info)
    a = input("wait")
    # e.send_view_text(
    #     "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.EditText")
    e.get_current_screen()