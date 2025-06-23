import tkinter as tk
from tkinter import messagebox, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager # No longer needed
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from datetime import datetime
import time
from dateutil.parser import parse
import threading
import logging
import os

# # Get current script directory
# base_dir = os.path.dirname(os.path.abspath(__file__)) # Now defined within setup_driver

# # Paths to Chrome binary and chromedriver
# chrome_path = os.path.join(base_dir, "chrome-win64", "chrome.exe") # Now defined within setup_driver
# driver_path = os.path.join(base_dir, "chromedriver.exe") # Now defined within setup_driver

# # Set Chrome binary location
# # options = Options() # Options are now local to setup_driver
# # options.binary_location = chrome_path

# # Optional: Run in headless or disable GPU
# # options.add_argument("--headless")
# # options.add_argument("--disable-gpu")

# # Create driver using Service + Options
# # service = Service(executable_path=driver_path) # Service is now local to setup_driver
# # driver = webdriver.Chrome(service=service, options=options) # This global driver is removed

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PasswordDialog:
    def __init__(self, parent, username):
        self.password = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("X.com Password")
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create widgets
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        tk.Label(main_frame, text=f"Enter password for @{username}:", font=('Arial', 10)).pack(pady=(0, 10))
        
        self.password_entry = tk.Entry(main_frame, show='*', width=30, font=('Arial', 10))
        self.password_entry.pack(pady=(0, 15))
        self.password_entry.focus()
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack()
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked, width=8).pack(side='left', padx=(0, 10))
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked, width=8).pack(side='left')
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
        # Protocol for window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
    
    def ok_clicked(self):
        self.password = self.password_entry.get()
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.password = None
        self.dialog.destroy()

class XItemDeleter:
    def __init__(self, root):
        self.root = root
        self.root.title("X Item Deleter")
        self.root.geometry("450x380")
        self.root.resizable(False, False)
        
        # Create main frame
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Username field
        tk.Label(main_frame, text="X Username:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        self.username_entry = tk.Entry(main_frame, width=40, font=('Arial', 10))
        self.username_entry.pack(pady=(0, 10))
        self.username_entry.insert(0, "You username here")
        
        # Date fields
        date_frame = tk.Frame(main_frame)
        date_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(date_frame, text="Start Date (YYYY-MM-DD):", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.start_date_entry = tk.Entry(date_frame, width=40, font=('Arial', 10))
        self.start_date_entry.pack(pady=(5, 10))
        self.start_date_entry.insert(0, "2025-06-01")
        
        tk.Label(date_frame, text="End Date (YYYY-MM-DD):", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.end_date_entry = tk.Entry(date_frame, width=40, font=('Arial', 10))
        self.end_date_entry.pack(pady=(5, 10))
        self.end_date_entry.insert(0, "2025-06-23")

        # Item type selection
        tk.Label(main_frame, text="Item to Delete:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        self.item_type_var = tk.StringVar(value="Replies")
        self.item_type_combobox = ttk.Combobox(
            main_frame, 
            textvariable=self.item_type_var, 
            width=37,
            font=('Arial', 10),
            state='readonly'
        )
        self.item_type_combobox['values'] = ("Replies", "Posts", "Likes", "Quotes")
        self.item_type_combobox.pack(pady=(0, 15))
        
        # Control buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(0, 10))
        
        self.delete_button = tk.Button(
            button_frame, 
            text="Start Deletion", 
            command=self.start_deletion_thread,
            bg='#1DA1F2',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10, # Reduced padding to make space
            pady=5
        )
        self.delete_button.pack(side=tk.LEFT, padx=(0, 5), pady=5) # Pack to left

        self.stop_button = tk.Button(
            button_frame,
            text="Stop",
            command=self.stop_deletion, # To be implemented
            bg='#E0245E', # A contrasting color for stop
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10, # Reduced padding
            pady=5,
            state='disabled' # Initially disabled
        )
        self.stop_button.pack(side=tk.LEFT, padx=(5, 0), pady=5) # Pack to left of delete
        
        # Status and progress
        self.status_label = tk.Label(main_frame, text="Status: Ready", font=('Arial', 9))
        self.status_label.pack(pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, length=400, mode='indeterminate')
        self.progress_bar.pack(pady=(0, 10))
        
        # Results display
        self.results_text = tk.Text(main_frame, height=6, width=50, font=('Arial', 9))
        self.results_text.pack(fill='both', expand=True)
        
        # Add scrollbar to results
        scrollbar = tk.Scrollbar(main_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_text.yview)
        
        # Initialize state
        self.is_running = False
        self.driver = None

    def stop_deletion(self):
        """Signal the deletion process to stop."""
        if self.is_running:
            self.log_message("Stop request received. Finishing current operations gracefully...")
            self.update_status("Stopping...")
            self.is_running = False # Signal loops to terminate
            self.stop_button.config(state='disabled') # Disable stop button to prevent multiple clicks
        else:
            self.log_message("Stop requested, but no process is currently running.")

    def log_message(self, message):
        """Add message to results text area"""
        self.results_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()
        logger.info(message)

    def update_status(self, status):
        """Update status label"""
        self.status_label.config(text=f"Status: {status}")
        self.root.update_idletasks()

    def validate_inputs(self):
        """Validate all user inputs"""
        username = self.username_entry.get().strip()
        start_date_str = self.start_date_entry.get().strip()
        end_date_str = self.end_date_entry.get().strip()
        item_type = self.item_type_var.get()
        
        if not username:
            raise ValueError("Username is required")
        
        if not start_date_str or not end_date_str:
            raise ValueError("Both start and end dates are required")
        
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD")
        
        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")
        
        if not item_type:
            raise ValueError("Please select an item type to delete")
        
        return username, start_date, end_date, item_type

    def get_password(self, username):
        """Get password from user using custom dialog"""
        password_dialog = PasswordDialog(self.root, username)
        self.root.wait_window(password_dialog.dialog)
        
        if not password_dialog.password:
            raise ValueError("Password is required")
        return password_dialog.password

    def setup_driver(self):
        """Setup Chrome driver with proper options"""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Use local ChromeDriver and Chrome binary
        # Get current script directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        driver_path = os.path.join(base_dir, "chromedriver.exe")
        chrome_path = os.path.join(base_dir, "chrome-win64", "chrome.exe")

        if not os.path.exists(driver_path):
            self.log_message(f"Error: chromedriver.exe not found at {driver_path}")
            self.update_status("Error: chromedriver.exe not found")
            raise FileNotFoundError(f"chromedriver.exe not found at {driver_path}")
        
        if not os.path.exists(chrome_path):
            self.log_message(f"Warning: Chrome binary not found at {chrome_path}. Selenium will try to use system Chrome.")
        else:
            options.binary_location = chrome_path
            self.log_message(f"Using Chrome binary from: {chrome_path}")

        self.log_message(f"Using ChromeDriver from: {driver_path}")
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

    def login_to_x(self, username, password):
        """Login to X.com"""
        self.update_status("Logging in to X.com...")
        self.log_message("Navigating to X.com login page...")
        
        try:
            self.driver.get("https://x.com/login")
            
            # Wait for and fill username
            self.log_message("Waiting for login page to load...")
            username_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, 'text'))
            )
            
            self.log_message("Entering username...")
            username_input.clear()
            username_input.send_keys(username)
            
            # Click next button - try multiple selectors
            self.log_message("Clicking Next button...")
            next_button = None
            next_selectors = [
                "//span[text()='Next']",
                "//div[@role='button']//span[contains(text(), 'Next')]",
                "//button[contains(@class, 'r-13qz1uu')]//span[text()='Next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not next_button:
                raise Exception("Could not find Next button")
            
            self.driver.execute_script("arguments[0].click();", next_button)
            time.sleep(3)
            
            # Handle phone verification if needed
            try:
                self.log_message("Checking for phone verification...")
                phone_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.NAME, 'text'))
                )
                
                # Check if we're on phone verification page
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
                if 'phone' in page_text or 'verify' in page_text:
                    self.log_message("Phone verification detected - entering phone number...")
                    phone_input.clear()
                    phone_input.send_keys('01159049348')
                    
                    # Click next again
                    for selector in next_selectors:
                        try:
                            next_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            self.driver.execute_script("arguments[0].click();", next_button)
                            break
                        except TimeoutException:
                            continue
                    time.sleep(3)
                    
            except TimeoutException:
                self.log_message("No phone verification required")
            
            # Enter password
            self.log_message("Entering password...")
            password_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, 'password'))
            )
            password_input.clear()
            password_input.send_keys(password)
            
            # Click login button - try multiple selectors
            self.log_message("Clicking Login button...")
            login_selectors = [
                "//span[text()='Log in']",
                "//div[@role='button']//span[contains(text(), 'Log in')]",
                "//button[contains(@data-testid, 'LoginForm_Login_Button')]"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not login_button:
                raise Exception("Could not find Login button")
            
            self.driver.execute_script("arguments[0].click();", login_button)
            time.sleep(5)
            
            # Verify login success - try multiple indicators
            self.log_message("Verifying login success...")
            success_selectors = [
                "//a[@aria-label='Home']",
                "//a[@data-testid='AppTabBar_Home_Link']",
                "//div[@data-testid='primaryColumn']"
            ]
            
            login_successful = False
            for selector in success_selectors:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    login_successful = True
                    break
                except TimeoutException:
                    continue
            
            if not login_successful:
                # Check if we're still on login page or error page
                current_url = self.driver.current_url.lower()
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
                
                if 'login' in current_url or 'error' in page_text or 'incorrect' in page_text:
                    raise Exception("Login failed - check your credentials")
                else:
                    self.log_message("Login may have succeeded but verification is uncertain")
            
            self.log_message("Login successful!")
            
        except TimeoutException as e:
            raise Exception(f"Login timeout: {str(e)}")
        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")

    def navigate_to_content(self, username, item_type, start_date_str, end_date_str):
        """Navigate to the appropriate content page"""
        self.update_status(f"Navigating to {item_type} page...")
        
        if item_type == "Replies":
            url = f"https://x.com/{username}/with_replies"
        elif item_type == "Posts":
            url = f"https://x.com/{username}"
        elif item_type == "Likes":
            url = f"https://x.com/{username}/likes"
        elif item_type == "Quotes":
            search_query = f"(from:{username}) filter:quote until:{end_date_str} since:{start_date_str}"
            url = f"https://x.com/search?q={search_query}&src=typed_query&f=live"
        else:
            raise ValueError(f"Unknown item type: {item_type}")
        
        self.log_message(f"Navigating to: {url}")
        self.driver.get(url)
        
        # Wait for content to load
        WebDriverWait(self.driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "main[role='main']"))
        )
        time.sleep(3)

    def scroll_element_into_view(self, element):
        """Scroll element into view and ensure it's clickable"""
        try:
            # Scroll element into center of viewport
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
            """, element)
            time.sleep(0.5)
            
            # Additional check to ensure element is in viewport
            self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                if (rect.top < 0 || rect.bottom > window.innerHeight) {
                    arguments[0].scrollIntoView({block: 'center'});
                }
            """, element)
            time.sleep(0.3)
            
        except Exception as e:
            self.log_message(f"Warning: Could not scroll element into view: {e}")

    def wait_for_element_clickable(self, parent, selector, timeout=10):
        """Wait for element to be clickable with better error handling"""
        try:
            element = WebDriverWait(parent, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            return element
        except TimeoutException:
            # Try finding by different selectors
            alternative_selectors = {
                "button[data-testid='caret']": [
                    "button[aria-label='More']",
                    "button[role='button'][aria-haspopup='menu']",
                    ".//button[contains(@aria-label, 'More')]",
                    ".//div[@role='button'][contains(@aria-label, 'More')]"
                ]
            }
            
            if selector in alternative_selectors:
                for alt_selector in alternative_selectors[selector]:
                    try:
                        if alt_selector.startswith('.//'):
                            element = parent.find_element(By.XPATH, alt_selector)
                        else:
                            element = parent.find_element(By.CSS_SELECTOR, alt_selector)
                        if element.is_enabled() and element.is_displayed():
                            return element
                    except:
                        continue
            
            raise TimeoutException(f"Could not find clickable element: {selector}")

    def delete_item(self, article, item_type, username):
        """Delete a single item"""
        try:
            # Scroll article into view first
            self.scroll_element_into_view(article)
            
            if item_type == "Likes":
                # Unlike the post
                self.scroll_element_into_view(article)
                unlike_button = self.wait_for_element_clickable(article, "button[data-testid='unlike']", 5)
                self.driver.execute_script("arguments[0].click();", unlike_button)
                time.sleep(0.7)
                return True
            else:
                # For posts, replies, and quotes - use delete menu
                menu_button_found_and_clicked = False

                if item_type == "Replies":
                    self.log_message(f"Attempting to delete a reply. Verifying ownership by @{username}...")
                    # Replies need special handling to ensure we're deleting the user's own reply,
                    # especially when it's part of a thread displayed in a single <article>.

                    # Find all potential tweet/reply content cells within the article.
                    # These often have 'cellInnerDiv' or similar structure.
                    # We look for a cell that contains a link to the user's profile.
                    potential_reply_cells = article.find_elements(By.XPATH, ".//div[div//a[@href='/" + username + "']]")
                    if not potential_reply_cells: # Fallback to a broader cell search if specific link isn't found at this stage
                        potential_reply_cells = article.find_elements(By.XPATH, ".//div[@data-testid='cellInnerDiv']")

                    found_user_reply_cell = None
                    for cell in potential_reply_cells:
                        try:
                            # Check if this cell directly contains the user's profile link and is visible.
                            # This helps ensure it's the user's actual reply content.
                            user_link = cell.find_element(By.XPATH, f".//a[@href='/{username}' and @role='link'][.//span[contains(text(), '@{username}')]]")
                            if user_link.is_displayed():
                                # Check if this cell also contains a time element, typical for actual tweets/replies
                                if cell.find_elements(By.CSS_SELECTOR, "time"):
                                    found_user_reply_cell = cell
                                    self.log_message(f"Identified a reply cell by @{username}.")
                                    break
                        except NoSuchElementException:
                            continue

                    if found_user_reply_cell:
                        # Search for the caret button within this specific user's reply cell
                        try:
                            self.log_message("Looking for menu button in user's reply cell...")
                            menu_button = self.wait_for_element_clickable(found_user_reply_cell, "button[data-testid='caret']", 5)
                            self.scroll_element_into_view(menu_button)
                            self.log_message("Clicking menu button for user's reply...")
                            self.driver.execute_script("arguments[0].click();", menu_button)
                            time.sleep(1)
                            menu_button_found_and_clicked = True
                        except TimeoutException:
                            self.log_message("Could not find menu button in the identified user's reply cell.")
                        except Exception as e_cell:
                            self.log_message(f"Error clicking menu button in user's reply cell: {e_cell}")
                    else:
                        self.log_message(f"Could not definitively identify a specific reply cell by @{username} within this article. Skipping for safety.")
                        return False # Important: if we can't be sure, don't delete.

                elif item_type == "Quotes":
                    # Verify it's user's own quote
                    try:
                        # Check for user's name/link in the quoting part of the tweet
                        quote_author_xpath = f".//div[@data-testid='tweetText']//a[@href='/{username}'] | .//a[contains(@href, '/{username}/status')]//span[contains(text(),'{username}')]"
                        author_links = article.find_elements(By.XPATH, quote_author_xpath)

                        if not any(link.is_displayed() for link in author_links):
                             self.log_message(f"This quote does not appear to be by @{username}. Skipping.")
                             return False
                    except NoSuchElementException:
                        self.log_message(f"Could not verify quote author for @{username}. Skipping.")
                        return False

                    # If verified, proceed to click the general caret button for the article
                    self.log_message("Looking for menu button for user's quote...")
                    menu_button = self.wait_for_element_clickable(article, "button[data-testid='caret']", 8)
                    self.scroll_element_into_view(menu_button)
                    self.log_message("Clicking menu button for user's quote...")
                    self.driver.execute_script("arguments[0].click();", menu_button)
                    time.sleep(1)
                    menu_button_found_and_clicked = True
                
                else: # For "Posts" or other types not "Likes" or "Replies" or "Quotes"
                    # This is the original behavior for items like user's own main posts.
                    self.log_message("Looking for menu button (general)...")
                    menu_button = self.wait_for_element_clickable(article, "button[data-testid='caret']", 8)
                    self.scroll_element_into_view(menu_button)
                    self.log_message("Clicking menu button (general)...")
                    self.driver.execute_script("arguments[0].click();", menu_button)
                    time.sleep(1)
                    menu_button_found_and_clicked = True

                if not menu_button_found_and_clicked:
                    self.log_message("Menu button not clicked. Cannot proceed with deletion for this item.")
                    # Attempt to close any unintentionally opened menu if possible
                    try:
                        body_element = self.driver.find_element(By.TAG_NAME, 'body')
                        body_element.click() # Clicking body might close an open menu
                        time.sleep(0.5)
                    except: # nosec
                        pass
                    return False

                # Common deletion steps (delete option, confirm button)
                self.log_message("Looking for delete option...")
                delete_selectors = [
                    "//div[@role='menuitem']//span[contains(text(), 'Delete')]",
                    "//div[@role='menuitem']//span[contains(text(), 'حذف')]",  # Arabic
                    "//div[contains(@class, 'css-1dbjc4n')]//span[contains(text(), 'Delete')]",
                    "//div[@data-testid='Dropdown']//span[contains(text(), 'Delete')]"
                ]
                
                delete_option = None
                for selector in delete_selectors:
                    try:
                        delete_option = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if not delete_option:
                    self.log_message("Could not find delete option in menu")
                    return False
                
                self.log_message("Clicking delete option...")
                self.driver.execute_script("arguments[0].click();", delete_option)
                time.sleep(1)
                
                # Confirm deletion
                self.log_message("Looking for confirmation button...")
                confirm_selectors = [
                    "button[data-testid='confirmationSheetConfirm']",
                    "button[role='button'][data-testid='confirmationSheetConfirm']",
                    "//button//span[contains(text(), 'Delete')]",
                    "//button//span[contains(text(), 'حذف')]"  # Arabic
                ]
                
                confirm_button = None
                for selector in confirm_selectors:
                    try:
                        if selector.startswith('//'):
                            confirm_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            confirm_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        break
                    except TimeoutException:
                        continue
                
                if not confirm_button:
                    self.log_message("Could not find confirmation button")
                    return False
                
                self.log_message("Confirming deletion...")
                self.driver.execute_script("arguments[0].click();", confirm_button)
                time.sleep(1.5)
                return True
                
        except Exception as e:
            self.log_message(f"Error in delete_item: {str(e)}")
            return False

    def process_items(self, username, start_date, end_date, item_type):
        """Process and delete items"""
        deleted_count = 0
        failed_count = 0
        processed_count = 0
        
        self.update_status(f"Processing {item_type.lower()}...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        no_new_content_count = 0
        
        while self.is_running:
            # Find all articles on current page
            articles = self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
            
            if not articles:
                self.log_message("No articles found, scrolling...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                continue
            
            page_processed = 0
            articles_to_process = []
            
            # First pass: collect articles in date range
            for article in articles:
                if not self.is_running:
                    break
                    
                try:
                    # Get post date
                    time_element = article.find_element(By.CSS_SELECTOR, "time")
                    post_date_str = time_element.get_attribute("datetime")
                    
                    if not post_date_str:
                        continue
                    
                    post_date = parse(post_date_str).replace(tzinfo=None)
                    
                    # Check if post is in date range
                    if start_date <= post_date <= end_date:
                        articles_to_process.append(article)
                        
                except Exception as e:
                    self.log_message(f"Error checking article date: {str(e)}")
                    continue
            
            # Second pass: process articles
            for article in articles_to_process:
                if not self.is_running:
                    break
                
                try:
                    processed_count += 1
                    page_processed += 1
                    
                    self.log_message(f"Processing item #{processed_count}...")
                    
                    # Scroll to article and ensure it's visible
                    self.scroll_element_into_view(article)
                    
                    # Small delay to ensure scrolling is complete
                    time.sleep(0.5)
                    
                    # Delete the item
                    if self.delete_item(article, item_type, username):
                        deleted_count += 1
                        self.log_message(f"✓ Successfully deleted {item_type.lower()} #{deleted_count}")
                    else:
                        failed_count += 1
                        self.log_message(f"✗ Failed to delete item #{processed_count}")
                    
                    self.update_status(f"Processed: {processed_count}, Deleted: {deleted_count}, Failed: {failed_count}")
                    
                    # Small delay between deletions to avoid rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    failed_count += 1
                    self.log_message(f"✗ Error processing item #{processed_count}: {str(e)}")
                    continue
            
            # If we processed items, scroll a bit to refresh the page
            if page_processed > 0:
                self.log_message(f"Processed {page_processed} items on this page section")
                # Scroll up a bit then down to refresh content
                self.driver.execute_script("window.scrollBy(0, -200);")
                time.sleep(1)
                self.driver.execute_script("window.scrollBy(0, 400);")
                time.sleep(2)
            
            # Scroll to load more content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Check if we've reached the end
            if new_height == last_height:
                no_new_content_count += 1
                if no_new_content_count >= 3:  # No new content for 3 consecutive scrolls
                    self.log_message("Reached end of content")
                    break
            else:
                no_new_content_count = 0
                last_height = new_height
        
        return deleted_count, failed_count, processed_count

    def start_deletion_thread(self):
        """Start deletion process in separate thread"""
        if self.is_running:
            return
        
        thread = threading.Thread(target=self.perform_deletion)
        thread.daemon = True
        thread.start()

    def perform_deletion(self):
        """Main deletion process"""
        try:
            # Validate inputs
            username, start_date, end_date, item_type = self.validate_inputs()
            
            # Get password
            password = self.get_password(username)
            
            # Set running state
            self.is_running = True
            self.delete_button.config(state='disabled', text='Running...')
            self.stop_button.config(state='normal') # Enable Stop button
            self.progress_bar.start()
            
            # Clear results
            self.results_text.delete(1.0, tk.END)
            
            # Setup driver
            self.log_message("Setting up browser...")
            self.driver = self.setup_driver()
            
            # Login
            self.login_to_x(username, password)
            
            # Navigate to content
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            self.navigate_to_content(username, item_type, start_date_str, end_date_str)
            
            # Process items
            deleted_count, failed_count, processed_count = self.process_items(
                username, start_date, end_date, item_type
            )
            
            # Show results
            final_status_message = "Process completed!"
            final_ui_status = "Completed"

            # Check if the process was stopped prematurely by the user
            # self.is_running will be false here anyway if stop_deletion was called.
            # A more reliable check is the status label text set by stop_deletion.
            if "Stopping..." in self.status_label.cget("text") or "Stopped by user" in self.status_label.cget("text"):
                final_status_message = "Process stopped by user."
                final_ui_status = "Stopped by user"

            self.log_message(final_status_message)
            self.log_message(f"Total processed: {processed_count}")
            self.log_message(f"Successfully deleted: {deleted_count}")
            self.log_message(f"Failed: {failed_count}")
            
            self.update_status(final_ui_status) # This will be handled by finally too, but good to be explicit
            
            messagebox.showinfo(
                final_ui_status.capitalize(), # "Process Complete" or "Stopped by user"
                f"Deleted {deleted_count} {item_type.lower()}\n"
                f"Failed: {failed_count}\n"
                f"Total processed: {processed_count}"
            )
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            self.log_message(f"Input error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.log_message(f"Error: {str(e)}")
        finally:
            # Cleanup
            self.is_running = False # Ensure this is set before UI updates if stop_deletion wasn't called
            self.progress_bar.stop()
            self.delete_button.config(state='normal', text='Start Deletion')
            self.stop_button.config(state='disabled') # Disable Stop button
            
            # Update status only if not already set to a specific "stopped" message
            if "Stopping..." not in self.status_label.cget("text") and "Stopped by user" not in self.status_label.cget("text"):
                self.update_status("Ready")
            elif "Stopping..." in self.status_label.cget("text"): # If it was stopping, now it's fully stopped.
                self.update_status("Stopped by user")

            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None

if __name__ == "__main__":
    root = tk.Tk()
    app = XItemDeleter(root)
    root.mainloop()