import os
from atproto import Client as AtprotoClient
import tweepy
from mastodon import Mastodon
import misskey
from dotenv import load_dotenv
import io
from PIL import Image
from sns_posters.bluesky import BlueskyPoster
from sns_posters.x import XPoster
from sns_posters.threads import ThreadsPoster
from sns_posters.misskey import MisskeyPoster
from sns_posters.mastodon import MastodonPoster
from constants import CHARACTER_LIMITS, IMAGE_LIMITS

# .envファイルから環境変数を読み込む
load_dotenv()


def get_character_limits():
    """文字数制限を取得する関数"""
    return CHARACTER_LIMITS


class SnsClient:
    def __init__(self):
        self.clients = {}
        self.setup_clients()
        self.posters = {}
        self.setup_posters()

    def setup_clients(self):
        # ...existing code...
        try:
            bluesky_username = os.getenv("BLUESKY_USERNAME")
            bluesky_password = os.getenv("BLUESKY_PASSWORD")
            if bluesky_username and bluesky_password:
                bluesky_client = AtprotoClient()
                bluesky_client.login(bluesky_username, bluesky_password)
                self.clients["bluesky"] = bluesky_client
        except Exception as e:
            print(f"Bluesky setup error: {e}")
        # ...existing code...
        try:
            x_api_key = os.getenv("X_API_KEY")
            x_api_secret = os.getenv("X_API_SECRET")
            x_access_token = os.getenv("X_ACCESS_TOKEN")
            x_access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
            if all([x_api_key, x_api_secret, x_access_token, x_access_token_secret]):
                auth = tweepy.Client(
                    consumer_key=x_api_key,
                    consumer_secret=x_api_secret,
                    access_token=x_access_token,
                    access_token_secret=x_access_token_secret,
                )
                x_client = auth
                self.clients["x"] = x_client
        except Exception as e:
            print(f"X/Twitter setup error: {e}")
        # ...existing code...
        try:
            misskey_token = os.getenv("MISSKEY_API_TOKEN")
            misskey_instance = os.getenv("MISSKEY_INSTANCE_URL")
            if misskey_token and misskey_instance:
                misskey_client = misskey.Misskey(misskey_instance, i=misskey_token)
                self.clients["misskey"] = misskey_client
        except Exception as e:
            print(f"Misskey setup error: {e}")
        # ...existing code...
        try:
            threads_instance = os.getenv("THREADS_ACCESS_TOKEN")
            if threads_instance:
                self.clients["threads"] = threads_instance
        except Exception as e:
            print(f"Misskey setup error: {e}")
        # ...existing code...
        try:
            mastodon_token = os.getenv("MASTODON_ACCESS_TOKEN")
            mastodon_instance = os.getenv("MASTODON_INSTANCE_URL")
            if mastodon_token and mastodon_instance:
                mastodon_client = Mastodon(
                    access_token=mastodon_token, api_base_url=mastodon_instance
                )
                self.clients["mastodon"] = mastodon_client
        except Exception as e:
            print(f"Mastodon setup error: {e}")

    def setup_posters(self):
        if "bluesky" in self.clients:
            self.posters["bluesky"] = BlueskyPoster(self.clients["bluesky"])
        if "x" in self.clients:
            self.posters["x"] = XPoster(self.clients["x"])
        if "threads" in self.clients:
            self.posters["threads"] = ThreadsPoster(self.clients["threads"])
        if "misskey" in self.clients:
            self.posters["misskey"] = MisskeyPoster(self.clients["misskey"])
        if "mastodon" in self.clients:
            self.posters["mastodon"] = MastodonPoster(self.clients["mastodon"])

    def compress_image_for_platform(
        self, image_path, max_size=None, min_size=None, max_attempts=None
    ):
        if max_size is None:
            max_size = IMAGE_LIMITS["bluesky"]["max_size"]
        if min_size is None:
            min_size = IMAGE_LIMITS["bluesky"]["min_size"]
        if max_attempts is None:
            max_attempts = IMAGE_LIMITS["bluesky"]["max_attempts"]
        try:
            with open(image_path, "rb") as f:
                img_bytes = f.read()
            img = Image.open(io.BytesIO(img_bytes))
            format = img.format if img.format in ["JPEG", "PNG"] else "JPEG"
            quality = 85
            buf = io.BytesIO()
            for attempt in range(max_attempts):
                buf = io.BytesIO()
                img.save(buf, format=format, quality=quality, optimize=True)
                if buf.tell() <= max_size:
                    buf.seek(0)
                    return buf, format
                if (attempt + 1) % 5 == 0:
                    w, h = img.size
                    if w < min_size or h < min_size:
                        break
                    img = img.resize((max(1, int(w * 0.8)), max(1, int(h * 0.8))))
                    quality = 85
                else:
                    quality = max(30, quality - 10)
            return (
                None,
                f"画像が制限({max_size // 1024}KB)以下になりません: {os.path.basename(image_path)}",
            )
        except Exception as e:
            return None, str(e)

    def handle_exception(self, e, platform_name=None):
        msg = str(e)
        if platform_name:
            msg = f"{platform_name}エラー: {msg}"
        return {"success": False, "error": msg}

    def _get_image_paths_limited(self, image_paths, platform):
        if not image_paths:
            return []
        max_images = IMAGE_LIMITS.get(platform, {}).get("max_images", 4)
        return image_paths[:max_images]

    def _upload_images_bluesky(self, bluesky_client, image_paths):
        images = []
        for image_path in self._get_image_paths_limited(image_paths, "bluesky"):
            buf, err = self.compress_image_for_platform(
                image_path,
                max_size=IMAGE_LIMITS["bluesky"]["max_size"],
                min_size=IMAGE_LIMITS["bluesky"]["min_size"],
                max_attempts=IMAGE_LIMITS["bluesky"]["max_attempts"],
            )
            if buf is None:
                return None, err
            blob = bluesky_client.com.atproto.repo.upload_blob(buf)
            images.append({"alt": "image", "image": blob["blob"]})
        return images, None

    def post_to_platforms(self, posts):
        results = {}
        for platform, post in posts.items():
            content = post.get("content")
            image_paths = post.get("image_paths")
            if platform in self.posters and content:
                if platform == "bluesky":
                    results[platform] = self.posters[platform].post(
                        content,
                        self._get_image_paths_limited(image_paths, platform),
                        self.compress_image_for_platform,
                    )
                else:
                    results[platform] = self.posters[platform].post(
                        content, self._get_image_paths_limited(image_paths, platform)
                    )
        return results


sns_client = SnsClient()
