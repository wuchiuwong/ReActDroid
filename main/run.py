import logging
from tool.action import Action
from tool.environment import EmulatorEnv
from tool.memory import Memory
from tool.observe import Observer
from tool.process_static_analysis import process_fax_res
from llm.chat import Chat
import time
from main.utils import *
import logging

class Main:
    def __init__(self):
        # app_pkg = "com.ichi2.anki"
        # app_acti = ".IntentHandler"
        app_name = "Amaze"
        crash_idx = 1
        app_pkg, app_acti = get_package_and_entry(app_name)
        crash_info = get_crash_info(app_name, crash_idx)
        app_info = {"app_pkg": app_pkg, "app_acti": app_acti, "app_name": app_name}
        self.env = EmulatorEnv(app_info)
        self.memory = Memory(app_info, self.env)
        process_fax_res("../Data/FaxRes/" + app_name, self.memory, crash_info)
        self.observer = Observer(self.env, self.memory, app_info)
        self.action = Action(self.env, self.memory)
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
            time.sleep(2)
        elif choose_action_key != "Back to previous page":
            self.memory.stg.update_previous_page(dst_page, page_id)

    def run(self):
        time.sleep(1)
        for i in range(100):
            logging.info("Step " + str(i + 1))
            self.step()

if __name__ == '__main__':
    Main().run()