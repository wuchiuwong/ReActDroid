import re

from llm.model import chatgpt
from tool.memory import Memory
from llm.prompt import *
import logging

logger = logging.getLogger(__name__)
logger.setLevel(1)


class Chat:
    def __init__(self, memory: Memory, crash_info: dict):
        self.memory = memory
        self.init_prompt = init_prompt
        self.crash_info = crash_info
        self.crash_desc_prompt = crash_desc_prompt.format(crash_info["crash_desc"])

    def choose_action(self, observe_res: dict, all_history=True):
        page_id = observe_res["page_id"]
        page_prompt = observe_res["page_prompt"]
        page_name = observe_res["page_info"]["page_name"]
        idx2action = observe_res["idx2action"]
        hint_prompt = self.generate_hint(page_id)
        if all_history:
            observation_prompt = "<Observation>: " + page_prompt + hint_prompt
            messages = [{"role": "system", "content": self.init_prompt},
                        {"role": "user", "content": self.crash_desc_prompt}]
            for chat_his in self.memory.chat_memory[-5:]:
                messages.append({"role": "user", "content": chat_his["observation"]})
                messages.append({"role": "assistant", "content": chat_his["response"]})
            messages.append({"role": "user", "content": observation_prompt})
        else:
            observation_prompt = "<Observation>:" + page_prompt + hint_prompt
            messages = [{"role": "system", "content": self.init_prompt},
                        {"role": "user", "content": self.crash_desc_prompt + "\n" + observation_prompt}]
        # response = chatgpt(messages)
        # idx2action = self.memory.get_idx2action(page_id)
        # choose_result = self.parse_response(response, idx2action)
        response, choose_result = self.perform_chat(messages, idx2action)
        cur_chat_memory = {"messages": messages, "response": response, "choose_result": choose_result,
                           "observation": observation_prompt}
        self.memory.chat_memory.append(cur_chat_memory)
        return choose_result


    def perform_chat(self, messages: list, idx2action: dict):
        try_times = 1
        while try_times <= 3:
            try_times += 1
            response = chatgpt(messages)
            choose_result = self.parse_response(response, idx2action)
            if len(choose_result.keys()) == 2:
                return response, choose_result
            print("### try chat again！times:", try_times)
        print("### max retry!")
        response = "<Thought>: I should try " + str(idx2action[1]) + "\n<Action>: 1"
        choose_result = {}
        choose_result.setdefault("thought", "I should try " + str(idx2action[1]))
        choose_result.setdefault("action", idx2action[1])
        return response, choose_result





    def parse_response(self, response: str, idx2action: dict):
        choose_result = {}
        for line in response.split("\n"):
            if ":" not in line:
                continue
            if "<Thought>" in line:
                thought_content = line.split(":")[-1].split("<")[0].strip()
                choose_result.setdefault("thought", thought_content)
            if "<Action>" in line:
                action_content = line.split("<Action>")[-1].split("<")[0].strip()
                action_idx = re.findall("\d+", action_content)
                if len(action_idx) > 0:
                    choose_action_idx = int(action_idx[0])
                    if choose_action_idx in idx2action.keys():
                        choose_result.setdefault("action", idx2action[choose_action_idx])
                    else:
                        print("### choose idx not in range:", choose_action_idx, ",", idx2action.keys())
            if "action" in choose_result.keys() and "thought" in choose_result.keys():
                return choose_result
        print("### not valid response")
        print(response)
        return {}
        # choose_result.setdefault("thought", "Not valid response")
        # choose_result.setdefault("action", "Back to previous page")
        # return choose_result

    def generate_hint(self, cur_page_id):
        crash_page_id = self.crash_info["crash_page_id"]
        hint_prompt = "\nHint:"
        if cur_page_id == crash_page_id:
            hint_prompt = hint_action_prompt.format(self.crash_info["crash_desc"])
            # input_boxs = []
            # for action_key in self.memory.get_available_actions(crash_page_id).keys():
            #     if "Input[" in action_key and action_key not in self.memory.input_memory["has_inputted"]:
            #         input_boxs.append(action_key)
            # if len(input_boxs) > 0:
            #     input_box_str = ", ".join(input_boxs)
            #     hint_prompt += " Note that you may first need to fill in all of the input boxs ({}).".format(input_box_str)
        elif crash_page_id != "unknown":
            next_page_id = self.memory.stg.get_closest_previous_page(crash_page_id, cur_page_id)
            next_page_info = self.memory.get_page_info(next_page_id)
            cur_page_info = self.memory.get_page_info(cur_page_id)
            cur_visit_time = cur_page_info["visit_times"]
            next_page_name = next_page_info["page_name"]
            hint_prompt = hint_page_prompt.format(next_page_name)
        # if "delete" in self.crash_info["crash_desc"].lower():
        #     hint_prompt += " If you want to delete something, may be you should try to select something by long pressing."
        # input_boxs = []
        # for action_key in self.memory.get_available_actions(cur_page_id).keys():
        #     if "Input[" in action_key and action_key not in self.memory.input_memory["has_inputted"]:
        #         input_boxs.append(action_key)
        # if len(input_boxs) > 0 and cur_page_id != crash_page_id:
        #     input_box_str = ", ".join(input_boxs)
        #     hint_prompt += " There are input boxes({}) on the current page, maybe you should first fill all of them in.".format(input_box_str)
        cur_page_info = self.memory.get_page_info(cur_page_id)
        cur_visit_time = cur_page_info["visit_times"]
        if cur_visit_time >= 5:
            unexplored_actions = []
            fex_explored_actions = []
            for action_key, action_info in self.memory.get_available_actions(cur_page_id).items():
                if action_info["visit_times"] == 0:
                    unexplored_actions.append(action_key)
                if action_info["visit_times"] <= 3:
                    fex_explored_actions.append(action_key)
            if len(unexplored_actions) == 0 and len(fex_explored_actions) == 0:
                hint_prompt += " It looks like you've explored this page sufficiently but made no progress, " + \
                               "so you probably should go back to the previous page to explore other paths."
            else:
                hint_prompt += " It looks like the page has been visited several times with no progress, "
                if len(unexplored_actions) > 0:
                    hint_prompt += "you may need to try some actions that have not been performed before ({})".format(
                                   ", ".join(unexplored_actions))
                else:
                    hint_prompt += "you may need to try some actions that have only been performed a few times ({})".format(
                        ", ".join(fex_explored_actions))
                hint_prompt += " or go back to previous page."
        if len(hint_prompt) < 10:
            return ""
        else:
            return hint_prompt

if __name__ == '__main__':
    a = "gwdiohnaiowhdw"
    print(re.findall("\d+", a))