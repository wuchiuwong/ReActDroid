# ReActDroid

## 1. Introduction
Code and Data for the paper "One Sentence Can Kill the Bug: Auto-replay Mobile App Crashes from One-sentence Overviews". For running video recordings of ReActDroid, please go to the following link to download: [Download link](https://drive.google.com/file/d/1G6UTNw90ZOw4LgwSFe0WElni8_DMoaS7/view)

## 2. Details of the Datasets Used in Our Experiments

For the 59 bug reports that at least one tool can successfully reproduce:
- Number of reproducing steps to trigger the crash (donate as **Step**): average: 4.2, min: 1, max: 14
- Number of pages included in the app (donate as **Page**): average: 15.9, min: 1, max: 60
- Number of widgets in the app (donate as **Widget**): average: 95.2 min: 5, max: 350
- Number of widgets per page in the app (donate as **WPP**): average: 5.7 min: 1, max: 33

The details of each report are as follows

#### Details of ReCDroids's Dataset
| **ID** | **Bug Report**  | **Step** | **Page** | **Widget** | **WPP** | **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP** |
|--------|-----------------|----------|----------|------------|---------|--------|----------------|----------|----------|------------|---------|
| R-1    | NewsBlur-1053   | 5        | 4        | 18         | 4.5     | R-15   | Transistor-63  | 2        | 5        | 15         | 3       |
| R-2    | Markor-194      | 4        | 5        | 68         | 13.6    | R-16   | Zom-271        | 5        | 9        | 35         | 3.89    |
| R-3    | Birthdroid-13   | 5        | 8        | 32         | 4       | R-17   | Pix-Art-125    | 3        | 5        | 22         | 4.4     |
| R-4    | Car Report-43   | 10       | 5        | 38         | 7.6     | R-18   | Pix-Art-127    | 3        | 5        | 19         | 3.8     |
| R-5    | AnyMemo-18      | 2        | 3        | 23         | 7.67    | R-19   | ScreenCam-25   | 5        | 6        | 29         | 4.83    |
| R-6    | AnyMemo-440     | 4        | 12       | 107        | 8.92    | R-20   | ownCloud-487   | 3        | 4        | 23         | 5.75    |
| R-7    | Notepad-23      | 6        | 7        | 33         | 4.71    | R-21   | OBDReader-22   | 9        | 5        | 15         | 3       |
| R-8    | Olam-2          | 2        | 1        | 4          | 4       | R-22   | Dagger-46      | 1        | 1        | 4          | 4       |
| R-9    | Olam-1          | 2        | 1        | 4          | 4       | R-23   | ODK-2086       | 3        | 51       | 260        | 5.1     |
| R-10   | FastAdapter-394 | 1        | 1        | 46         | 46      | R-24   | K-9Mail-3255   | 4        | 2        | 11         | 5.5     |
| R-11   | LibreNews-22    | 5        | 7        | 36         | 5.14    | R-25   | K-9Mail-2612   | 3        | 3        | 36         | 12      |
| R-12   | LibreNews-23    | 6        | 6        | 34         | 5.67    | R-26   | K-9Mail-2019   | 2        | 2        | 17         | 8.5     |
| R-13   | LibreNews-27    | 5        | 6        | 34         | 5.67    | R-27   | TagMo-12       | 2        | 3        | 15         | 5       |
| R-14   | SMSsync-464     | 4        | 18       | 160        | 8.89    | R-28   | FlashCards-13  | 6        | 5        | 13         | 2.6     |


#### Details of AndroR2 Dataset
| **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP** | **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP** |
|--------|----------------|----------|----------|------------|---------|--------|----------------|----------|----------|------------|---------|
| A-1    | HABPanel-25    | 5        | 6        | 12         | 2       | A-6    | K-9Mail-3255   | 4        | 2        | 11         | 5.5     |
| A-2    | Noad Player-1  | 1        | 1        | 1          | 5       | A-7    | K-9Mail-3971   | 5        | 7        | 29         | 4.14    |
| A-3    | Weather-61     | 4        | 4        | 16         | 4       | A-8    | Firefox-3932   | 5        | 8        | 63         | 7.88    |
| A-4    | Berkeley-82    | 1        | 1        | 8          | 8       | A-9    | Aegis-3932     | 14       | 15       | 101        | 6.73    |
| A-5    | andOTP-500     | 12       | 14       | 86         | 6.14    |        |                |          |          |            |         |


#### Details of ScopeDroid's Dataset
| **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP** | **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP ** |
|--------|----------------|----------|----------|------------|---------|--------|----------------|----------|----------|------------|----------|
| S-1    | SDBViewer-10   | 2        | 11       | 35         | 3.18    | S-12   | FoodTracker-55 | 3        | 17       | 84         | 4.94     |
| S-2    | Anki-9914      | 3        | 24       | 239        | 9.96    | S-13   | GrowTracker-87 | 9        | 25       | 128        | 5.12     |
| S-3    | Anki-10584     | 2        | 16       | 154        | 9.62    | S-14   | Markor-1565    | 7        | 29       | 350        | 12.07    |
| S-4    | Alarmio-47     | 2        | 6        | 53         | 8.83    | S-15   | nRF Mesh-495   | 3        | 12       | 73         | 6.08     |
| S-5    | plusTimer-19   | 6        | 13       | 97         | 7.46    | S-16   | SDBViewer-7    | 2        | 8        | 25         | 3.12     |
| S-6    | GrowTracker-89 | 5        | 19       | 89         | 4.68    | S-17   | FakeStandby-30 | 2        | 5        | 15         | 3        |
| S-7    | Shuttle-456    | 6        | 27       | 210        | 7.78    | S-18   | pedometer-101  | 3        | 31       | 223        | 7.19     |
| S-8    | Anki-2765      | 2        | 40       | 230        | 5.75    | S-19   | Revolution-183 | 4        | 31       | 160        | 5.16     |
| S-9    | Anki-3370      | 6        | 60       | 327        | 5.45    | S-20   | Anki-3224      | 4        | 18       | 62         | 3.44     |
| S-10   | Anki-2681      | 2        | 40       | 241        | 6.03    | S-21   | getodk-219     | 1        | 35       | 240        | 6.86     |
| S-11   | WhereUGo-368   | 5        | 17       | 105        | 6.18    | S-22   | Anitrend-110   | 1        | 1        | 5          | 5        |



## 3. Preparation Before Running

#### 3.1 Requirements
* Android emulator
* Ubuntu or Windows
* Appium Desktop Client: [Download link](https://github.com/appium/appium-desktop/releases/tag/v1.22.3-4)
* Python 3.10
  * apkutils==0.10.2
  * Appium-Python-Client==1.3.0
  * Levenshtein==0.18.1
  * lxml==4.8.0
  * opencv-python==4.5.5.64
  * openai==0.27.8  
  * tiktoken==0.4.0  

#### 3.2 Setting the api_key for OpenAI
ReActDroid is based on GPT-3.5-turbo to reproduce crashes, but the model's predictions are not free, so it requires the user to set their ```api_key``` in ```llm/model.py```.


## 4. How to run ReActDroid on apps in our experiment
1. Download our data archive from Google Play and extract it to this directory: [Download link](https://drive.google.com/file/d/1aA8Re93V6YgBQ-kLRs6z6hPKUO1m_PL3/view?usp=sharing)
2. Launch an Android emulator and connect to it via `adb`
3. Launch the `Appium Desktop Client`
4. In the `Main` directory, there are several scripts to run CrashTranslator:
   * `main/run_recdroid.py`: run ReActDroid on apps in the ReCDroid's dataset
   * `main/run_andror2.py`: run ReActDroid on apps in the AndroR2 dataset
   * `main/run_mydata.py`: run ReActDroid on apps in the CrashTranslator's dataset
   * To change the running app, modify the `app_idx` variable in `do_test(app_idx)`.