import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# -- The 5 Target Cities in Maharashtra --
# Strictly Pune, Mumbai Main, Thane, Nashik, and Nagpur. No other cities.
TARGET_CITIES = [
    {
        "name": "Pune",
        "official_unit": "PUNE CITY",
        "district_code": "19393",
    },
    {
        "name": "Mumbai Main",
        "official_unit": "BRIHAN MUMBAI CITY",
        "district_code": "19378",
    },
    {
        "name": "Thane",
        "official_unit": "THANE CITY",
        "district_code": "19399",
    },
    {
        "name": "Nashik",
        "official_unit": "NASHIK CITY",
        "district_code": "19408",
    },
    {
        "name": "Nagpur",
        "official_unit": "NAGPUR CITY",
        "district_code": "19387",
    },
]

BASE_URL = "https://citizen.mahapolice.gov.in"
INDEX_URL = f"{BASE_URL}/Citizen/MH/index.aspx"
PUBLISHED_FIRS_URL = f"{BASE_URL}/Citizen/MH/PublishedFIRs.aspx"


def init_chrome_driver(download_dir):
    """Initialize a headless Chrome browser configured to automatically save PDFs."""
    abs_download_dir = os.path.abspath(download_dir)
    os.makedirs(abs_download_dir, exist_ok=True)

    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,1000")
    opts.add_argument("--headless=new")

    prefs = {
        "download.default_directory": abs_download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    opts.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=opts)
    # Enable file downloads in headless Chrome via Chrome DevTools Protocol
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": abs_download_dir
        })
        driver.execute_cdp_cmd("Browser.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": abs_download_dir
        })
    except Exception:
        pass
    return driver


def wait_for_new_pdf_download(download_dir, before_files, timeout=20):
    """Wait until a new non-crdownload PDF file appears and finishes writing."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(download_dir))
        new_files = current_files - before_files
        # Check if any new PDF exists and no .crdownload file is active
        has_crdownload = any(f.endswith(".crdownload") for f in current_files)
        new_pdfs = [f for f in new_files if f.lower().endswith(".pdf")]
        if new_pdfs and not has_crdownload:
            # Check file size is stable and > 0
            latest = new_pdfs[0]
            latest_path = os.path.join(download_dir, latest)
            if os.path.exists(latest_path) and os.path.getsize(latest_path) > 1000:
                return latest
        time.sleep(1)
    return None


def scrape_firs(download_dir="firs_downloaded"):
    """
    Scrapes real, official First Information Report (FIR) PDFs from the Maharashtra Police
    Citizen Portal exclusively for the 5 target cities:
    1. Pune (PUNE CITY - 19393)
    2. Mumbai Main (BRIHAN MUMBAI CITY - 19378)
    3. Thane (THANE CITY - 19399)
    4. Nashik (NASHIK CITY - 19408)
    5. Nagpur (NAGPUR CITY - 19387)

    Search parameters:
      - Date From: Today
      - Date To: Today
      - Unit: Selected city unit code
      - Police Station: Blank (searches all stations in the unit)
      - FIR Number: Blank
    """
    abs_download_dir = os.path.abspath(download_dir)
    os.makedirs(abs_download_dir, exist_ok=True)

    print("\n" + "=" * 70, flush=True)
    print("  MAHARASHTRA POLICE FIR SCRAPER -- 5 TARGET CITIES (LIVE PORTAL)", flush=True)
    print("=" * 70, flush=True)
    for i, city in enumerate(TARGET_CITIES, 1):
        print(f"  [{i}/5] {city['name'].upper()} ({city['official_unit']} - Code: {city['district_code']})", flush=True)
    print("=" * 70, flush=True)

    driver = None
    downloaded_files = []

    try:
        print("\n[Portal] Launching headless browser...", flush=True)
        driver = init_chrome_driver(abs_download_dir)
        wait = WebDriverWait(driver, 20)

        # Step 1: Establish session cookies by loading home page
        print("[Portal] Navigating to index page to initialize session...", flush=True)
        driver.get(INDEX_URL)
        time.sleep(2)

        today = datetime.now()
        today_str = today.strftime("%d/%m/%Y")
        print(f"[Portal] Querying FIRs exclusively for TODAY: {today_str}\n", flush=True)

        for idx, city in enumerate(TARGET_CITIES, 1):
            cname = city["name"]
            ccode = city["district_code"]
            unit_name = city["official_unit"]

            print(f"--- [{idx}/5] Querying City: {cname.upper()} ({unit_name}) ---", flush=True)

            try:
                # Navigate to the Published FIRs search page
                driver.get(PUBLISHED_FIRS_URL)
                time.sleep(2)

                # Set Date From and Date To strictly to today
                from_input = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_txtDateOfRegistrationFrom")))
                to_input = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_txtDateOfRegistrationTo")))
                driver.execute_script("arguments[0].value = arguments[1];", from_input, today_str)
                driver.execute_script("arguments[0].value = arguments[1];", to_input, today_str)

                # Select the Unit from dropdown (Pune City, Brihan Mumbai City, Thane City, etc.)
                unit_select = Select(driver.find_element(By.ID, "ContentPlaceHolder1_ddlDistrict"))
                unit_select.select_by_value(ccode)
                time.sleep(2)

                # Re-verify dates are intact after ASP.NET postback
                driver.execute_script("arguments[0].value = arguments[1];", driver.find_element(By.ID, "ContentPlaceHolder1_txtDateOfRegistrationFrom"), today_str)
                driver.execute_script("arguments[0].value = arguments[1];", driver.find_element(By.ID, "ContentPlaceHolder1_txtDateOfRegistrationTo"), today_str)

                # Leave Police Station blank and FIR Number blank
                # Click the Search button
                search_btn = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_btnSearch")))
                search_btn.click()
                time.sleep(4)

                # Check total record count label
                total_records = "0"
                try:
                    lbl = driver.find_element(By.ID, "ContentPlaceHolder1_lbltotalrecord")
                    total_records = lbl.text.strip()
                except Exception:
                    pass

                print(f"  [Portal Status] {cname}: Total FIR records found today: {total_records}", flush=True)

                # Inspect results table
                tables = driver.find_elements(By.ID, "ContentPlaceHolder1_gdvDeadBody")
                if tables:
                    rows = tables[0].find_elements(By.TAG_NAME, "tr")
                    data_rows = rows[1:] if len(rows) > 1 else []
                    print(f"  [Table Rows] Found {len(data_rows)} rows displayed for {cname}", flush=True)

                    if data_rows:
                        # Find the first row that hasn't been downloaded yet
                        selected_row = None
                        selected_fir = None
                        selected_ps = None
                        selected_reg_time = None

                        existing_local_names = set(os.listdir(abs_download_dir))
                        for row in data_rows:
                            cols = [c.text.strip().replace("\n", " ") for c in row.find_elements(By.TAG_NAME, "td")]
                            cand_fir = cols[5] if len(cols) > 5 else ""
                            # Check if this FIR has already been downloaded
                            already_downloaded = any(cand_fir and cand_fir in fname for fname in existing_local_names)
                            if not already_downloaded:
                                selected_row = row
                                selected_fir = cand_fir
                                selected_ps = cols[3] if len(cols) > 3 else "N/A"
                                selected_reg_time = cols[6] if len(cols) > 6 else ""
                                break

                        # Fallback to row 0 if all were seen
                        if not selected_row:
                            selected_row = data_rows[0]
                            cols = [c.text.strip().replace("\n", " ") for c in selected_row.find_elements(By.TAG_NAME, "td")]
                            selected_fir = cols[5] if len(cols) > 5 else "N/A"
                            selected_ps = cols[3] if len(cols) > 3 else "N/A"
                            selected_reg_time = cols[6] if len(cols) > 6 else ""

                        clean_ps = selected_ps.encode("ascii", "replace").decode("ascii")
                        print(f"  [Selected FIR] FIR #{selected_fir} at Police Station: {clean_ps} (Registered: {selected_reg_time})", flush=True)

                        # Click Download button to fetch real PDF
                        download_btns = selected_row.find_elements(By.CSS_SELECTOR, "input[value='Download']")
                        if download_btns:
                            before_files = set(os.listdir(abs_download_dir))
                            # Trigger click via JS for reliable headless download
                            driver.execute_script("arguments[0].click();", download_btns[0])
                            new_pdf = wait_for_new_pdf_download(abs_download_dir, before_files, timeout=25)
                            if new_pdf:
                                full_path = os.path.join(abs_download_dir, new_pdf)
                                size_kb = os.path.getsize(full_path) // 1024
                                print(f"  [Download Complete] Real PDF saved: {new_pdf} ({size_kb} KB)", flush=True)
                                downloaded_files.append(full_path)
                            else:
                                print(f"  [Notice] Download initiated, checking existing directory files.", flush=True)
                else:
                    print(f"  [Portal Status] {cname}: No table displayed for today's date.", flush=True)

            except Exception as city_err:
                print(f"  [City Error] {cname}: Error querying portal: {city_err}", flush=True)

            time.sleep(1)

    except Exception as e:
        print(f"[Portal Error] Scraper encountered an exception: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    print(f"\n[Scraper Complete] Total real government FIR PDFs downloaded this cycle: {len(downloaded_files)}", flush=True)
    return download_dir, downloaded_files


if __name__ == "__main__":
    scrape_firs()
