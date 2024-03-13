from playwright.sync_api import sync_playwright, ElementHandle
from utils import Utils
from urllib import request
from string import printable
from configs import *
from requests import get
from typing import List, Literal
from interfaces import ISource
from os import getenv, mkdir, path
from shutil import rmtree
import json


class FacebookFetch:
    def __init__(self) -> None:
        self.ALREADY_UPLOADED: list = Utils.get_uploaded_files("both")
        with sync_playwright() as p:
            self.browser = p.chromium.launch(headless=not DEBUG, channel="chrome", args=["--window-position=0,0"])
            self.context = self.browser.new_context(**p.devices["iPhone 13"])
            self.page = self.context.new_page()

            # self.generate_cookie()
            self.load_cookie()
            for source in self.get_sources_list("facebook_group"):
                print("=" * 10 + f" {source['name']} " + "=" * 10)
                self.fetch_group(source)

    def get_sources_list(self, source_type: Literal["facebook_group"]) -> List[ISource]:
        with open(f"{PROJECT_ROOT}/sources.json", "r") as sources_file:
            sources = json.load(sources_file)
        return [source for source in sources if source["source_type"] == source_type]

    def fetch_group(self, source: ISource) -> None:
        self.scroll(source)
        input("now")
        for post in self.get_articles():
            input()
            data_store = post.get_attribute("data-store")
            if data_store is None:
                continue

            id = json.loads(data_store)["feedback_target"]
            print("[fetch_group@id]", id)
            if not str(id).isdigit():
                continue

            if id in self.ALREADY_UPLOADED:
                continue

            post_type = self.get_post_type(post)
            if post_type is None:
                print(f"\t[-] Skipped: not photo, video")
                continue

            reaction_count = self.get_post_reaction_count(post)
            if int(source["min_reaction"][post_type]) > reaction_count:
                print("\t[-] Skipped: reaction low")
                continue

            print(f"[*] ID: {id}")
            print(f"\t[+] Reaction count: {reaction_count}")
            print(f"\t[+] Post type: {post_type}")

            mkdir(f"{STATIC_ROOT}/{id}")
            if post_type == "photo":
                self.fetch_group_post_image(id, post, source, reaction_count)

            elif post_type == "video_inline":
                self.fetch_group_post_video(id, post, source, reaction_count)

    def fetch_group_post_video(self, id: str, post: ElementHandle, source: ISource, reaction_count: int) -> None:
        try:
            print("\t[*] Downloading video")

            el_inline = post.query_selector("xpath=.//div[@data-sigil='inlineVideo']")
            if el_inline is None:
                return
            video_id = json.loads(el_inline.get_attribute("data-store") or "")["videoID"]
            self.context.new_page()
            self.context.pages[1].goto("https://snapsave.app/")
            el_input = self.context.pages[1].wait_for_selector("//input[@placeholder='Paste video URL Facebook']", state="visible")
            if el_input:
                el_input.fill(f"https://facebook.com/{source['username']}/videos/{video_id}")
            el_button = self.context.pages[1].wait_for_selector("//button[@id='send']", state="visible")
            if el_button:
                el_button.click()
            video_endpoint_link = self.context.pages[1].wait_for_selector("//tbody//a[contains(text(), 'Download')]", timeout=20000)
            if video_endpoint_link:
                href = video_endpoint_link.get_attribute("href")
                if href:
                    request.urlretrieve(href, f"{STATIC_ROOT}/{id}/video.mp4")
            self.context.pages[1].close()

            el_description = post.query_selector('xpath=.//div[@data-gt=\'{"tn":"*s"}\']')
            if el_description:
                description = self.get_clean_text(el_description.inner_text())
            else:
                description = ""

            # saving content
            with open(f"{STATIC_ROOT}/{id}/meta.json", "w") as f:
                f.write(
                    json.dumps(
                        {
                            "description": description,
                            "reaction_count": reaction_count,
                            "min_reaction_to_pass": source["min_reaction"]["video_inline"],
                            "source": source["name"],
                        },
                        indent=2,
                    )
                )

        except Exception as e:
            # video too long
            print(f"\t[-] Skipping: video too long")
            if len(self.context.pages) > 1:
                for _ in range(len(self.context.pages) - 1):
                    self.context.pages[_ + 1].close()
            folder_path = f"{STATIC_ROOT}/{id}"
            if path.exists(folder_path):
                rmtree(folder_path)

    def fetch_group_post_image(self, id: str, post: ElementHandle, source: ISource, reaction_count: int) -> None:
        post_el = post.query_selector('xpath=.//div[@data-gt=\'{"tn":"E"}\']/a')
        if post_el is None:
            return
        post_el.click()
        fu_size = self.page.wait_for_selector("xpath=//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'full size')]")
        if fu_size is None:
            return
        fu_size.click()
        self.page.wait_for_timeout(500)

        with open(f"{STATIC_ROOT}/{id}/image.jpg", "wb") as f:
            f.write(get(self.context.pages[-1].url).content)
        self.context.pages[-1].close()
        self.page.go_back()

        try:
            description = post.query_selector('xpath=.//div[@data-gt=\'{"tn":"*s"}\']')
            if description is None:
                return
            description = self.get_clean_text(description.inner_text())
        except Exception:
            description = ""
            print("[-] error@fetch_group_post_image")

        with open(f"{STATIC_ROOT}/{id}/meta.json", "w") as f:
            f.write(
                json.dumps(
                    {
                        "description": description,
                        "reaction_count": reaction_count,
                        "min_reaction_to_pass": source["min_reaction"]["photo"],
                        "source": source["name"],
                    },
                    indent=2,
                )
            )

    def get_clean_text(self, text: str) -> str:
        return "".join(filter(lambda x: x in printable, text.replace("\n", " ")))

    def get_post_reaction_count(self, post: ElementHandle) -> int:
        post_el = post.query_selector("xpath=.//footer//div[@data-sigil='reactions-bling-bar']")
        if post_el is None:
            return 0
        react_str = post_el.inner_text().split("\n")[0] or "0"

        return self.get_number_reaction_count(react_str)

    def get_number_reaction_count(self, count: str) -> int:
        ret = 0
        try:
            if "others" in count:
                count = count.split()[-2]

            if "K" in count:
                ret = float(count.replace("K", "")) * 1000
            else:
                ret = int(count)
            return int(ret)
        except Exception as e:
            return int(ret)

    def get_post_type(self, post: ElementHandle) -> Literal["photo", "video_inline", None]:
        data_ft = post.get_attribute("data-ft")
        if data_ft is None:
            return None
        data_ft = json.loads(data_ft)
        if "story_attachment_style" in data_ft and data_ft["story_attachment_style"] in ["photo", "video_inline"]:
            return data_ft["story_attachment_style"]
        return None

    def get_articles(self) -> List[ElementHandle]:
        return self.page.query_selector_all("//div[@data-mcomponent='MContainer' and @data-type='vscroller']//div[@data-mcomponent='MContainer' and @data-type='container' and @class='m displayed']")

    def scroll(self, source: ISource) -> None:
        self.page.goto(f"https://m.facebook.com/groups/{source['username']}?sorting_setting=RECENT_ACTIVITY")
        print("[DEBUG] scrolling ...")
        for _ in range(FETCH_TOTAL_SCROLL):
            self.page.evaluate("window.scrollTo(0,document.body.scrollHeight)")
            self.page.wait_for_timeout(2000)

    def generate_cookie(self) -> None:
        self.page.goto(SOCIAL_MAPS["facebook"]["login"])
        self.page.fill("//input[@id='m_login_email']", getenv("FACEBOOK_USERNAME", ""))
        self.page.fill("//input[@id='m_login_password']", getenv("FACEBOOK_PASSWORD", ""))
        self.page.click("//button[@name='login']")
        self.page.wait_for_load_state("networkidle")

        cookies = self.page.context.cookies()
        with open(f"{PROJECT_ROOT}/sessions/{SOCIAL_MAPS['facebook']['filename']}", "w") as f:
            json.dump(cookies, f)
        input("[*] press any key to continue")
        exit()

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
