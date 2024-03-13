from facebook.fetch import FacebookFetch
from instagram.upload import InstagramUpload
from facebook.upload import FacebookUpload
from discord.upload import DiscordUpload
from utils import Utils


def main() -> None:
    Utils.clear_static_folder()
    FacebookFetch()
    # Utils.prepare_data()
    # if Utils.get_upload_count() > 0:
    # DiscordUpload()
    # FacebookUpload()
    # InstagramUpload()
    # else:
    #     print('[-] Nothing to upload')


if __name__ == "__main__":
    main()
