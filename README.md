# Tweety-selenium (X Reply Deleter)

This Python application uses Tkinter for its GUI and Selenium to automate the deletion of your X (formerly Twitter) content, including replies, posts, likes, and quotes within a specified date range.

## How to Run

1.  **Prerequisites:**
    *   Python 3.x installed.
    *   Google Chrome browser installed.
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(If a `requirements.txt` is not available, you'll need to install dependencies manually: `pip install selenium webdriver-manager python-dateutil`)*
3.  **Run the Application:**
    ```bash
    python XDel.py
    ```
4.  **Usage:**
    *   Enter your X.com username.
    *   Enter the start and end dates (YYYY-MM-DD) for the content you wish to delete.
    *   Select the type of item to delete (Replies, Posts, Likes, Quotes).
    *   Click "Start Deletion".
    *   You will be prompted for your X.com password.
    *   A Chrome browser window will open and automate the login and deletion process. Monitor the GUI for status updates.

## Limitations and Important Notes

*   **X.com UI Changes:** This script relies on specific HTML structures (selectors) of X.com. If X.com updates its website design, the script may break or fail to find elements correctly. This is a common challenge for web automation scripts and may require updates to the selectors in `XDel.py`.
*   **Login Security:**
    *   The script prompts for your password. While it uses Selenium to enter it into the official X.com login page, always be cautious with scripts that handle credentials. Review the code if you have concerns.
    *   X.com may present CAPTCHAs, 2FA prompts, or other security challenges during login that the script is not designed to handle. If this occurs, you may need to complete these steps manually in the browser window opened by Selenium, or the script might fail to log in.
*   **Rate Limiting/Account Action:** Automating actions on X.com could potentially trigger rate limits or other account actions if used excessively or if it violates X.com's terms of service. Use responsibly.
*   **Chrome Browser Required:** The script is currently configured to use Google Chrome and `webdriver-manager` to automatically download the correct ChromeDriver. Other browsers are not supported out-of-the-box.
*   **Error Handling:** While basic error handling is in place, unexpected scenarios during the Selenium interaction (e.g., sudden page changes, modals) might not be gracefully handled and could stop the script.
*   **Deletion is Permanent:** Items deleted by this script are permanently removed from your X.com account. There is no undo feature. Use with caution and double-check your date ranges.
*   **Language Dependency:** Some selectors, particularly for "Delete" or "Next" buttons, might be language-dependent. The script includes some fallbacks but is primarily tested with English interface elements. If your X.com interface is in a different language, selectors might need adjustment.
*   **"Headless" Mode:** Running in headless mode (browser not visible) is commented out by default. While it can be enabled, some websites, including X.com, may have stricter bot detection or behave differently in headless mode, potentially reducing reliability.
*   **Performance:** Deleting a very large number of items can take a significant amount of time. The script processes items one by one by scrolling and interacting with the page.

## Development

*   Unit tests for date validation are available in `test_xdel.py`. Run with `python -m unittest test_xdel.py`.