import json
import subprocess
from configs import (
    PROJECT_ROOT,
    STATIC_ROOT,
    FINAL_ROOT,
    FETCH_VIDEO_MAX_SEC,
    FETCH_VIDEO_MIN_SEC,
)
from moviepy.editor import concatenate_videoclips, VideoFileClip, VideoClip
from json import load as json_load
from time import strftime
from os import path, mkdir, listdir
from typing import Literal, List
from shutil import rmtree


class Utils:
    @staticmethod
    def clear_static_folder() -> None:
        rmtree(STATIC_ROOT)
        rmtree(FINAL_ROOT)
        mkdir(STATIC_ROOT)
        mkdir(FINAL_ROOT)
        open(f"{STATIC_ROOT}/.gitkeep", "w").close()
        open(f"{FINAL_ROOT}/.gitkeep", "w").close()

    @staticmethod
    def get_uploaded_files(source: Literal["facebook", "instagram", "discord", "both"]) -> List:
        ret = []
        if source == "facebook":
            with open(f"{PROJECT_ROOT}/done.json", "r") as f:
                for _ in json_load(f):
                    if "facebook" in _ and _["facebook"]["uploaded"]:
                        ret.append(_["hash"])
        elif source == "instagram":
            with open(f"{PROJECT_ROOT}/done.json", "r") as f:
                for _ in json_load(f):
                    if "instagram" in _ and _["instagram"]["uploaded"]:
                        ret.append(_["hash"])
        elif source == "discord":
            with open(f"{PROJECT_ROOT}/done.json", "r") as f:
                for _ in json_load(f):
                    if "discord" in _ and _["discord"]["uploaded"]:
                        ret.append(_["hash"])
        elif source == "both":
            with open(f"{PROJECT_ROOT}/done.json", "r") as f:
                for _ in json_load(f):
                    if "facebook" in _ and _["facebook"]["uploaded"] and "instagram" in _ and _["instagram"]["uploaded"]:
                        ret.append(_["hash"])
        return ret

    @staticmethod
    def get_upload_count() -> int:
        return len(listdir(STATIC_ROOT))

    @staticmethod
    def get_static_list() -> List[str]:
        return [_ for _ in listdir(STATIC_ROOT) if _ != ".gitkeep"]

    @staticmethod
    def get_post_type_for_upload(post_id: str) -> Literal["video", "photo"]:
        if "video.mp4" in listdir(f"{STATIC_ROOT}/{post_id}"):
            return "video"
        return "photo"

    @staticmethod
    def prepare_data() -> None:
        print("=" * 10 + " PREPARING DATA " + "=" * 10)
        videos = []
        for post_id in [_ for _ in listdir(STATIC_ROOT) if _.isdigit()]:
            list_files = listdir(f"{STATIC_ROOT}/{post_id}")
            print(f"[*] Post: {post_id}")
            if "video.mp4" in list_files:
                duration = Utils.get_video_length(f"{STATIC_ROOT}/{post_id}/video.mp4")
                print(f"\t[+] Duration: {duration}")
                if duration > FETCH_VIDEO_MAX_SEC:
                    print("\t[-] Deleting: (video too long)")
                    rmtree(f"{STATIC_ROOT}/{post_id}")
                if duration < FETCH_VIDEO_MIN_SEC:
                    print("\t[-] Deleting: (video too short)")
                    rmtree(f"{STATIC_ROOT}/{post_id}")
                videos.append({"duration": duration, "post_id": post_id})

        if not path.exists(f"{FINAL_ROOT}"):
            mkdir(FINAL_ROOT)

        # combining videos
        combined_videos, current_video, current_duration = [], [], 0
        max_duration = 90
        for obj_video in videos:
            if current_duration + obj_video["duration"] <= max_duration:
                current_duration += obj_video["duration"]
                current_video.append({"post_id": obj_video["post_id"], "duration": obj_video["duration"]})
            else:
                combined_videos.append(current_video)
                current_duration = obj_video["duration"]
                current_video = [{"post_id": obj_video["post_id"], "duration": obj_video["duration"]}]
        if current_video:
            combined_videos.append(current_video)

        for index, videos in enumerate(combined_videos):
            total_duration = sum([_["duration"] for _ in videos])
            if total_duration < 30:
                continue
            video_paths = [f"{STATIC_ROOT}/{_['post_id']}/video.mp4" for _ in videos]
            final_video_path = f"{FINAL_ROOT}/{index}-{total_duration}.mp4"
            final_clip = Utils.combine_videos(video_paths)
            final_clip.write_videofile(final_video_path)

    @staticmethod
    def combine_videos(video_paths) -> VideoClip:
        video_clips = []

        for video_path in video_paths:
            video_clip = VideoFileClip(video_path)
            resized_clip = video_clip.resize(width=1920)
            centered_clip = resized_clip.set_position("center")
            video_clips.append(centered_clip)

        final_clip = concatenate_videoclips(video_clips)

        return final_clip

    @classmethod
    def get_video_length(cls, file_path: str) -> float:
        clip = VideoFileClip(file_path)
        return clip.duration

    @staticmethod
    def get_list_static_files(file_path: str) -> List[str]:
        return [_ for _ in listdir(file_path) if _.isdigit()]

    @staticmethod
    def get_upload_text(post_id: str) -> str:
        with open(f"{STATIC_ROOT}/{post_id}/meta.json", "r") as f:
            meta_data = json.load(f)

        description = meta_data["description"]
        return description
        # if you need meta data
        # reaction_count = meta_data['reaction_count']
        # min_reaction_to_pass = meta_data['min_reaction_to_pass']
        # timestamp = strftime('%Y.%m.%d %H:%M')
        # return f"{description}\n\nReaction count: {reaction_count}\nMin reaction to pass: {min_reaction_to_pass}\n\n{timestamp}\n\n\n #byamba4meme #meme #facebook #trending #viral #explore #love #mememongolia #mongolia #funny" if len(description) > 5 else f"Reaction count: {reaction_count}\nMin reaction to pass: {min_reaction_to_pass}\n\n{timestamp}\n\n\n #byamba4meme #meme #facebook #trending #viral #explore #love #mememongolia #mongolia #funny"

        # """
        #     Watch till the end #fbreels #fbreelsvideo #reels2023 #reelsvideo #reelsfb #reelsviral #fyp #viral #fyp #funny #funnyvideos #funnyreels #funnymemes #memes #memelord #memesfunny #funnypost #reels #fb
        # """

    @staticmethod
    def save_uploaded_content(source_type: Literal["instagram", "facebook", "discord"], post_id: str):
        with open(f"{PROJECT_ROOT}/done.json", "r") as f:
            done_contents: List[dict] = json.load(f)
        with open(f"{STATIC_ROOT}/{post_id}/meta.json", "r") as f:
            meta_data = json.load(f)

        item = next((i for i in done_contents if i.get("hash") == post_id), None)

        if item:
            item[source_type] = {
                "uploaded": True,
                "time": strftime("%Y.%m.%d %H:%M:%S"),
            }
        else:
            done_contents.append(
                {
                    "hash": post_id,
                    source_type: {
                        "reaction_count": meta_data["reaction_count"],
                        "source": meta_data["source"],
                        "uploaded": True,
                        "time": strftime("%Y.%m.%d %H:%M:%S"),
                    },
                }
            )

        with open(f"{PROJECT_ROOT}/done.json", "w") as f:
            json.dump(done_contents, f, indent=2)

        print("\t[+] Done")

    @staticmethod
    def kill_chrome_processes() -> None:
        subprocess.run(["pkill", "chrome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
