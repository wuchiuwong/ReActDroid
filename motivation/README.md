# Motivational Study of ReActDroid

## 1. Introduction
We employ the web crawler developed by Wendland et al. [25] to automatically collect bug reports from Android projects between January 2015 and October 2023, resulting in 112,148 bug reports. We apply filters based on keywords associated with application crashes, such as crash and exception. As a result, we obtain 11,821 Android crash reports for this study.

## 2. How is a bug report determined to information reltaed to the crash?
### 2.1 Reproducing steps
The report is considered to include the reproducing steps if either one of the two criteria is met:
- There must be three or more sequential lines, where each line starts with an itemization mark (such as -) or a numerical index (for instance, 1, 2, 3). This criterion is congruent with the method mentioned in your comment.
- There must be three or more sequential lines, where each line contains a verb that corresponds to GUI actions (Listed below). This criterion accommodates instances where the reporter describes reproducing steps without itemization indications.
```python
verbs = ['select', 'choose', 'swipe', 'press', 'type', 'enter', 'change', 'switch', 'enable', 'open', 'import', "tell",
         "insert", "rotate", "reconnect", "start", "stop", "add", "say", 'clicking', 'disable', 'launch', 'set', 'tap',
         'click', 'go', 'turn', 'write', 'input', 'put', "cancel", "send", "map", "scroll", "create", "search"]
```

### 2.2 Reproducing steps
There are at least five lines in the report that match the regular expression ```". *? \.java:\d+. *?"```

### 2.3 Visual recordings
The report contains the following words: ".png", ".jpg", ".jpeg", ".gif"

### 2.4 Crash overview
The report is considered to include the crash overview if three criteria are all met:
- It is only one line (separated by the line break) and one sentence (separated by the period). 
- The presence of terms related to "crash"
- The presence of verbs denoting GUI actions (Consistent with 2.1 Reproducing steps)