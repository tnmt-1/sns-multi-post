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
        """
        各SNSクライアントのセットアップを行う。
        環境変数から認証情報を取得し、各SNSのAPIクライアントを初期化する。
        """
        try:
            bluesky_username = os.getenv("BLUESKY_USERNAME")
            bluesky_password = os.getenv("BLUESKY_PASSWORD")
            if bluesky_username and bluesky_password:
                bluesky_client = AtprotoClient()
                bluesky_client.login(bluesky_username, bluesky_password)
                # Blueskyの認証情報も保持
                self.clients["bluesky"] = {
                    "client": bluesky_client,
                    "username": bluesky_username,
                    "password": bluesky_password,
                }
        except Exception as e:
            print(f"Bluesky setup error: {e}")

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

        try:
            misskey_token = os.getenv("MISSKEY_API_TOKEN")
            misskey_instance = os.getenv("MISSKEY_INSTANCE_URL")
            if misskey_token and misskey_instance:
                misskey_client = misskey.Misskey(misskey_instance, i=misskey_token)
                self.clients["misskey"] = misskey_client
        except Exception as e:
            print(f"Misskey setup error: {e}")

        try:
            threads_instance = os.getenv("THREADS_ACCESS_TOKEN")
            if threads_instance:
                self.clients["threads"] = threads_instance
        except Exception as e:
            print(f"Misskey setup error: {e}")

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
        """
        各SNS投稿クラス（Poster）のセットアップを行う。
        利用可能なSNSクライアントごとにPosterインスタンスを生成し、self.postersに格納する。
        """
        if "bluesky" in self.clients:
            # BlueskyPosterに認証情報も渡す
            bluesky_info = self.clients["bluesky"]
            self.posters["bluesky"] = BlueskyPoster(
                bluesky_info["client"],
                username=bluesky_info["username"],
                password=bluesky_info["password"],
            )
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
        """
        汎用画像圧縮・リサイズ関数。
        指定サイズ・回数制限内で画像を圧縮・リサイズし、バイト列を返す。
        Args:
            image_path: 画像ファイルパス
            max_size: バイト単位の最大サイズ
            min_size: 最小幅・高さ
            max_attempts: 最大試行回数
        Returns:
            (buf, format) or (None, error_message)
        """
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
        """
        共通エラーハンドリング関数。
        Args:
            e: 例外
            platform_name: SNS名（任意）
        Returns:
            dict: エラー情報
        """
        msg = str(e)
        if platform_name:
            msg = f"{platform_name}エラー: {msg}"
        return {"success": False, "error": msg}

    def _get_image_paths_limited(self, image_paths, platform):
        """
        指定プラットフォームの最大枚数まで画像パスリストを制限する。
        Args:
            image_paths: 画像パスのリスト
            platform: SNS名
        Returns:
            制限後の画像パスリスト
        """
        if not image_paths:
            return []
        max_images = IMAGE_LIMITS.get(platform, {}).get("max_images", 4)
        return image_paths[:max_images]

    def _upload_images_bluesky(self, bluesky_client, image_paths):
        """
        Bluesky用の画像アップロード処理。
        圧縮・リサイズ後の画像をBlueskyにアップロードし、blob情報リストを返す。
        Args:
            bluesky_client: Blueskyクライアント
            image_paths: 画像パスリスト
        Returns:
            (images, None) or (None, error_message)
        """
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
        """
        複数のプラットフォームに投稿する関数。
        Args:
            posts: プラットフォーム名をキー、{"content":..., "image_paths":...}を値とする辞書
        Returns:
            各プラットフォームの投稿結果を含む辞書
        """
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
