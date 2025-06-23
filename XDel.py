import tkinter as tk
from tkinter import messagebox, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
from dateutil.parser import parse # Used for parsing datetime strings from tweet elements
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class XReplyDeleter:
    def __init__(self, root):
        self.root = root
        self.root.title("X Item Deleter") # Renamed for broader scope
        self.root.geometry("400x320") # Adjusted height slightly for better layout
        
        # --- GUI Elements ---
        tk.Label(root, text="X Username:").pack(pady=5)
        self.username_entry = tk.Entry(root, width=30)
        self.username_entry.pack(pady=5)
        # self.username_entry.insert(0, "your_username") # Example placeholder, removed default
        
        tk.Label(root, text="Start Date (YYYY-MM-DD):").pack(pady=5)
        self.start_date_entry = tk.Entry(root, width=30) # Renamed for clarity
        self.start_date_entry.pack(pady=5)
        
        tk.Label(root, text="End Date (YYYY-MM-DD):").pack(pady=5)
        self.end_date_entry = tk.Entry(root, width=30) # Renamed for clarity
        self.end_date_entry.pack(pady=5)

        tk.Label(root, text="Item to Delete:").pack(pady=5)
        self.item_type_var = tk.StringVar()
        self.item_type_combobox = ttk.Combobox(root, textvariable=self.item_type_var, width=27)
        self.item_type_combobox['values'] = ("Replies", "Posts", "Likes", "Quotes")
        self.item_type_combobox.current(0)  # Default to "Replies"
        self.item_type_combobox.pack(pady=5)
        
        self.delete_button = tk.Button(root, text="Start Deletion", command=self.start_deletion_process)
        self.delete_button.pack(pady=10)
        
        self.status_label = tk.Label(root, text="Status: Idle") # Renamed for clarity
        self.status_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(root, length=300, mode='indeterminate') # Renamed
        self.progress_bar.pack(pady=5)

    def validate_dates(self, start_date_str, end_date_str):
        """
        Validates the start and end date strings against "YYYY-MM-DD" format
        and ensures start_date is not after end_date.
        Returns (parsed_start_date, parsed_end_date, error_message_or_none).
        """
        if not start_date_str or not end_date_str:
            return None, None, "Please fill all date fields!"

        try:
            # Use datetime.strptime for strict "YYYY-MM-DD" format validation.
            start = datetime.strptime(start_date_str, "%Y-%m-%d")
            end = datetime.strptime(end_date_str, "%Y-%m-%d")

            # strptime produces timezone-naive datetime objects by default.
            if start > end:
                return None, None, "Start date must be before or the same as end date."
            return start, end, None
        except ValueError: # Raised by strptime if format is wrong.
            return None, None, "Invalid date format! Please use YYYY-MM-DD."

    def start_deletion_process(self): # Renamed for clarity
        """Handles pre-deletion checks (input validation, password prompt) and initiates deletion."""
        from tkinter.simpledialog import askstring # Local import for password dialog

        username = self.username_entry.get()
        start_date_str = self.start_date_entry.get()
        end_date_str = self.end_date_entry.get()
        item_type = self.item_type_var.get()
        
        if not username or not start_date_str or not end_date_str:
            messagebox.showerror("Input Error", "Please fill all required fields (Username, Start Date, End Date).")
            return

        start_date_obj, end_date_obj, error_msg = self.validate_dates(start_date_str, end_date_str)
        if error_msg:
            messagebox.showerror("Date Validation Error", error_msg)
            return

        # Securely get password via dialog
        password = askstring("X.com Password", f"Enter X.com password for user '{username}':", show='*')
        if not password: # User cancelled or entered empty password
            messagebox.showinfo("Cancelled", "Deletion process cancelled by user (password not provided).")
            return
        
        # Update GUI for processing state
        self.delete_button.config(state='disabled')
        self.progress_bar.start()
        self.status_label.config(text=f"Starting deletion of {item_type.lower()}...")
        self.root.update_idletasks() # Ensure GUI updates immediately
        
        # Initiate the core deletion logic
        # Pass original date strings for URL construction (especially for Quotes search)
        self.perform_item_deletion(username, password, start_date_obj, end_date_obj, item_type, start_date_str, end_date_str)
        
    def _login_to_x(self, driver, username, password): # Prefixed with _ as it's an internal helper
        """Handles the automated login process on X.com."""
        try:
            # Wait for username input field
            user_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, 'text')),
                message="Username input field not found on login page."
            )
            user_input.clear()
            user_input.send_keys(username)

            # Click "Next" button (with fallbacks for robustness)
            next_btn = None
            try:
                next_btn_xpath = "//span[contains(text(),'Next')]/ancestor::div[@role='button'] | //span[contains(text(),'التالي')]/ancestor::div[@role='button']"
                next_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, next_btn_xpath)),
                    message="Primary 'Next' button selector failed."
                )
            except Exception: # Broader exception for timeout or other issues
                btns = driver.find_elements(By.XPATH, "//div[@role='button']")
                for btn in btns:
                    if btn.is_displayed() and btn.is_enabled():
                        btn_text_lower = btn.text.lower()
                        if "next" in btn_text_lower or "التالي" in btn_text_lower or len(btns) == 1:
                            next_btn = btn; break
            if not next_btn:
                clickable_buttons = [b for b in driver.find_elements(By.XPATH, "//div[@role='button']") if b.is_displayed() and b.is_enabled()]
                if len(clickable_buttons) == 1: next_btn = clickable_buttons[0]
                elif len(clickable_buttons) > 1:
                    for cb in clickable_buttons:
                        spans = cb.find_elements(By.TAG_NAME, "span")
                        if spans and spans[0].is_displayed() and ("next" in spans[0].text.lower() or "التالي" in spans[0].text.lower()):
                            next_btn = cb; break
                if not next_btn: raise Exception("Next button not found or ambiguous on login page after multiple fallbacks.")

            driver.execute_script("arguments[0].click();", next_btn)

            # Wait for password input field
            pwd_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, 'password')),
                message="Password input field not found after clicking Next."
            )
            pwd_input.clear()
            pwd_input.send_keys(password)

            # Click "Log in" button
            login_btn_xpath = "//span[contains(text(),'Log in')]/ancestor::div[@role='button'] | //span[contains(text(),'تسجيل الدخول')]/ancestor::div[@role='button'] | //div[@data-testid='LoginForm_Login_Button']"
            login_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, login_btn_xpath)),
                message="'Log in' button not found."
            )
            driver.execute_script("arguments[0].click();", login_btn)
            # Successful login is confirmed in the calling method.
        except Exception as e:
            error_detail = f"Automated login failed: {str(e)}"
            print(error_detail)
            messagebox.showerror("Login Error", error_detail)
            raise # Re-raise to be caught by the main deletion logic

    def perform_item_deletion(self, username, password, start_date_obj, end_date_obj, item_type, start_date_str, end_date_str): # Renamed
        """Core logic for Selenium browser automation to delete items."""
        driver = None
        items_deleted_count = 0
        items_failed_count = 0
        try:
            # --- WebDriver Setup ---
            options = webdriver.ChromeOptions()
            # options.add_argument("--headless") # Enable for no GUI browser; may affect X.com compatibility
            # options.add_argument("--disable-gpu")
            # options.add_argument("--no-sandbox")
            # options.add_argument("--window-size=1920,1080")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            self.status_label.config(text="Attempting to log in to X.com...")
            self.root.update_idletasks()

            # --- Login ---
            driver.get("https://x.com/login")
            WebDriverWait(driver, 20).until( # Wait for login page readiness
                lambda d: "login" in d.title.lower() or d.find_elements(By.NAME, 'text'),
                message="Failed to load X.com login page."
            )
            self._login_to_x(driver, username, password) # Call internal login helper

            # --- Login Confirmation ---
            try: # Check for a known element post-login (e.g., Home button)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Home']|//a[@data-testid='AppTabBar_Home_Link']")),
                    message="Login confirmation element (Home link) not found."
                )
                self.status_label.config(text="Login successful. Navigating...")
                self.root.update_idletasks()
            except Exception as login_confirm_ex:
                current_url = driver.current_url
                error_detail = f"Original error: {login_confirm_ex}. Current URL: {current_url}"
                if "login" in current_url or "error" in current_url or "i/flow/login" in current_url:
                    messagebox.showerror("Login Failed", f"Could not confirm login. URL suggests still on login/error page. {error_detail}")
                else:
                    messagebox.showwarning("Login Status Uncertain", f"Login status uncertain. {error_detail}")
                # Consider halting if login is critical: if driver: driver.quit(); return
                self.status_label.config(text="Login confirmation failed or uncertain.")
                self.root.update_idletasks()
                # For robustness, we might allow proceeding, but it's risky. Here, we'll stop.
                if driver: driver.quit()
                self.progress_bar.stop()
                self.delete_button.config(state='normal')
                return


            # --- Navigation to Target Page ---
            base_url = "https://x.com"
            target_url = ""
            self.status_label.config(text=f"Navigating to {item_type} section...")
            self.root.update_idletasks()

            if item_type == "Replies": target_url = f"{base_url}/{username}/with_replies"
            elif item_type == "Posts": target_url = f"{base_url}/{username}"
            elif item_type == "Likes": target_url = f"{base_url}/{username}/likes"
            elif item_type == "Quotes":
                if not start_date_str or not end_date_str:
                    raise ValueError("Start/End date strings required for Quotes search URL.")
                # Use original string dates for X.com search query format
                search_query = f"(from%3A{username})%20filter%3Aquote%20until%3A{end_date_str}%20since%3A{start_date_str}"
                target_url = f"{base_url}/search?q={search_query}&src=typed_query&f=live"

            if target_url:
                driver.get(target_url)
                # Wait for main content area to load
                WebDriverWait(driver, 25).until( # Increased wait for page load
                    EC.presence_of_element_located((By.CSS_SELECTOR, "main[role='main'], div[data-testid='primaryColumn']")),
                    message=f"Failed to load content for {item_type} page: {target_url}"
                )
                time.sleep(3) # Increased pause for dynamic content, especially after search/navigation
            else:
                messagebox.showerror("Internal Error", f"Unknown item_type for URL: {item_type}")
                raise ValueError(f"Unknown item_type for URL: {item_type}") # Stop execution

            # --- Item Deletion Loop ---
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                self.status_label.config(text=f"Scanning for {item_type.lower()}... Deleted: {items_deleted_count}, Failed: {items_failed_count}")
                self.root.update_idletasks()

                articles = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                if not articles: # If no articles, try a page retry button if present
                    retry_buttons = driver.find_elements(By.XPATH, "//span[contains(text(), 'Try again')]|//span[contains(text(), 'Retry')]")
                    if retry_buttons and retry_buttons[0].is_displayed():
                        try:
                            self.status_label.config(text="No items visible, clicking page retry button..."); self.root.update_idletasks()
                            driver.execute_script("arguments[0].click();", retry_buttons[0])
                            time.sleep(3.5); articles = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                        except Exception as retry_ex: print(f"Error clicking retry: {retry_ex}")

                page_processed_items_this_scroll = 0
                for article_idx, article in enumerate(articles):
                    try:
                        date_elem = WebDriverWait(article, 7).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "time")),
                            message=f"Time element not found in article {article_idx + 1}"
                        )
                        post_date_str = date_elem.get_attribute("datetime")
                        if not post_date_str: print(f"Article {article_idx+1} missing datetime. Skipping."); continue
                        post_date = parse(post_date_str)

                        if not (start_date_obj <= post_date.replace(tzinfo=None) <= end_date_obj):
                            continue
                        page_processed_items_this_scroll += 1

                        if item_type == "Likes":
                            unlike_btn = WebDriverWait(article, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='unlike']")), "Unlike button error.")
                            driver.execute_script("arguments[0].click();", unlike_btn); time.sleep(0.7)
                            items_deleted_count += 1; self.status_label.config(text=f"Unliked {items_deleted_count} items")
                        else: # Posts, Replies, Quotes
                            if item_type == "Quotes": # Verify authorship for Quotes from search
                                is_own_quote = False
                                try: # More robust check for user's own quote
                                    author_links = article.find_elements(By.XPATH, f".//div[@data-testid='User-Name']//a[@href='/{username.lower()}' and .//span[contains(text(), '@{username.lower()}')]]")
                                    if any(link.is_displayed() for link in author_links): is_own_quote = True
                                except Exception as q_auth_ex: print(f"Quote author check error: {q_auth_ex}")
                                if not is_own_quote: continue # Skip if not confirmed user's quote

                            menu_btn = WebDriverWait(article, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='caret']")), "Menu button error.")
                            driver.execute_script("arguments[0].click();", menu_btn)

                            del_opt_xpath = "//div[@role='menuitem' and (.//span[contains(text(),'Delete')] or .//span[contains(text(),'حذف')])]"
                            del_opt = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, del_opt_xpath)), "Delete option error.")
                            driver.execute_script("arguments[0].click();", del_opt)

                            conf_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='confirmationSheetConfirm']")), "Confirm button error.")
                            driver.execute_script("arguments[0].click();", conf_btn); time.sleep(1.8)
                            items_deleted_count += 1; self.status_label.config(text=f"Deleted {items_deleted_count} {item_type.lower()}")
                        
                        self.root.update_idletasks()
                    except Exception as post_ex:
                        items_failed_count += 1
                        print(f"Could not process item {article_idx + 1}: {post_ex}")
                        self.status_label.config(text=f"Deleted: {items_deleted_count}, Failed: {items_failed_count}. Item error.")
                        self.root.update_idletasks()
                        # Consider driver.send_keys(Keys.ESCAPE) to close potential popups/menus
                        continue
                
                # --- Scroll and Check End Conditions ---
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3) # Wait for new content loading
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height: # Height unchanged
                    if page_processed_items_this_scroll == 0: # And no items processed in this view
                        time.sleep(2.5) # Final wait for any very late content
                        articles_after_wait = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                        page_text_lower = driver.find_element(By.TAG_NAME, 'body').text.lower()
                        end_phrases = ["you're all caught up", "no more tweets", "no results for", "no likes yet", "you don't have any likes yet"]
                        if any(phrase in page_text_lower for phrase in end_phrases) or not articles_after_wait:
                            self.status_label.config(text=f"End of content detected for {item_type.lower()}."); break
                    # If items were processed, continue even if height is same (dynamic loading might not change total height)
                last_height = new_height
            
            # --- Process Finished ---
            self.status_label.config(text=f"Deletion process completed for {item_type.lower()}.")
        except ValueError as ve: # Specific error for known issues like bad item_type
            messagebox.showerror("Configuration Error", str(ve))
            self.status_label.config(text="Configuration error.")
        except Exception as e: # Catch-all for Selenium or other unexpected errors
            print(f"An unhandled error occurred in deletion process: {e}")
            messagebox.showerror("Critical Error", f"An critical error occurred: {str(e)}")
            self.status_label.config(text="Critical error during deletion!")
        finally: # Ensure cleanup and GUI reset
            if driver: driver.quit()
            self.progress_bar.stop()
            self.delete_button.config(state='normal')
            final_msg = f"Finished! Deleted: {items_deleted_count} {item_type.lower()}."
            if items_failed_count > 0: final_msg += f" Failed: {items_failed_count}."
            self.status_label.config(text=final_msg)
            if items_deleted_count > 0 or items_failed_count > 0 : # Only show final popup if actions were attempted
                 messagebox.showinfo("Process Finished", final_msg)
            elif not 've' in locals() and not 'e' in locals(): # No errors and no items processed implies nothing to do
                 messagebox.showinfo("Process Finished", f"No {item_type.lower()} found in the specified date range.")


if __name__ == "__main__":
    # --- Main Application Setup ---
    root = tk.Tk()  # Create the main Tkinter window
    app = XReplyDeleter(root)  # Instantiate the application class
    root.mainloop()  # Start the Tkinter event loop to display GUI and handle events
