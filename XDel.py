import tkinter as tk
from tkinter import messagebox, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
from dateutil.parser import parse

class XReplyDeleter:
    def __init__(self, root):
        self.root = root
        self.root.title("X Reply Deleter")
        self.root.geometry("400x300")
        
        # GUI Elements
        tk.Label(root, text="X Username:").pack(pady=5)
        self.username_entry = tk.Entry(root)
        self.username_entry.pack(pady=5)
        
        tk.Label(root, text="Start Date (YYYY-MM-DD):").pack(pady=5)
        self.start_date = tk.Entry(root)
        self.start_date.pack(pady=5)
        
        tk.Label(root, text="End Date (YYYY-MM-DD):").pack(pady=5)
        self.end_date = tk.Entry(root)
        self.end_date.pack(pady=5)

        tk.Label(root, text="Item to Delete:").pack(pady=5)
        self.item_type_var = tk.StringVar()
        self.item_type_combobox = ttk.Combobox(root, textvariable=self.item_type_var)
        self.item_type_combobox['values'] = ("Replies", "Posts", "Likes", "Quotes")
        self.item_type_combobox.current(0)  # Default to Replies
        self.item_type_combobox.pack(pady=5)
        
        self.delete_button = tk.Button(root, text="Start Deletion", command=self.start_deletion)
        self.delete_button.pack(pady=10)
        
        self.status = tk.Label(root, text="")
        self.status.pack(pady=5)
        
        self.progress = ttk.Progressbar(root, length=200, mode='indeterminate')
        self.progress.pack(pady=5)

    def start_deletion(self):
        username = self.username_entry.get()
        start_date_str = self.start_date.get()
        end_date_str = self.end_date.get()
        item_type = self.item_type_var.get()
        
        if not username or not start_date_str or not end_date_str:
            messagebox.showerror("Error", "Please fill all fields!")
            return
        
        try:
            start = parse(start_date_str)
            end = parse(end_date_str)
            if start > end:
                messagebox.showerror("Error", "Start date must be before end date!")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD")
            return
        
        self.delete_button.config(state='disabled')
        self.progress.start()
        self.status.config(text=f"Starting deletion of {item_type.lower()}...")
        self.root.update()
        
        # Pass string dates for URL construction if needed, and parsed dates for comparison
        self.delete_items(username, start, end, item_type, start_date_str, end_date_str)
        
    def delete_items(self, username, start_date, end_date, item_type, start_date_str=None, end_date_str=None):
        driver = None  # Initialize driver to ensure it's available in finally block
        try:
            # Setup Selenium
            options = webdriver.ChromeOptions()
            # options.add_argument("--headless")  # Comment out for debugging, enable for release
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            # Navigate to appropriate page
            base_url = "https://x.com"
            if item_type == "Replies":
                driver.get(f"{base_url}/{username}/with_replies")
            elif item_type == "Posts":
                driver.get(f"{base_url}/{username}")
            elif item_type == "Likes":
                driver.get(f"{base_url}/{username}/likes")
            elif item_type == "Quotes":
                # Ensure date strings are in YYYY-MM-DD for the URL
                s_date = start_date.strftime('%Y-%m-%d')
                e_date = end_date.strftime('%Y-%m-%d')
                search_query = f"(from%3A{username})%20filter%3Aquote%20until%3A{e_date}%20since%3A{s_date}"
                driver.get(f"{base_url}/search?q={search_query}&src=typed_query&f=live")
            
            time.sleep(5)  # Wait for page load, increased for potentially slower pages like search

            # Log in if required (manual step for now)
            # X.com might require login to see content or perform actions.
            # This script assumes the user is already logged in via their browser session
            # or that the content is publicly accessible and deletable without login (less likely for delete actions).
            # For a robust solution, Selenium would need to handle login.
            # For now, we'll prompt the user if they seem stuck on a login page.
            if "login" in driver.current_url.lower() or "signin" in driver.current_url.lower():
                 # Check if we are on a login page
                if messagebox.askyesno("Login Required", "It seems you are on a login page. Please log in to X.com in the browser window that Selenium opened, then click 'Yes' to continue. Click 'No' to abort."):
                    # User will manually log in, then we can try to re-fetch the target page if needed
                    # Re-attempt navigation after potential login
                    if item_type == "Replies":
                        driver.get(f"{base_url}/{username}/with_replies")
                    elif item_type == "Posts":
                        driver.get(f"{base_url}/{username}")
                    elif item_type == "Likes":
                        driver.get(f"{base_url}/{username}/likes")
                    elif item_type == "Quotes":
                        s_date = start_date.strftime('%Y-%m-%d')
                        e_date = end_date.strftime('%Y-%m-%d')
                        search_query = f"(from%3A{username})%20filter%3Aquote%20until%3A{e_date}%20since%3A{s_date}"
                        driver.get(f"{base_url}/search?q={search_query}&src=typed_query&f=live")
                    time.sleep(5) # Wait again
                else:
                    raise Exception("Login required by user, aborted.")


            last_height = driver.execute_script("return document.body.scrollHeight")
            items_deleted_count = 0
            items_failed_count = 0
            
            while True:
                # Find tweet/item elements. This selector is common for tweets.
                # For likes, the article might still be the container.
                articles = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                if not articles:
                    # Potentially no more items or page structure changed
                    # Check for "Try again" or "Retry" button if content fails to load
                    retry_buttons = driver.find_elements(By.XPATH, "//span[contains(text(), 'Try again')]|//span[contains(text(), 'Retry')]")
                    if retry_buttons:
                        try:
                            retry_buttons[0].click()
                            time.sleep(3)
                            articles = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']") # try finding articles again
                        except:
                            pass # if click fails or no articles after retry, will proceed to scroll or break

                page_processed_items_this_scroll = 0

                for article in articles:
                    try:
                        # Get post date
                        date_elem = article.find_element(By.CSS_SELECTOR, "time")
                        post_date_str = date_elem.get_attribute("datetime")
                        post_date = parse(post_date_str) # Use the original parsed date for comparison

                        if not (start_date <= post_date.replace(tzinfo=None) <= end_date.replace(tzinfo=None)):
                            continue

                        page_processed_items_this_scroll +=1

                        if item_type == "Likes":
                            # Unlike action
                            unlike_button = article.find_element(By.CSS_SELECTOR, "button[data-testid='unlike']")
                            driver.execute_script("arguments[0].click();", unlike_button) # JS click
                            time.sleep(1) # Short pause for action to register
                            items_deleted_count += 1
                            self.status.config(text=f"Unliked {items_deleted_count} items")
                        else: # Handles Posts, Replies, Quotes (as they are types of posts)
                            # Verify user ID - important for replies and quotes from search
                            # For main profile posts, this might not be strictly necessary but good for consistency
                            user_link_css = f"a[href='/{username.lower()}']" # X.com URLs are case-insensitive for usernames typically
                            user_elements = article.find_elements(By.CSS_SELECTOR, user_link_css)

                            # Check if the tweet is by the target user.
                            # This is crucial for search results (quotes) and reply pages.
                            is_own_tweet = False
                            for el in user_elements:
                                # Check if the element is part of the tweet's author section, not a mention.
                                # This can be tricky. A common pattern is that the author link is within a div with data-testid="User-Name"
                                try:
                                    # Traverse up to find a specific parent that indicates it's the author link
                                    parent_div = el.find_element(By.XPATH, "./ancestor::div[@data-testid='User-Name']")
                                    if parent_div:
                                        is_own_tweet = True
                                        break
                                except: # NoSuchElementException
                                     # If not found via specific parent, check if it's the first link with username in the article
                                     # This is a fallback and might not always be accurate.
                                    if el.get_attribute("tabindex") == "0": # Author link often has tabindex="0"
                                        is_own_tweet = True
                                        break

                            if not is_own_tweet and item_type != "Likes": # For likes, we don't care who posted it.
                                # If we are on the user's own profile (Posts/Replies), this check might be redundant
                                # but for Quotes (search results), it's important.
                                # Let's refine this: only skip if it's quotes and not by the user.
                                if item_type == "Quotes":
                                     # Check if the displayed username in the tweet matches.
                                    screen_name_elements = article.find_elements(By.CSS_SELECTOR, "div[data-testid='User-Name'] span[id^='id__']")
                                    tweet_author_found = False
                                    for sn_elem in screen_name_elements:
                                        if sn_elem.text.strip().lower() == f"@{username.lower()}":
                                            tweet_author_found = True
                                            break
                                    if not tweet_author_found:
                                        continue # Skip this quote as it's not by the target user


                            # Click three dots (caret button)
                            menu_button = article.find_element(By.CSS_SELECTOR, "button[data-testid='caret']")
                            driver.execute_script("arguments[0].click();", menu_button)
                            time.sleep(1)

                            # Click delete option from dropdown menu
                            # The delete option is usually the first item in the menu for own posts
                            # Attempt to find by text first, then fall back to position
                            try:
                                # Try to find the delete menu item by its text content or a more specific testid
                                # This example assumes English "Delete" text. This should be internationalized or made more robust.
                                delete_option = driver.find_element(By.XPATH, "//div[@role='menuitem' and (.//span[text()='Delete'] or .//span[contains(text(),'Delete Post')])]")
                            except: # Fallback to first item if specific text not found
                                delete_option = driver.find_element(By.XPATH, "//div[@role='menuitem'][1]")

                            driver.execute_script("arguments[0].click();", delete_option)
                            time.sleep(1)

                            # Confirm deletion
                            confirm_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='confirmationSheetConfirm']")
                            driver.execute_script("arguments[0].click();", confirm_button)
                            time.sleep(2) # Wait for deletion to process

                            items_deleted_count += 1
                            self.status.config(text=f"Deleted {items_deleted_count} {item_type.lower()}")
                        
                        self.root.update()
                    except Exception as post_ex:
                         items_failed_count += 1
                        print(f"Could not process an item: {post_ex}") # Log to console for debugging
                         self.status.config(text=f"Processed: {items_deleted_count}, Failed: {items_failed_count}. Error with one item.")
                         self.root.update()
                        continue # Move to next post/article
                
                # Scroll down
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3) # Increased wait after scroll for content to load
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                # Break condition: if no new items were processed on this page after scroll, and height hasn't changed.
                # This helps if the page dynamically loads but finds no more relevant items.
                if new_height == last_height and page_processed_items_this_scroll == 0:
                    # Check if we are at the end of the page content for likes (often shows "You don't have any likes yet" or similar)
                    if item_type == "Likes":
                        end_of_likes_msgs = ["You don't have any likes yet", "No likes yet"]
                        page_text = driver.find_element(By.TAG_NAME, 'body').text
                        if any(msg in page_text for msg in end_of_likes_msgs):
                            break
                    # For other types, if height is same and no items processed, likely end.
                    elif item_type != "Likes": # For posts, replies, quotes
                        # More robust end-of-scroll check: if no new articles are loaded after some scrolls
                        # This is tricky. The current 'new_height == last_height' is a common way.
                        # If 'articles' list was empty before scroll and still empty after, and height is same.
                        pass # The outer loop condition (new_height == last_height) will handle this.


                if new_height == last_height:
                    # If scroll height hasn't changed, try one more check for content.
                    # Sometimes content loads slightly after scroll height stabilizes.
                    time.sleep(2)
                    articles_after_wait = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                    if not articles_after_wait and page_processed_items_this_scroll == 0 :
                         # If still no articles and no items processed, then break
                        no_more_content_texts = ["You’re all caught up", "No more Tweets to show", "No results for"]
                        body_text = driver.find_element(By.TAG_NAME, 'body').text
                        if any(text in body_text for text in no_more_content_texts):
                            break
                        # For quotes search, if "No results for..." appears.
                        if item_type == "Quotes" and "No results for" in body_text:
                            break

                    if new_height == driver.execute_script("return document.body.scrollHeight") and page_processed_items_this_scroll == 0 and not articles_after_wait:
                        break # Break if height is truly stable and no new items found

                last_height = new_height
            
            if driver:
                driver.quit()
            self.progress.stop()
            self.delete_button.config(state='normal')
            final_status_message = f"Finished! Processed: {items_deleted_count} {item_type.lower()}."
            if items_failed_count > 0:
                final_status_message += f" Failed to process: {items_failed_count}."
            self.status.config(text=final_status_message)
            messagebox.showinfo("Success", final_status_message)
            
        except Exception as e:
            if driver: # Ensure driver is quit even if an error occurs mid-process
                driver.quit()
            self.progress.stop()
            self.delete_button.config(state='normal')
            error_message = f"An error occurred: {str(e)}"
            if items_failed_count > 0:
                error_message += f" Additionally, {items_failed_count} item(s) could not be processed before this error."
            self.status.config(text="Error occurred!") # Keep GUI status brief
            messagebox.showerror("Error", error_message)

if __name__ == "__main__":
    root = tk.Tk()
    app = XReplyDeleter(root)
    root.mainloop()
