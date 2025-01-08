from tool.layout_parser import parse_layout_appium
from tool.environment import EmulatorEnv
from tool.memory import Memory
from tool.utils import check_is_confirm_button, check_is_back
from my_utils.str_utils import get_activity_name, action_key_to_desc
import logging

logger = logging.getLogger(__name__)
logger.setLevel(1)


class Observer:
    def __init__(self, env: EmulatorEnv, memory: Memory, app_info: dict):
        self.env = env
        self.memory = memory
        self.app_pkg = app_info["app_pkg"]
        self.crash_desc = app_info["crash_desc"]

    def observe(self, add_visit_time=False):
        latest_action = self.memory.get_latest_action()
        # add 1115 input not add visit time
        if latest_action != None and "Input[" in latest_action["action_id"]:
            add_visit_time = False
        page_info = self.get_page_info()
        if page_info["page_type"] == "out of app" or page_info["page_type"] == "empty page":
            return {"page_prompt": "NA", "page_id": page_info["page_type"], "page_info": page_info,
                    "idx2action": {1: "Back to previous page"}, "full_page_info": {}}
        page_id = self.memory.get_page_id(page_info, add_visit_time=add_visit_time)
        full_page_info = self.memory.get_page_info(page_id)

        self.log_current_page(page_id, full_page_info)
        available_actions = self.memory.get_available_actions(page_id)
        page_prompt, idx2action = self.get_page_prompt(full_page_info, available_actions, latest_action)
        return {"page_prompt": page_prompt, "page_id": page_id, "page_info": page_info, "idx2action": idx2action,
                "full_page_info": full_page_info}

    def get_page_info(self):
        screen_info = self.env.get_current_screen()
        if self.app_pkg != screen_info["package"]:
            print("### activity out of app:", screen_info["package"], screen_info["activity"])
            if "CameraActivity" in screen_info["activity"]:
                self.env.system_back()
            return {"page_type": "out of app"}
        page_info = parse_layout_appium(screen_info["xml_path"])
        if len(page_info.keys()) == 0:
            print("### empty page:", screen_info["activity"])
            return {"page_type": "empty page"}
        activity_name = get_activity_name(screen_info["activity"])
        # if "page_title" in page_info.keys() and len(page_info["page_title"]) > 0:
        #     page_name = page_info["page_title"]
        # else:
        #     if page_info["page_type"] == "dialog":
        #         page_name = "dialog of " + activity_name
        #     elif page_info["page_type"] == "option menu":
        #         page_name = "menu of " + activity_name
        #     else:
        #         page_name = activity_name
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
        page_info.setdefault("activity", screen_info["activity"].split("/")[-1].split(".")[-1])
        page_info.setdefault("page_xml", screen_info["xml_path"])
        page_info.setdefault("page_img", screen_info["img_path"])
        return page_info

    def get_page_prompt(self, full_page_info: dict, available_actions: dict, latest_action: dict):
        page_visit_times = full_page_info["visit_times"]
        page_name = full_page_info["page_name"]
        if latest_action == None:
            begin_prompt = "You are now on the page called {}, which is a newly explored page. ".format(page_name)
        else:
            action_desc = action_key_to_desc(latest_action["action_id"])
            if latest_action["src_page"] == latest_action["dst_page"]:
                begin_prompt = "In the previous step, you {}, but still kept in the \"{}\" page, ".format(action_desc,
                                                                                                          page_name)
            else:
                begin_prompt = "In the previous step, you {}, and navigated to the \"{}\" page, ".format(action_desc,
                                                                                                         page_name)
            if page_visit_times > 1:
                begin_prompt = begin_prompt + "which you have visited {} times. ".format(page_visit_times)
            else:
                begin_prompt = begin_prompt + "which is a newly explored page. "
        # old show_action_list
        # show_action_list = []
        # for action_key, action_info in available_actions.items():
        #     action_dst_page = action_info["dst_page_name"]
        #     if action_dst_page == "out of app" or action_dst_page == "empty page":
        #         continue
        #     if action_key == "Back to previous page" and page_visit_times <= 3:
        #         continue
        #     show_action_list.append(action_key)
        show_action_list = self.get_show_actions(full_page_info, available_actions)
        action_str_list = []
        idx2action = {}
        for show_idx, action_key in enumerate(show_action_list):
            action_info = available_actions[action_key]
            action_str = "(" + str(show_idx + 1) + ") " + action_key + ": "
            idx2action.setdefault(show_idx + 1, action_key)
            action_visit_times = action_info["visit_times"]
            action_dst_page = action_info["dst_page_name"]
            if "Input[" in action_key:
                if action_key not in self.memory.input_memory["has_inputted"]:
                    action_str = action_str + "You haven't filled this input box yet, please first fill it in."
                else:
                    action_str = action_str + "You have filled this input box. No need to select this action again."
            elif action_dst_page == "unknown":
                action_str = action_str + "You haven't performed the action yet."
            else:
                if action_visit_times > 0:
                    action_str = action_str + "You perform the action {} times, and the action goes to page \"{}\"".format(
                        action_visit_times, action_dst_page)
                else:
                    action_str = action_str + "You haven't performed the action yet, and the action goes to page \"{}\"".format(
                        action_dst_page)
            action_str_list.append(action_str)
        action_size = len(action_str_list)
        action_prompt = "On \"{}\" page, you need to choose one of the following {} actions to perform:\n".format(
            page_name, action_size)
        action_prompt += "\n".join(action_str_list)
        page_prompt = begin_prompt + action_prompt
        return page_prompt, idx2action

    def log_current_page(self, page_id: str, full_page_info: dict):
        logger.info("page_id: " + page_id)
        logger.info("page name: " + full_page_info["page_name"])
        logger.info("page actions: " + ", ".join(list(full_page_info["actions"].keys())))

    def get_show_actions(self, full_page_info: dict, available_actions: dict):
        # basic flit
        # show_action_list = []
        # page_visit_times = full_page_info["visit_times"]
        # for action_key, action_info in available_actions.items():
        #     action_dst_page = action_info["dst_page_name"]
        #     if action_dst_page == "out of app" or action_dst_page == "empty page":
        #         continue
        #     if action_key == "Back to previous page" and page_visit_times <= 3:
        #         continue
        #     show_action_list.append(action_key)
        # return show_action_list

        # advance flit
        show_action_list = []
        has_edittext = False
        has_confirm = False
        activity_name = full_page_info["activity"].lower()
        page_name = full_page_info["page_name"].lower()
        is_intro = "intro" in activity_name or "tutorial" in activity_name
        is_setting = ("setting" in activity_name or "preference" in activity_name) and ("dialog" not in page_name)
        # is_setting = False
        is_picker = "picker" in activity_name
        for action_key, action_info in available_actions.items():
            if "Input[" in action_key and action_key not in self.memory.input_memory["has_inputted"]:
                has_edittext = True
            if check_is_confirm_button(action_key):
                has_confirm = True
        # not_show_back = (full_page_info["visit_times"] <= 3 or has_confirm or is_intro) and not (
        #             is_setting or is_picker)
        not_show_back = (full_page_info["visit_times"] <= 3 or has_confirm or is_intro) and not (is_setting or is_picker)
        # not_show_back = not_show_back and full_page_info["visit_times"] <= 6 and "back " not in self.crash_desc.lower()
        not_show_back = not_show_back and full_page_info["visit_times"] <= 6
        log_str = "has_edittext:{}, has_confirm:{}, not_show_back:{}".format(has_edittext, has_confirm, not_show_back)
        logger.info(log_str)
        for action_key, action_info in available_actions.items():
            action_dst_page = action_info["dst_page_name"]
            if "Input[" in action_key and action_key in self.memory.input_memory["has_inputted"]:
                continue
            if action_dst_page == "out of app" or action_dst_page == "empty page":
                continue
            if action_key == "Back to previous page" and not_show_back:
                continue
            if check_is_back(action_key) and not_show_back:
                continue
            if check_is_back(action_key) and has_confirm and "back " not in self.crash_desc.lower():
                continue
            if check_is_confirm_button(action_key) and has_edittext:
                continue
            if action_info["visit_times"] >= 10:
                continue
            show_action_list.append(action_key)
        if len(show_action_list) <= 1 and not is_intro and ("dialog" not in page_name):
        # if len(show_action_list) <= 1 and not is_intro and not has_edittext:
            show_action_list = list(available_actions.keys())
        interest_words = ["new", "create", "add", "preference", "option", "next", "start", "ok", "enter", "show",
                          "more", "main", "menu", "correct", "select"]
        sort_action_list = []
        for action_key in show_action_list:
            score = 0
            for word in interest_words:
                if word in action_key.lower():
                    score = 1
                    break
            if "Input[" in action_key:
                score += 0.1
            sort_action_list.append([action_key, score])
        sort_action_list.sort(key=lambda x: x[1], reverse=True)
        show_action_list = [t[0] for t in sort_action_list]
        return show_action_list
