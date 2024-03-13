from playwright.sync_api import sync_playwright
from utils import Utils
from configs import *
from os import getenv, path
import json


class InstagramUpload:
    def __init__(self) -> None:
        self.ALREADY_UPLOADED: list = Utils.get_uploaded_files("instagram")
        with sync_playwright() as p:
            self.browser = p.chromium.launch(
                headless=not DEBUG,
                channel="chrome",
                args=["--enable-popup-blocking", "--mute-audio"],
            )
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.load_cookie()
            self.post_contents()

    def post_contents(self) -> None:
        print("=" * 10 + " posting to instagram " + "=" * 10)
        for post_id in Utils.get_list_static_files(STATIC_ROOT):
            if post_id in self.ALREADY_UPLOADED:
                print(f"[-] Already uploaded: {post_id}")
                continue
            print(f"[+] Trying to upload: {post_id}")
            self.page.goto("https://instagram.com")
            self.page.wait_for_load_state("networkidle")
            try:
                # sometimes Notifications modal shows on first time
                self.page.wait_for_selector("//button[contains(text(), 'Not Now' )]", timeout=2_000).click()
            except:
                pass

            # click Create
            self.page.query_selector_all("//a[@role='link'][@href='#']")[2].click()
            post_type = Utils.get_post_type_for_upload(post_id)
            upload_item = "image.jpg" if post_type == "photo" else "video.mp4"
            # set input file
            self.page.locator("//input[@type='file' and @multiple]").set_input_files(f"{STATIC_ROOT}/{post_id}/{upload_item}")
            self.page.wait_for_load_state("networkidle")
            try:
                # sometimes: "Video posts are now shared as reels" modal popups
                if post_type == "video":
                    self.page.wait_for_selector("//button[contains(text(), 'OK' )]", timeout=3_000).click()
            except:
                pass
            self.page.wait_for_timeout(2_000)
            # set view size to original
            self.page.query_selector_all("//div[@role='dialog']//button[@type='button']")[1].click()
            self.page.wait_for_selector("//div[contains(text(), 'Original')]").click()

            # click next button
            self.page.wait_for_selector("//div[@role='dialog']//div[contains(text(), 'Next')]").click()

            # click next button
            self.page.wait_for_selector("//div[@role='dialog']//div[contains(text(), 'Next')]").click()

            # set description
            self.page.wait_for_selector("//div[@role='dialog']//div[@data-lexical-editor='true']").fill(Utils.get_upload_text(post_id))

            # click share button
            self.page.wait_for_selector("//div[@role='dialog']//div[contains(text(), 'Share')]").click()

            # waiting content shared modal shows up
            # if video is long it takes a while
            try:
                self.page.wait_for_selector(
                    "//div[@role='dialog']//span[contains(text(), 'been shared')]",
                    timeout=20_000,
                )
            except:
                pass
            Utils.save_uploaded_content("instagram", post_id)

    def generate_cookie(self) -> None:
        self.page.goto(SOCIAL_MAPS["instagram"]["login"])
        self.page.fill("//input[@name='username']", getenv("INSTAGRAM_USERNAME", ""))
        self.page.fill("//input[@name='password']", getenv("INSTAGRAM_PASSWORD", ""))
        self.page.click("//button[@type='submit']")
        self.page.wait_for_load_state("networkidle")

        cookies = self.page.context.cookies()
        with open(f"{PROJECT_ROOT}/sessions/{SOCIAL_MAPS['instagram']['filename']}", "w") as f:
            json.dump(cookies, f)
        input("[*] press any key to continue")
        exit()

    def load_cookie(self) -> None:
        file_path = f"{PROJECT_ROOT}/sessions/{SOCIAL_MAPS['instagram']['filename']}"
        if not path.exists(file_path):
            print("[-] Not found instagram.json")
            print("[-] Generate using `generate_cookie()`")
            exit()

        self.page.goto(SOCIAL_MAPS["instagram"]["login"])
        with open(file_path, "r") as f:
            cookies = json.loads(f.read())
            self.context.add_cookies(cookies)
        self.page.wait_for_load_state("networkidle")
