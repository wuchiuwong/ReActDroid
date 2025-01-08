from my_utils.layout_utils import is_point_in_bound, get_bound_distance, get_bound_lou, get_bound_center
from my_utils.str_utils import process_xpath
import shutil
import os
from tool.environment import EmulatorEnv
from tool.layout_parser import parse_layout_appium


class Memory:
    def __init__(self, app_info: dict, env: EmulatorEnv):
        self.all_page_info = {}
        self.all_action_info = {}
        self.chat_memory = []
        self.action_record = []
        self.stg = STG()
        self.app_info = app_info
        self.app_pkg = app_info["app_pkg"]
        self.app_state_dir = "../Data/AppState/" + str(app_info["app_name"]) + "/"
        self.env = env
        self.input_memory = {"page_id": "", "has_inputted": set()}
        if not os.path.exists(self.app_state_dir):
            os.mkdir(self.app_state_dir)

    def get_page_id(self, in_page_info: dict, add_visit_time=False, init_by_static=False, do_update=True):
        for page_id, page_info in self.all_page_info.items():
            # if page_info["is_scrollable"]:
            #     print("### is_scrollable", page_id)
            if self.check_page_is_same(in_page_info, page_info):
                # if page_info["visit_times"] <= 0:
                #     # self.update_xpath(in_page_info, page_info, page_id)
                #     self.update_page_action(in_page_info, page_info, page_id)
                if page_info["init_by_static"] and do_update:
                    self.update_page_action(in_page_info, page_info, page_id)
                if add_visit_time:
                    page_info["visit_times"] += 1
                # if page_id != self.input_memory["page_id"]:
                #     self.input_memory["page_id"] = page_id
                #     self.input_memory["has_inputted"] = set()
                return page_id
        new_page_id = self.add_new_page(in_page_info, init_by_static)
        # self.input_memory["page_id"] = new_page_id
        # self.input_memory["has_inputted"] = set()
        return new_page_id

    def add_new_page(self, in_page_info: dict, init_by_static: bool):
        # init all_page_info
        in_page_info.setdefault("init_by_static", init_by_static)
        new_page_id = in_page_info["page_name"] + "#" + str(len(self.all_page_info.keys()))
        # print("add new_page_id start:", new_page_id)
        self.stg.previous_page_map.setdefault(new_page_id, [])
        in_page_info.setdefault("visit_times", 0)
        self.all_page_info.setdefault(new_page_id, in_page_info)
        # init all_action_info
        cur_action_infos = self.init_action_infos()
        # if in_page_info["is_scrollable"]:
        #     init_scroll = 0
        # else:
        #     init_scroll = -1
        for action_id, ori_info in in_page_info["actions"].items():
            action_idx = len(cur_action_infos.keys()) + 1
            if in_page_info["is_scrollable"] and ori_info["warp_in_scrollable"]:
                scroll_symbol = 0
            else:
                scroll_symbol = -1
            action_info = {"action_idx": action_idx, "visit_times": 0, "dst_page": "unknown", "name": ori_info["name"],
                           "bound": ori_info["bound"], "dst_page_name": "unknown", "xpath": ori_info["xpath"],
                           "scroll": scroll_symbol}
            cur_action_infos.setdefault(action_id, action_info)
        self.all_action_info.setdefault(new_page_id, cur_action_infos)
        shutil.copy(in_page_info["page_xml"], self.app_state_dir + new_page_id + ".xml")
        shutil.copy(in_page_info["page_img"], self.app_state_dir + new_page_id + ".png")
        # print("### is_scrollable:", in_page_info["is_scrollable"])
        if in_page_info["is_scrollable"] and not init_by_static and self.app_pkg != "com.amaze.filemanager":
            found_actions = in_page_info["actions"]
            # print("before add scroll", cur_action_infos.keys())
            scroll_times = 1
            while scroll_times <= 3:
                has_add = False
                self.env.scroll_down()
                new_screen_info = self.env.get_current_screen()
                new_page_info = parse_layout_appium(new_screen_info["xml_path"])
                for action_id, ori_info in new_page_info["actions"].items():
                    if action_id in found_actions.keys():
                        continue
                    # print("### add scroll action:", action_id)
                    has_add = True
                    found_actions.setdefault(action_id, ori_info)
                    action_idx = len(cur_action_infos.keys()) + 1
                    action_info = {"action_idx": action_idx, "visit_times": 0, "dst_page": "unknown",
                                   "scroll": scroll_times, "name": ori_info["name"], "bound": ori_info["bound"],
                                   "dst_page_name": "unknown", "xpath": ori_info["xpath"]}
                    cur_action_infos.setdefault(action_id, action_info)
                scroll_times += 1
                if not has_add:
                    break
        #     print("after add scroll", cur_action_infos.keys())
        # print("add new_page_id end:", new_page_id)
        return new_page_id

    def init_action_infos(self):
        back_action = {"xpath": "back", "visit_times": 0, "dst_page": "unknown", "dst_page_name": "unknown",
                       "action_idx": 1, "name": "Back to previous page", "bound": [[0, 0], [0, 0]], "scroll": 0}
        init_info = {"Back to previous page": back_action}
        return init_info

    def check_page_is_same(self, page_info1: dict, page_info2: dict, thres_action=0.9, thres_text=0.9):
        if "activity" not in page_info1.keys() or "activity" not in page_info2.keys():
            return False
        if page_info1["activity"] != page_info2["activity"]:
            # print(page_info1["activity"], page_info2["activity"])
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

    def check_page_is_same_old(self, page_info1: dict, page_info2: dict, thres_action=0.8, thres_text=0.9):
        if page_info1["page_name"] != page_info2["page_name"]:
            return False
        action_keys1 = set(page_info1["actions"])
        action_keys2 = set(page_info2["actions"])
        inter_action_size = len(action_keys1.intersection(action_keys2))
        union_action_size = len(action_keys1.union(action_keys2))
        if union_action_size > 0 and inter_action_size / union_action_size >= thres_action:
            text_set1 = set(page_info1["text_on_screen"])
            text_set2 = set(page_info2["text_on_screen"])
            inter_text_size = len(text_set1.intersection(text_set2))
            union_text_size = len(text_set1.intersection(text_set2))
            if union_text_size > 0 and inter_text_size / union_text_size >= thres_text:
                return True
            else:
                return False
        else:
            return False

    def get_action(self, page_id: str, action_id: str):
        assert page_id in self.all_action_info.keys()
        assert action_id in self.all_action_info[page_id]
        return self.all_action_info[page_id][action_id]

    def get_available_actions(self, page_id: str):
        assert page_id in self.all_action_info.keys()
        return self.all_action_info[page_id]

    def get_page_info(self, page_id: str):
        assert page_id in self.all_page_info.keys()
        return self.all_page_info[page_id]

    def get_idx2action(self, page_id: str):
        actions_on_page = self.all_action_info[page_id]
        idx2action = {}
        for action_key, action_info in actions_on_page.items():
            idx2action.setdefault(str(action_info["action_idx"]), action_key)
        return idx2action

    def update_action(self, src_page: str, action_id: str, dst_page: str):
        action_info = self.all_action_info[src_page][action_id]
        if action_id == "Back to previous page":
            if dst_page == "out of app" or dst_page == "empty page" or src_page == dst_page:
                action_info["dst_page"] = "out of app"
                action_info["dst_page_name"] = "out of app"
                dst_page_name = dst_page
            else:
                dst_page_name = self.all_page_info[dst_page]["page_name"]
                if action_info["dst_page"] == "unknown":
                    # dst_page_name = self.all_page_info[dst_page]["page_name"]
                    action_info["dst_page"] = dst_page
                    action_info["dst_page_name"] = dst_page_name
                elif action_info["dst_page"] != dst_page:
                    print("### dst conflict:, ori:", action_info["dst_page"], ", now:", dst_page)
                    # dst_page_name = self.all_page_info[dst_page]["page_name"]
                    action_info["dst_page"] = dst_page
                    action_info["dst_page_name"] = dst_page_name
        else:
            if dst_page == "out of app" or dst_page == "empty page":
                action_info["dst_page"] = dst_page
                action_info["dst_page_name"] = dst_page
                dst_page_name = dst_page
            else:
                dst_page_name = self.all_page_info[dst_page]["page_name"]
                if action_info["dst_page"] == "unknown":
                    # dst_page_name = self.all_page_info[dst_page]["page_name"]
                    action_info["dst_page"] = dst_page
                    action_info["dst_page_name"] = dst_page_name
                elif action_info["dst_page"] != dst_page:
                    print("### dst conflict:, ori:", action_info["dst_page"], ", now:", dst_page)
                    # dst_page_name = self.all_page_info[dst_page]["page_name"]
                    action_info["dst_page"] = dst_page
                    action_info["dst_page_name"] = dst_page_name

        src_page_name = self.all_page_info[src_page]["page_name"]
        cur_record = {"src_page": src_page, "src_page_name": src_page_name, "action_id": action_id,
                      "dst_page": dst_page, "dst_page_name": dst_page_name}
        self.action_record.append(cur_record)

    def get_action_by_pos(self, page_id: str, click_pos: list):
        all_view_info = self.all_page_info[page_id]["clickable_views"]
        min_dis = 1920 * 1920 * 2
        min_action_id = ""
        min_action_info = {}
        for action_id, action_info in self.all_action_info[page_id].items():
            if action_info["xpath"] not in all_view_info.keys():
                continue
            view_info = all_view_info[action_info["xpath"]]
            if is_point_in_bound(click_pos, view_info["bounds"]):
                center = get_bound_center(view_info["bounds"])
                dis_x = center[0] - click_pos[0]
                dis_y = center[1] - click_pos[1]
                dis = dis_x * dis_x + dis_y * dis_y
                if dis < min_dis:
                    min_action_id = action_id
                    min_action_info = action_info
        return min_action_id, min_action_info

    # def update_xpath(self, new_page_info: dict, old_page_info: dict, page_id: str, dis_thres=200):
    #     new_actions = set(new_page_info["actions"].keys())
    #     old_actions = set(old_page_info["actions"].keys())
    #     for action_key in new_actions.intersection(old_actions):
    #         new_action_info = new_page_info["actions"][action_key]
    #         old_action_info = old_page_info["actions"][action_key]
    #         bound_dis = get_bound_distance(new_action_info["bound"], old_action_info["bound"])
    #         if bound_dis <= dis_thres and new_action_info["xpath"] != old_action_info["xpath"]:
    #             old_action_info["xpath"] = new_action_info["xpath"]
    #             self.all_action_info[page_id][action_key]["xpath"] = new_action_info["xpath"]

    def update_page_action(self, new_page_info: dict, old_page_info: dict, page_id: str, lou_thres=0.9):
        old_page_info["init_by_static"] = False
        old_action_info = self.all_action_info[page_id]
        update_action_infos = self.init_action_infos()
        for action_id, ori_info in new_page_info["actions"].items():
            action_idx = len(update_action_infos.keys()) + 1
            action_info = {"action_idx": action_idx, "visit_times": 0, "dst_page": "unknown", "name": ori_info["name"],
                           "bound": ori_info["bound"], "dst_page_name": "unknown", "xpath": ori_info["xpath"],
                           "scroll": 0}
            if action_id in old_action_info.keys() and old_action_info[action_id]["dst_page"] != "unknown":
                action_info["dst_page"] = old_action_info[action_id]["dst_page"]
                action_info["dst_page_name"] = old_action_info[action_id]["dst_page_name"]
                action_info["scroll"] = old_action_info[action_id]["scroll"]
                # pass
            else:
                for old_key, old_info in old_action_info.items():
                    lou = get_bound_lou(old_info["bound"], ori_info["bound"])
                    if lou >= lou_thres and old_info["dst_page"] != "unknown":
                        # print("copy dst:", old_info["bound"], "->", ori_info["bound"])
                        action_info["dst_page"] = old_info["dst_page"]
                        action_info["dst_page_name"] = old_info["dst_page_name"]
                        action_info["scroll"] = old_info["scroll"]
                        # if page_id == "Amaze#2":
                        #     print("ori key:", old_key, ", new key:", action_id)
                        #     print("copy dst:", old_info["bound"], "->", ori_info["bound"], old_info["dst_page_name"])
            update_action_infos.setdefault(action_id, action_info)
        if new_page_info["is_scrollable"]:
            found_actions = new_page_info["actions"]
            # print("before add scroll", update_action_infos.keys())
            scroll_times = 1
            while scroll_times <= 3:
                has_add = False
                self.env.scroll_down()
                new_screen_info = self.env.get_current_screen()
                new_page_info = parse_layout_appium(new_screen_info["xml_path"])
                for action_id, ori_info in new_page_info["actions"].items():
                    if action_id in found_actions.keys():
                        continue
                    # print("### add scroll action:", action_id)
                    has_add = True
                    found_actions.setdefault(action_id, ori_info)
                    action_idx = len(update_action_infos.keys()) + 1
                    action_info = {"action_idx": action_idx, "visit_times": 0, "dst_page": "unknown",
                                   "scroll": scroll_times, "name": ori_info["name"], "bound": ori_info["bound"],
                                   "dst_page_name": "unknown", "xpath": ori_info["xpath"]}
                    update_action_infos.setdefault(action_id, action_info)
                scroll_times += 1
                if not has_add:
                    break
        self.all_action_info[page_id] = update_action_infos
        old_page_info["actions"] = new_page_info["actions"].copy()

    def reset_page_visit(self):
        for page_id, page_info in self.all_page_info.items():
            page_info["visit_times"] = 0

    def get_latest_action(self):
        if len(self.action_record) > 0:
            return self.action_record[-1]
        else:
            return None


class STG:
    def __init__(self):
        self.previous_page_map = {}

    def update_previous_page(self, after_page: str, previous_page=None):
        if after_page not in self.previous_page_map.keys():
            if previous_page and previous_page != after_page:
                self.previous_page_map.setdefault(after_page, [previous_page])
            else:
                self.previous_page_map.setdefault(after_page, [])
        elif previous_page and previous_page not in self.previous_page_map[after_page] and previous_page != after_page:
            self.previous_page_map[after_page].append(previous_page)

    def get_closest_previous_page(self, dst_page: str, current_page: str):
        # print("dst_page:", dst_page, ", previous page:", self.previous_page_map[dst_page], "cur_page:", current_page)
        if len(self.previous_page_map[dst_page]) == 0 or current_page in self.previous_page_map[dst_page]:
            return dst_page
        previous_page = self.previous_page_map[dst_page][0]
        return self.get_closest_previous_page(previous_page, current_page)

