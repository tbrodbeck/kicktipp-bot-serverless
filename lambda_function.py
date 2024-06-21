import os
import random
from datetime import datetime
from datetime import timedelta
import requests
import logging
from logging import debug
import json

from playwright.sync_api import sync_playwright

# Constants
BASE_URL = "https://www.kicktipp.de/"
LOGIN_URL = "https://www.kicktipp.de/info/profil/login/"
EMAIL = os.getenv("KICKTIPP_EMAIL")
PASSWORD = os.getenv("KICKTIPP_PASSWORD")
NAME_OF_COMPETITION = os.getenv("KICKTIPP_NAME_OF_COMPETITION")
ZAPIER_URL = os.getenv("ZAPIER_URL")
TIME_UNTIL_GAME = os.getenv("KICKTIPP_HOURS_UNTIL_GAME") != None and timedelta(
    hours=int(os.getenv("KICKTIPP_HOURS_UNTIL_GAME"))) or timedelta(hours=2)
NTFY_URL = os.getenv("NTFY_URL")
NTFY_USERNAME = os.getenv("NTFY_USERNAME")
NTFY_PASSWORD = os.getenv("NTFY_PASSWORD")

LOG_LEVEL = os.getenv("LOG_LEVEL")

def predict_with_win_loss_ratio(win, loss, goals_so_far, group_phase=True):
    """
    Calculate predicted goals based on win/loss ratio and average goals.

    Args:
    win (int): Number of wins.
    loss (int): Number of losses.
    average_goals (float): Average goals per game.

    Returns:
    tuple: Tuple containing predicted goals for team 1, team 2, and the loss ratio.
    """
    ko_goal_multiplier = 3.29 / 2.94
    expected_goals = goals_so_far if group_phase else goals_so_far * ko_goal_multiplier # the group phase will require an additional scraping logic with calculating the `expected_goals`

    loss_ratio = win / (win + loss)
    debug(f'average_goals={expected_goals}; loss_ratio={loss_ratio}')
    loss_goals_estimate = expected_goals * loss_ratio
    win_goals_estimate = expected_goals - loss_goals_estimate
    debug(f'loss_ratio={loss_ratio}; loss_goals_estimate={loss_goals_estimate}; win_goals_estimate={win_goals_estimate}')

    if not group_phase and win_goals_estimate == loss_goals_estimate:
        if loss_ratio < 0.5:
            if win_goals_estimate + loss_goals_estimate < expected_goals:
                win_goals_estimate += 1
            else:
                loss_goals_estimate -= 1
        elif loss_ratio == 0.5:
            logging.info('GG')
            if random.randint(0, 1):
                win_goals_estimate += 1
            else:
                loss_goals_estimate += 1
        else:
            if win_goals_estimate + loss_goals_estimate < expected_goals:
                loss_goals_estimate += 1
            else:
                win_goals_estimate -= 1

    return round(win_goals_estimate), round(loss_goals_estimate), 1 - round(loss_ratio, 2), round(expected_goals, 2)

def tip_all_games():
    # Launch Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Login
        login(page)

        page.goto(F"https://www.kicktipp.de/{NAME_OF_COMPETITION}/tabellen")

        # Find tables with games data
        tables = page.query_selector_all(".drei_punkte_regel")

        games_x2 = 0
        goals_x2 = 0
        for table in tables:
            game_counts = table.query_selector_all(".col2")
            for game_count_idx in range(1, len(game_counts)):
                game_count_text = game_counts[game_count_idx].inner_text()
                games_x2 += int(game_count_text)
            goals_found = table.query_selector_all(".col4")
            for goal_idx in range(1, len(goals_found)):
                both_goals_str = goals_found[goal_idx].inner_text()
                both_goals = both_goals_str.split(':')
                goals_x2 += int(both_goals[0]) + int(both_goals[1])

        goals_so_far = goals_x2 / games_x2
        logging.info(f'{goals_so_far=}')

        # Go to tip submission page
        page.goto(F"https://www.kicktipp.de/{NAME_OF_COMPETITION}/tippabgabe")

        page.get_by_role("button", name="ZUSTIMMEN").click()

        # Find open game forms
        table_handle = page.locator("#tippabgabeSpiele")

        datarows = table_handle.locator('xpath=//tbody/tr')

        for game_locator in datarows.all():
            tippabgaben = game_locator.locator('.kicktipp-tippabgabe')

            for tippabgabe in tippabgaben.all():
                logging.debug(f'{game_locator.inner_html()=}')

                # Get game info
                time_element = game_locator.locator(".kicktipp-time")
                time_str = time_element.inner_text()
                time = datetime.strptime(time_str, '%d.%m.%y %H:%M')

                # Skip game if outside time threshold
                time_until_game = time - datetime.now()
                debug(f'{time_until_game=}')
                if time_until_game > TIME_UNTIL_GAME:
                    print(f'Game starts in {time_until_game}, thats more than ', TIME_UNTIL_GAME, '. Skipping...\n')
                    continue

                # Extract Team names
                home_team_element = game_locator.locator(".col1")
                home_team = home_team_element.inner_text()
                away_team_element = game_locator.locator(".col2")
                away_team = away_team_element.inner_text()

                # Print game details
                print(home_team + " - " + away_team)

                # Find quotes element
                quotes_element = game_locator.locator(".wettquote-link")
                debug(f'{quotes_element=}')

                # quotes_element = game_element
                if quotes_element:
                    quotes_raw = quotes_element.inner_text()
                else:
                    print("Quotes not found")
                    continue

                # Extract quotes and clean
                quotes_sanitized = quotes_raw.replace("Quote: ", "")
                if quotes_sanitized.find("/") != -1:
                    quotes = quotes_sanitized.split(" / ")
                elif quotes_sanitized.find(" | ") != -1:
                    quotes = quotes_sanitized.split(" | ")
                else:
                    print("Quotes not found")
                    continue

                # Print quotes
                print("Quotes:" + str(quotes))

                # Calculate tips
                tip = predict_with_win_loss_ratio(float(quotes[0]), float(quotes[2]), goals_so_far)
                print("Tip: " + str(tip), "\n")

                # Enter tips
                debug(f'{tippabgabe.inner_html()=}')
                home_tip_input = tippabgabe.locator("xpath=//input[2]")
                home_tip_input.fill(str(tip[0]))

                away_tip_input = tippabgabe.locator("xpath=//input[3]")
                away_tip_input.fill(str(tip[1]))

                page.get_by_role("button", name="Tipps speichern").click()

                # custom webhook to zapier
                send_zapier_webhook(time, home_team, away_team, quotes, tip)

                # ntfy notification
                send_ntfy_notification(time, home_team, away_team, quotes, tip)

        # Close browser
        browser.close()


def login(page):
    print("Logging in...")
    page.goto(LOGIN_URL)
    page.fill("#kennung", EMAIL)
    page.fill("#passwort", PASSWORD)
    page.get_by_role("button", name="Anmelden").click()
    if page.url == BASE_URL:
        print("Logged in!\n")
    else:
        print("Login failed!\n")

def send_zapier_webhook(time, home_team, away_team, quotes, tip):
    if ZAPIER_URL is not None:
        try:
            payload = {
                'date': time,
                'team1': home_team,
                'team2': away_team,
                'quoteteam1': quotes[0],
                'quotedraw': quotes[1],
                'quoteteam2': quotes[2],
                'tipteam1': tip[0],
                'tipteam2': tip[1]}
            files = []
            headers = {}

            requests.post(ZAPIER_URL, headers=headers,
                          data=payload, files=files)
        except IndexError:
            pass


def send_ntfy_notification(time, home_team, away_team, quotes, tip):
    if NTFY_URL is not None and NTFY_USERNAME is not None and NTFY_PASSWORD is not None:
        try:
            data = f"Time: {time.strftime('%d.%m.%y %H:%M')}; quotes={quotes}; ratio={tip[2]}; goals={tip[3]}"

            headers = {
                "X-Title": f"{home_team} - {away_team} tipped {tip[0]}:{tip[1]}",
            }

            # utf-8 encode headers
            headers = {k: v.encode('utf-8') for k, v in headers.items()}

            requests.post(NTFY_URL, auth=(
                NTFY_USERNAME, NTFY_PASSWORD), data=data, headers=headers)

        except IndexError:
            pass

def lambda_handler(_event, _context):

    # Check for valid log level names (case-insensitive)
    valid_log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    if LOG_LEVEL not in valid_log_levels:
        raise ValueError(f"Invalid log level: {LOG_LEVEL}. Valid levels are: {', '.join(valid_log_levels.keys())}")

    # Configure logging with the chosen level
    logging.basicConfig(level=valid_log_levels[LOG_LEVEL])

    if EMAIL is None or PASSWORD is None or NAME_OF_COMPETITION is None:
        print("Please set the environment variables KICKTIPP_EMAIL, KICKTIPP_PASSWORD and KICKTIPP_NAME_OF_COMPETITION")
        exit(1)

    now = datetime.now().strftime('%d.%m.%y %H:%M:%S')
    print(now + ": The script will execute now!\n")

    tip_all_games()

    print(now + ": The script has finished. Sleeping for 30 min...\n")
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

if __name__ == '__main__':
    lambda_handler(None, None)
