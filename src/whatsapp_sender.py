"""
whatsapp_sender.py — Send automated messages to WhatsApp group via Selenium.

⭐ HIGH-VALUE SKILL — rare on freelance platforms ($300–$1500/project).

Setup (first time):
  1. Run with headless=False
  2. Scan QR code on https://web.whatsapp.com
  3. Session is saved to ./wa_session/ — no re-scan needed next time

Requirements:
  - Google Chrome installed
  - chromedriver matching Chrome version (https://chromedriver.chromium.org/)
  - selenium==4.x

Config (in .env):
  WA_GROUP_NAME=Your Group Name
"""
import os
import time
import logging
from pathlib import Path

log = logging.getLogger(__name__)

WA_SESSION_DIR = str(Path(__file__).parent.parent / "wa_session")
WA_GROUP_NAME  = os.environ.get("WA_GROUP_NAME", "Report Bot Test")


def _get_driver(headless=False):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    opts.add_argument(f"--user-data-dir={WA_SESSION_DIR}")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-gpu")
    if headless:
        opts.add_argument("--headless=new")
    return webdriver.Chrome(options=opts)


def send_wa_message(message, group_name=None, headless=True):
    """
    Send a text message to a WhatsApp group.

    Parameters
    ----------
    message    : str  the message text (supports newlines)
    group_name : str  WhatsApp group name (defaults to WA_GROUP_NAME env var)
    headless   : bool True for background mode (needs prior QR scan session)
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    target_group = group_name or WA_GROUP_NAME
    driver = _get_driver(headless=headless)
    wait   = WebDriverWait(driver, 60)

    try:
        driver.get("https://web.whatsapp.com")
        log.info("[whatsapp] Waiting for WhatsApp Web to load...")
        time.sleep(6)

        # Find the search box
        search_box = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        ))
        search_box.click()
        search_box.send_keys(target_group)
        time.sleep(2)

        # Click on the group
        group_el = wait.until(EC.presence_of_element_located(
            (By.XPATH, f'//span[@title="{target_group}"]')
        ))
        group_el.click()
        time.sleep(1)

        # Type message in message box
        msg_box = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        ))
        for line in message.split("\n"):
            msg_box.send_keys(line)
            msg_box.send_keys(Keys.SHIFT + Keys.ENTER)
        msg_box.send_keys(Keys.ENTER)
        time.sleep(2)

        log.info("[whatsapp] Message sent to group: %s", target_group)
        print(f"[whatsapp] Message sent to: {target_group}")

    except Exception as exc:
        log.error("[whatsapp] Failed to send message: %s", exc)
        raise
    finally:
        driver.quit()


def send_wa_report(report_date, operator_summaries):
    """
    Send a formatted daily report to WhatsApp group.

    Parameters
    ----------
    report_date       : str   e.g. "2026-05-26"
    operator_summaries: list  list of dicts with keys: operator, duration_min, dod_pct
    """
    lines = []
    for item in operator_summaries:
        arrow = "▲" if item.get("dod_pct", 0) >= 0 else "▼"
        lines.append(
            f"  {item['operator']}: {item['duration_min']:,.0f} min  "
            f"{arrow}{abs(item.get('dod_pct', 0)):.1f}% DoD"
        )

    message = (
        f"📊 *Daily Telecom Report — {report_date}*\n\n"
        + "\n".join(lines)
        + "\n\n_Auto-generated · Python Pipeline_\n"
        "_Runs daily at 06:12 WIB — no manual trigger_"
    )
    send_wa_message(message)
