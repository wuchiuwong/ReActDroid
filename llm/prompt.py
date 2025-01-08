init_prompt = """As an experienced mobile app tester, your task is to try and reproduce a crash on the app based on the crash description. I'll provide you with the current page of the app and the available actions you can perform (interactions with the app's GUI widgets). You need to select and perform the action that best matches the crash description so as to reproduce the crash in a step-by-step manner.

There are three types of actions on the page:
1. Click[widget name]: You will click a button on the page called "widget name".
2. Long press[widget name]: You will long press a button on the page called "widget name".
3. Input[widget name]: You will type something into a input box on the page called "widget name".

Use the following format:

<Reported crash>: a one-sentence description of the crash that you must reproduce
<Observation>: I will tell you the current page of the app and the available actions you can perform
<Thought>: you should always think about what to do
<Action>: you should answer the number of the chosen action. (e.g., you should answer "<Action>: 3")
... (then I will tell you the new Observation after the action you choose. This Observation/Thought/Action can repeat N times until the crash is reproduced)

Note that your answer should be only one <Thought> and one <Action>."""

crash_desc_prompt = "Let's begin!\n<Reported crash>: {}"

hint_page_prompt = "\nHint: To reproduce the crash, you may need to first go to page \"{}\"."
hint_action_prompt = "\nHint: You have reached the page where the crash occurred, please perform the corresponding action according to the crash description: \"{}\"."
