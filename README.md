Installation and Usage
1. Go to directory where you want to download
```bash
#for linux users
git clone https://github.com/agenta007/coomer.st-scraper
cd coomer.st-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
```powershell
#for windows users
# 1️⃣  Clone the repo (works in Git‑Bash, PowerShell, CMD, etc.)
git clone https://github.com/agenta007/coomer.st-scraper

# 2️⃣  Move into the directory
Set-Location -Path .\coomer.st-scraper\

# 3️⃣  Create a virtual environment
python -m venv venv        # the 'venv' folder will be created here

# 4️⃣  Activate the virtual environment *in PowerShell*
# (If you get an execution‑policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once.)
.\venv\Scripts\Activate.ps1

# 5️⃣  (Optional) upgrade pip inside the venv
python -m pip install --upgrade pip

# 6️⃣  Install the required packages
pip install -r requirements.txt
```
2. Define your media download directory. Open scraper.py and change value of BASE_SAVE_URL = "" to BASE_SAVE_URL = "/path/to/download" or BASE_SAVE_URL = "C:\Users\Bob\Downloads" for Windows
3. If your environment is not activated activate it with source venv/bin/activate in the directory of scraper.py (you must see (venv) in your command prompt / terminal)
4. Run with example command scraper.py itslolaxo o --verbose. Change "itslolaxo" to the username you want to scrape. If you want to reiterate use --restart. Omit --verbose to quiet down the script
5. Enjoy your scraped media!