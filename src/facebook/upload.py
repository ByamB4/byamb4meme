from configs import *
from playwright.sync_api import sync_playwright
from utils import Utils
from configs import *
from os import path
import json


class FacebookUpload:
    def __init__(self) -> None:
        self.ALREADY_UPLOADED: list = Utils.get_uploaded_files("facebook")
        with sync_playwright() as p:
            # channel 'chrome' works for facebook reels
            self.browser = p.chromium.launch(headless=not DEBUG, channel="chrome", args=["--enable-popup-blocking", "--start-maximized"])
            self.context = self.browser.new_context(no_viewport=True)
            self.page = self.context.new_page()
            self.load_cookie()
            self.page.goto("https://www.facebook.com/byamba4meme")
            self.page.wait_for_selector("//div[@aria-label='Switch Now']").click()

            self.page.wait_for_load_state("networkidle")
            self.post_contents()

    def post_contents(self) -> None:
        print("=" * 10 + " posting to facebook " + "=" * 10)
        for post_id in Utils.get_list_static_files(STATIC_ROOT):
            try:
                if post_id in self.ALREADY_UPLOADED:
                    print(f"[-] Already uploaded: {post_id}")
                    continue

                print(f"[+] Trying to upload: {post_id}")
                self.page.wait_for_load_state("networkidle")

                post_type = Utils.get_post_type_for_upload(post_id)
                if post_type == "photo":
                    self.page.goto("https://www.facebook.com/byamba4meme")
                    self.page.wait_for_selector("//span[contains(text(), 'Photo/video')]").click()
                    self.page.locator("xpath=//div[@role='dialog']//input[@type='file']").set_input_files(f"{STATIC_ROOT}/{post_id}/image.jpg")
                    self.page.locator('xpath=//div[@data-lexical-editor="true"][@aria-label="What\'s on your mind?"]').fill(Utils.get_upload_text(post_id))
                    self.page.wait_for_load_state("networkidle")
                    self.page.wait_for_selector("//div[@role='dialog']//div[@aria-label='Post']").click()
                    self.page.wait_for_load_state("networkidle")

                if post_type == "video":
                    self.page.goto("https://www.facebook.com/reels/create")
                    self.page.locator("xpath=//div[@aria-label='Reels']//input[@type='file']").set_input_files(f"{STATIC_ROOT}/{post_id}/video.mp4")
                    self.page.wait_for_load_state("networkidle")
                    self.page.wait_for_selector("//div[@aria-label='Next'][@role='button'][@tabindex='0']").click()
                    self.page.wait_for_selector("//div[@data-lexical-editor='true'][@aria-label='Describe your reel...']").fill(Utils.get_upload_text(post_id))
                    self.page.wait_for_selector("//div[@aria-label='Publish'][@tabindex='0']").click()
                    self.page.wait_for_load_state("networkidle")
                Utils.save_uploaded_content("facebook", post_id)
            except Exception as e:
                print(f"\t[-] Error@facebook_upload: {e}")
                # if DEBUG: input()

    def load_cookie(self) -> None:
        file_path = f"{PROJECT_ROOT}/sessions/{SOCIAL_MAPS['facebook']['filename']}"
        if not path.exists(file_path):
            print("[-] Not found facebook.json")
            print("[-] Generate using `generate_cookie()`")
            exit()

        self.page.goto(SOCIAL_MAPS["facebook"]["login"])
        with open(file_path, "r") as f:
            cookies = json.loads(f.read())
            self.context.add_cookies(cookies)
