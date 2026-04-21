import os
import time
import queue
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By


logging.basicConfig(
    filename='parsing.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class Parser:
    def __init__(self, 
            save_path='downdetector_comments_new.txt', 
            num_scrolls=6
        ):
        self.event_queue = queue.Queue()
        self.driver = webdriver.Chrome()
        self.num_scrolls = num_scrolls
        self.save_path = save_path
        if os.path.isfile(self.save_path):
            with open(save_path) as f:
                self.seen = f.readlines()
        else:
            self.seen = []
    
    def get_content(self,):
        logging.info('loading content')
        self.driver.get("https://detector404.ru/telegram")
        source = self.driver.page_source
        counter = 0
        while counter <= self.num_scrolls:
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, "button[data-ellipsis='telegram']")
                self.driver.execute_script("""arguments[0].scrollIntoView({block: 'center'});""", button)
                time.sleep(1)

                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(2)
                counter += 1
            except Exception as e:
                logging.error(e)
                print("No more button or finished loading")
                break
            comments = self.driver.find_elements(By.XPATH, "//span[@data-author]")
        return comments
    
    def is_new_comment(self, comment):
        author = comment.text
        tick_elem = comment.find_element(By.XPATH, "following-sibling::span[@data-tick][1]")
        tick_value = tick_elem.get_attribute("data-tick")
        text = comment.find_element(By.XPATH, "following::div[1]").text
        comm_to_save = f'{tick_value}|{text}\n'
        if comm_to_save not in self.seen:
            self.seen.append(comm_to_save)
            with open(self.save_path, 'a+') as f:
                # f.write(comm_to_save)
                logging.info(comm_to_save)
                return text
        return False
    
    def parse(self,):
        while True:
            comments = self.get_content()
            logging.info('searching for new comments')
            for comment in comments:
                text = self.is_new_comment(comment)
                if text:
                    self.event_queue.put(f"{text}")
            time.sleep(120)

# parser = Parser()
# parser.parse()