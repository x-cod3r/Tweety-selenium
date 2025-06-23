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
        
        self.delete_button = tk.Button(root, text="Delete Replies", command=self.start_deletion)
        self.delete_button.pack(pady=10)
        
        self.status = tk.Label(root, text="")
        self.status.pack(pady=5)
        
        self.progress = ttk.Progressbar(root, length=200, mode='indeterminate')
        self.progress.pack(pady=5)

    def start_deletion(self):
        username = self.username_entry.get()
        start_date = self.start_date.get()
        end_date = self.end_date.get()
        
        if not username or not start_date or not end_date:
            messagebox.showerror("Error", "Please fill all fields!")
            return
        
        try:
            start = parse(start_date)
            end = parse(end_date)
            if start > end:
                messagebox.showerror("Error", "Start date must be before end date!")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD")
            return
        
        self.delete_button.config(state='disabled')
        self.progress.start()
        self.status.config(text="Starting deletion...")
        self.root.update()
        
        self.delete_replies(username, start, end)
        
    def delete_replies(self, username, start_date, end_date):
        try:
            # Setup Selenium
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")  # Run in headless mode
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            # Navigate to profile replies
            driver.get(f"https://x.com/{username}/with_replies")
            time.sleep(3)  # Wait for page load
            
            # Scroll and collect replies
            last_height = driver.execute_script("return document.body.scrollHeight")
            replies_deleted = 0
            
            while True:
                # Find reply elements
                posts = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                
                for post in posts:
                    try:
                        # Get post date
                        date_elem = post.find_element(By.CSS_SELECTOR, "time")
                        post_date = parse(date_elem.get_attribute("datetime"))
                        
                        # Check if within date range
                        if start_date <= post_date <= end_date:
                            # Verify user ID
                            user_elem = post.find_element(By.CSS_SELECTOR, "a[href='/{username}']")
                            if user_elem:
                                # Click three dots
                                menu_button = post.find_element(By.CSS_SELECTOR, "button[data-testid='caret']")
                                menu_button.click()
                                time.sleep(1)
                                
                                # Click delete
                                delete_option = driver.find_element(By.CSS_SELECTOR, "div[role='menuitem'][data-testid='delete']")
                                delete_option.click()
                                time.sleep(1)
                                
                                # Confirm deletion
                                confirm_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='confirmationSheetConfirm']")
                                confirm_button.click()
                                time.sleep(2)
                                
                                replies_deleted += 1
                                self.status.config(text=f"Deleted {replies_deleted} replies")
                                self.root.update()
                    except Exception:
                        continue
                
                # Scroll down
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                last_height = new_height
            
            driver.quit()
            self.progress.stop()
            self.delete_button.config(state='normal')
            self.status.config(text=f"Finished! Deleted {replies_deleted} replies")
            messagebox.showinfo("Success", f"Deleted {replies_deleted} replies!")
            
        except Exception as e:
            driver.quit()
            self.progress.stop()
            self.delete_button.config(state='normal')
            self.status.config(text="Error occurred!")
            messagebox.showerror("Error", str(e)))

if __name__ == "__main__":
    root = tk.Tk()
    app = XReplyDeleter(root)
    root.mainloop()
