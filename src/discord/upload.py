from utils import Utils
from configs import *
from os import path
import discord, asyncio


class DiscordUpload:
    def __init__(self) -> None:
        self.ALREADY_UPLOADED: list = Utils.get_uploaded_files("discord")
        self.client = discord.Client(intents=discord.Intents.default())
        asyncio.run(self.post_contents())

    async def post_contents(self) -> None:
        print("=" * 10 + " posting discord " + "=" * 10)
        for post_id in Utils.get_list_static_files(STATIC_ROOT):
            try:
                if post_id in self.ALREADY_UPLOADED:
                    print(f"[-] Already uploaded: {post_id}")
                    continue
                print(f"[+] Trying to upload: {post_id}")
                post_type = Utils.get_post_type_for_upload(post_id)
                upload_item = "video.mp4" if post_type == "video" else "image.jpg"
                file_path = f"{STATIC_ROOT}/{post_id}/{upload_item}"
                if not path.exists(file_path):
                    continue
                await self.send_message_with_attachment(
                    Utils.get_upload_text(post_id), file_path
                )
                Utils.save_uploaded_content("discord", post_id)
            except Exception as e:
                print("\t[-] Error@discord_upload: {e}")

    async def send_message_with_attachment(
        self, message, file_path, add_separator=True
    ) -> None:
        client = discord.Client(intents=discord.Intents.default())

        @client.event
        async def on_ready() -> None:
            with open(file_path, "rb") as f:
                file = discord.File(f)
                await client.get_channel(DISCORD_CHANNEL).send(
                    content=message, file=file
                )
                if add_separator:
                    await client.get_channel(DISCORD_CHANNEL).send(content="-" * 50)
            await client.close()

        await client.login(DISCORD_TOKEN)
        await client.connect()
