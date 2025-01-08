import re
from Levenshtein import distance

def only_ascii(in_str: str):
    s1 = re.sub(r"[^\x00-\xFF]", " ", in_str)
    s2 = re.sub(r"\s+", " ", s1).strip()
    return s2


def only_ascii_clip(in_str: str, clip_token=6):
    s1 = re.sub(r"[^\x00-\xFF]", " ", in_str)
    s2 = re.sub(r"\s+", " ", s1).strip()
    s2_token = s2.split()
    s2_token_clean = [t for t in s2_token if len(t) <= 20 and len(t) >= 1]
    s2_clean = " ".join(s2_token_clean)
    if len(s2_token_clean) <= clip_token:
        return s2_clean
    else:
        return " ".join(s2_token_clean[:clip_token]) + " ..."


def only_digit_and_alpha_clip(in_str: str, clip_token=6):
    s1 = re.sub(r"[^A-Za-z0-9\',.]", " ", in_str)
    s2 = re.sub(r"\s+", " ", s1).strip()
    s2_token = s2.split()
    if len(s2_token) <= clip_token:
        return s2
    else:
        return " ".join(s2_token[:clip_token]) + " ..."


def is_str_match(str1: str, str2: str, len_thres=0.9, diff_thes=0.2):
    # proc_str1 = only_ascii(str1).replace(" ", "")
    # proc_str2 = only_ascii(str2).replace(" ", "")
    proc_str1 = re.sub("[^a-zA-Z0-9]", " ", str1)
    proc_str1 = re.sub("\s+", " ",  proc_str1).strip()
    proc_str2 = re.sub("[^a-zA-Z0-9]", " ", str2)
    proc_str2 = re.sub("\s+", " ",  proc_str2).strip()
    min_len = min(len(proc_str1), len(proc_str2))
    max_len = max(len(proc_str1), len(proc_str2))
    if min_len < len_thres * max_len:
        return False
    dis = distance(proc_str1, proc_str2)
    if dis < diff_thes * max_len:
        return True
    else:
        return False

def tokenize_str(in_str: str):
    in_str = in_str.split("/")[-1]
    in_str = re.sub(r'([a-z])([A-Z])', r'\1 \2', in_str)
    in_str = re.sub(r"[^a-zA-Z0-9]", " ", in_str)
    in_str = re.sub(r"\s+", " ", in_str).strip()
    return in_str


def clean_resource_id(resource_id: str):
    resource_id = tokenize_str(resource_id)
    resource_id = re.sub("[^a-zA-Z]", " ", resource_id).lower().strip()
    useless_words = ["edittext", "button", "none", "view", "textview", "fab", "action", "icon"]
    words = resource_id.strip().split(" ")
    use_word = []
    for word in words:
        word_char = set(word.lower())
        # drop word that maybe abbreviation from edittext/button, like: edit, edt, ed, text...
        use_flag = True
        for useless_word in useless_words:
            inter_with_useless_word = word_char.intersection(set(useless_word))
            if len(word_char) <= len(inter_with_useless_word):
                use_flag = False
                break
        if use_flag:
            use_word.append(word)
    if len(use_word) == 0:
        return "none"
    else:
        return " ".join(use_word)

def get_activity_name(activity: str):
    activity = tokenize_str(activity.split(".")[-1])
    return activity

def action_key_to_desc(action_key: str):
    if "[" in action_key:
        verb = action_key.split("[")[0].lower()
        object = action_key.split("[")[1].split("]")[0]
        if verb == "click":
            desc = 'clicked on the "' + object + '" button'
        elif verb == "long press":
            desc = 'long pressed the "' + object + '" button'
        else:
            desc = 'filled in the "' + object + '" input box'
        return desc
    elif action_key == "Back to previous page":
        return "go back to previous page"
    else:
        return "go back to previous page"


def process_xpath(xpath: str):
    elements = []
    for ele in xpath.lower().split("/"):
        if len(ele) > 0:
            elements.append(ele.split(".")[-1])
    xpath = "/".join(elements)
    for view_name in ["listview", "recyclerview"]:
        if view_name in xpath:
            xpath1 = xpath.split(view_name, 1)[0]
            xpath2 = xpath.split(view_name, 1)[1]
            xpath2 = re.sub("\[\d+]", "*", xpath2)
            xpath = xpath1 + view_name + xpath2
    return xpath

if __name__ == '__main__':
    a = "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.view.ViewGroup/android.widget.FrameLayout/android.view.ViewGroup/androidx.viewpager.widget.ViewPager/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.widget.RelativeLayout[3]"
    print(process_xpath(a))