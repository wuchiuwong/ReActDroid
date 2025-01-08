import time

from tool.memory import Memory
from tool.environment import EmulatorEnv
from tool.observe import Observer
import logging
logger = logging.getLogger(__name__)
logger.setLevel(1)

class Action:
    def __init__(self, env: EmulatorEnv, memory: Memory, observer: Observer):
        self.memory = memory
        self.env = env
        self.observer = observer

    def perform_action(self, page_id: str, action_key: str):
        logger.info("Perform action: " + action_key)
        if page_id != self.memory.input_memory["page_id"]:
            self.memory.input_memory["page_id"] = page_id
            self.memory.input_memory["has_inputted"] = set()
        if action_key == "rotate":
            self.env.rotate_screen()
            return
        action_info = self.memory.get_action(page_id, action_key)
        if action_key == "Back to previous page":
            before_page_info = self.observer.get_page_info()
            before_page_id = self.memory.get_page_id(before_page_info)
            self.env.perform_action({"type": "system_back", "xpath": ""})
            after_page_info = self.observer.get_page_info()
            if len(after_page_info.keys()) > 3:
                after_page_id = self.memory.get_page_id(after_page_info)
                if after_page_id == before_page_id:
                    print("try back one more time!")
                    self.env.perform_action({"type": "system_back", "xpath": ""})
        else:
            # print(action_key, action_info["scroll"])
            if action_info["scroll"] >= 0:
                self.env.click_view_scroll(action_info["name"])
            else:
                self.env.perform_action({"type": action_key.split("[")[0], "xpath": action_info["xpath"]})
            if action_key.split("[")[0] == "Input":
                self.memory.input_memory["has_inputted"].add(action_key)
        action_info["visit_times"] += 1
        if self.is_click_login(action_key):
            time.sleep(5)
        # time.sleep(0.3)


    def is_click_login(self, action_key):
        if "Click[" in action_key and ("login" in action_key.lower() or "log in" in action_key.lower()):
            return True
        return False


if __name__ == '__main__':
    a = Action()
    a.list_action("../Data/Temp/cur_screen.xml")