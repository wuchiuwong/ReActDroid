import sys
sys.path.append("..")
from tool.action import Action
from tool.environment import EmulatorEnv
from tool.memory import Memory
from tool.observe import Observer
from tool.process_static_analysis import process_fax_res
from llm.chat import Chat
from predict_page.predict_crash_page import predict
import time
from main.utils import *
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s[%(name)s:%(lineno)s]: %(message)s')


class Main:
    def __init__(self):
        app_idx = 32
        crash_info = get_crash_info_recdroid_all(app_idx)
        # input_cont = {"email": "lu@gml.com", "pass": "12331986"}
        # input_cont = {"email": "lu@gml.com", "pass": "12331986"}
        # input_cont = {"name": "", "pass": ""}
        # input_cont = {"all": "1234"}
        # crash_info.setdefault("input_cont", input_cont)
        install_app(crash_info["app_pkg"], crash_info["app_name"] + ".apk")
        perform_logcat()
        self.env = EmulatorEnv(crash_info)
        self.memory = Memory(crash_info, self.env)
        fax_res = process_fax_res("../Data/FaxRes/" + crash_info["app_name"], self.memory, crash_info)
        predict_res = predict(crash_info["app_name"], crash_info["crash_desc"])
        if len(predict_res.keys()) > 0:
            predict_crash_page_id = predict_res["crash_page_id"]
            confidence = predict_res["Confidence"]
            if confidence == 5:
                crash_info["crash_page_id"] = predict_crash_page_id
                # print("set crash_page_id:", predict_crash_page_id)
        self.observer = Observer(self.env, self.memory, crash_info)
        self.action = Action(self.env, self.memory, self.observer)
        self.chat = Chat(self.memory, crash_info)

    def step(self):
        observe_res = self.observer.observe(add_visit_time=True)
        # page_prompt = observe_res["page_prompt"]
        page_id = observe_res["page_id"]
        choose_result = self.chat.choose_action(observe_res)
        choose_action_key = choose_result["action"]
        self.action.perform_action(page_id, choose_action_key)
        dst_observe = self.observer.observe(add_visit_time=False)
        dst_page = dst_observe["page_id"]
        self.memory.update_action(page_id, choose_action_key, dst_page)
        if dst_observe["page_id"] == "out of app" or dst_observe["page_id"] == "empty page":
            self.env.relaunch_app()
        elif choose_action_key != "Back to previous page":
            self.memory.stg.update_previous_page(dst_page, page_id)

    def run(self):
        time.sleep(3)
        start_time = time.time()
        for i in range(10000):
            logging.info("Step " + str(i + 1))
            self.step()
            if check_crash():
                break
        end_time = time.time()
        print("Reproducing time:", end_time - start_time)


if __name__ == '__main__':
    Main().run()
