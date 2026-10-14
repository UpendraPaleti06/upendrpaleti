# Installing Python and pip on Windows

This guide installs Python and pip (pip comes with Python) on Windows 10 or 11, then sets up the job search agent. It takes about 10 minutes.

## Step 1: Check whether Python is already installed

1. Press the **Windows key**, type `cmd`, and press **Enter**. A black Command Prompt window opens.
2. Type this and press **Enter**:

   ```
   python --version
   ```

3. What you see tells you what to do next:
   - `Python 3.12.x` (or any version 3.10 or newer): Python is installed. Skip to [Step 4](#step-4-check-that-it-worked).
   - `'python' is not recognized...`, or the **Microsoft Store** opens: Python isn't installed. Close the Store and go to Step 2.

## Step 2: Download Python

1. Open your browser and go to **https://www.python.org/downloads/**.
2. Click the big yellow **Download Python 3.x.x** button. The site detects Windows automatically.
3. Wait for the file to download. It's named something like `python-3.13.x-amd64.exe` and is about 25 MB. It goes to your **Downloads** folder.

> Only download Python from python.org. Other sites may bundle unwanted software.

## Step 3: Run the installer

1. Open your **Downloads** folder and double-click the `python-3.x.x-amd64.exe` file.
2. If Windows asks *"Do you want to allow this app to make changes to your device?"*, click **Yes**.
3. On the first screen of the installer, look at the **bottom**. There are two checkboxes:
   - ☑ **Use admin privileges when installing py.exe**: leave this ticked.
   - ☐ **Add python.exe to PATH**: **tick this box.**

   > **This is the most important step.** PATH is the list of folders Windows searches when you type a command. If you don't tick this box, typing `python` or `pip` in Command Prompt gives a *"not recognized"* error.

4. Click **Install Now** (at the top of the window). This also installs pip.
5. Wait 1–3 minutes for the progress bar to finish.
6. If the last screen shows **"Disable path length limit"**, click it and choose **Yes**. This avoids errors with long folder names later.
7. Click **Close**.

## Step 4: Check that it worked

1. **Close every Command Prompt window** you had open. Old windows don't see the new PATH.
2. Open a new one: press the **Windows key**, type `cmd`, and press **Enter**.
3. Run these two commands:

   ```
   python --version
   pip --version
   ```

4. You should see something like:

   ```
   Python 3.13.0
   pip 24.2 from C:\Users\YourName\AppData\Local\Programs\Python\Python313\Lib\site-packages\pip (python 3.13)
   ```

   If you see both version numbers, Python and pip are ready. If not, see [Troubleshooting](#troubleshooting).

5. Optionally, update pip to the latest version:

   ```
   python -m pip install --upgrade pip
   ```

## Step 5: Set up the job search agent

1. Download this project. Either:
   - On GitHub, click the green **Code** button, then **Download ZIP**, and extract the ZIP. Or
   - If you have Git installed, run `git clone https://github.com/UpendraPaleti06/upendrpaleti.git`.
2. In Command Prompt, go to the project folder. Change the path to wherever you put it:

   ```
   cd %USERPROFILE%\Downloads\upendrpaleti
   ```

3. Create and turn on a virtual environment. This is a private package folder for this project:

   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

   Your prompt now starts with `(.venv)`. Run the `activate` line again each time you open a new Command Prompt.

4. Install the project's packages:

   ```
   pip install -r requirements.txt
   ```

5. Set your Claude API key. You can get one at https://platform.claude.com.

   ```
   set ANTHROPIC_API_KEY=your_key_here
   ```

   > `set` lasts only for the current window. To save the key permanently, run `setx ANTHROPIC_API_KEY "your_key_here"` and then open a new window. Never share your key or commit it to GitHub.

6. Create your profile and run the agent:

   ```
   copy example_profile.txt my_profile.txt
   notepad my_profile.txt
   python -m job_search_agent "Find remote Python developer jobs" --profile my_profile.txt
   ```

   When it finishes, open `shortlist.md` to see your ranked jobs.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `'python' is not recognized` or `'pip' is not recognized` | Python isn't on PATH. Run the installer again, choose **Modify**, click **Next**, tick **Add Python to environment variables**, and click **Install**. Then open a new Command Prompt. |
| Typing `python` opens the Microsoft Store | Open **Settings → Apps → Advanced app settings → App execution aliases** and turn **off** both *python.exe* and *python3.exe*. Then open a new Command Prompt. |
| `python` works but `pip` doesn't | Use `python -m pip` instead of `pip` (for example `python -m pip install -r requirements.txt`), or run `python -m ensurepip --upgrade`. |
| Neither `python` nor `pip` works, but `py` does | Use the Python launcher: `py --version`, `py -m pip install -r requirements.txt`, `py -m job_search_agent ...`. |
| `.venv\Scripts\activate` fails in **PowerShell** with *"running scripts is disabled"* | Use Command Prompt (`cmd`) instead, or run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` in PowerShell once, answer **Y**, and try again. |
| `Could not find a version that satisfies the requirement anthropic` | Your Python is too old. Install Python 3.10 or newer from python.org. |
| `AuthenticationError` or `invalid x-api-key` when running the agent | The API key is missing or wrong. Run `set ANTHROPIC_API_KEY=...` again in the same window you run the agent from. |
