import os
import requests
from atproto import Client as AtprotoClient
import tweepy
from mastodon import Mastodon
import misskey
from dotenv import load_dotenv
import io
from PIL import Image
from requests_oauthlib import OAuth1

# .envファイルから環境変数を読み込む
load_dotenv()

# 文字数制限の定義
CHARACTER_LIMITS = {
    "bluesky": 300,
    "x": 280,
    "threads": 500,
    "misskey": 3000,
    "mastodon": 500,
}


def get_character_limits():
    """文字数制限を取得する関数"""
    return CHARACTER_LIMITS


class SnsClient:
    def __init__(self):
        """SNSクライアントの初期化"""
        self.clients = {}
        self.setup_clients()

    def setup_clients(self):
        """各SNSクライアントのセットアップ"""
        # Blueskyのセットアップ
        try:
            bluesky_username = os.getenv("BLUESKY_USERNAME")
            bluesky_password = os.getenv("BLUESKY_PASSWORD")
            if bluesky_username and bluesky_password:
                bluesky_client = AtprotoClient()
                bluesky_client.login(bluesky_username, bluesky_password)
                self.clients["bluesky"] = bluesky_client
        except Exception as e:
            print(f"Bluesky setup error: {e}")

        # X/Twitterのセットアップ
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
        # Misskeyのセットアップ
        try:
            misskey_token = os.getenv("MISSKEY_API_TOKEN")
            misskey_instance = os.getenv("MISSKEY_INSTANCE_URL")
            if misskey_token and misskey_instance:
                misskey_client = misskey.Misskey(misskey_instance, i=misskey_token)
                self.clients["misskey"] = misskey_client
        except Exception as e:
            print(f"Misskey setup error: {e}")
        # Threadsのセットアップ
        try:
            threads_instance = os.getenv("THREADS_ACCESS_TOKEN")
            if threads_instance:
                self.clients["threads"] = threads_instance
        except Exception as e:
            print(f"Misskey setup error: {e}")

        # Mastodonのセットアップ
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

    def post_to_bluesky(self, content, image_path=None):
        """Blueskyに投稿する関数（画像対応・1MB制限対応）"""
        try:
            if "bluesky" in self.clients:
                bluesky_username = os.getenv("BLUESKY_USERNAME")
                bluesky_password = os.getenv("BLUESKY_PASSWORD")
                bluesky_client = AtprotoClient()
                bluesky_client.login(bluesky_username, bluesky_password)
                self.clients["bluesky"] = bluesky_client
                if image_path:
                    # 画像サイズが1MB超ならリサイズ・圧縮
                    max_size = 976 * 1024  # 976.56KB
                    with open(image_path, "rb") as f:
                        img_bytes = f.read()
                    if len(img_bytes) > max_size:
                        img = Image.open(io.BytesIO(img_bytes))
                        # JPEG/PNGのみ対応
                        format = img.format if img.format in ["JPEG", "PNG"] else "JPEG"
                        # サイズを縮小しながら圧縮
                        quality = 85
                        for _ in range(10):
                            buf = io.BytesIO()
                            img.save(buf, format=format, quality=quality, optimize=True)
                            if buf.tell() <= max_size:
                                break
                            # さらに圧縮
                            quality -= 10
                            if quality < 30:
                                img = img.resize(
                                    (int(img.width * 0.8), int(img.height * 0.8))
                                )
                                quality = 85
                        buf.seek(0)
                        blob = bluesky_client.com.atproto.repo.upload_blob(buf)
                    else:
                        with open(image_path, "rb") as f:
                            blob = bluesky_client.com.atproto.repo.upload_blob(f)
                    response = bluesky_client.send_post(
                        content,
                        embed={
                            "$type": "app.bsky.embed.images",
                            "images": [{"alt": "image", "image": blob["blob"]}],
                        },
                    )
                else:
                    response = bluesky_client.send_post(content)
                return {"success": True, "response": "投稿成功"}
            return {
                "success": False,
                "error": "Blueskyクライアントが設定されていません",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_x(self, content, image_path=None):
        try:
            if "x" in self.clients:
                if image_path:
                    # v2 API: media/upload (OAuth1.0a) で画像アップロード
                    x_api_key = os.getenv("X_API_KEY")
                    x_api_secret = os.getenv("X_API_SECRET")
                    x_access_token = os.getenv("X_ACCESS_TOKEN")
                    x_access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

                    oauth = OAuth1(
                        x_api_key, x_api_secret, x_access_token, x_access_token_secret
                    )
                    upload_url = "https://upload.twitter.com/1.1/media/upload.json"
                    with open(image_path, "rb") as f:
                        files = {"media": f}
                        resp = requests.post(upload_url, files=files, auth=oauth)
                    if resp.status_code != 200:
                        return {
                            "success": False,
                            "error": f"media/upload失敗: {resp.text}",
                        }
                    media_id = resp.json().get("media_id_string")
                    # ツイート投稿（v2）
                    tweet = self.clients["x"].create_tweet(
                        text=content, media_ids=[media_id]
                    )
                else:
                    tweet = self.clients["x"].create_tweet(text=content)
                return {"success": True, "response": "投稿成功"}
            return {"success": False, "error": "Xクライアントが設定されていません"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_threads(self, content, image_path=None):
        """Threadsにテキストのみ投稿（画像は未対応）"""
        try:
            if image_path:
                return {"success": False, "error": "Threadsは画像投稿に未対応です"}
            ACESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
            API_BASE_URL = "https://graph.threads.net/v1.0"
            user_url = f"{API_BASE_URL}/me"
            user_headers = {"Authorization": f"Bearer {ACESS_TOKEN}"}
            user_response = requests.get(user_url, headers=user_headers)
            if user_response.ok:
                user_id = user_response.json().get("id")
                create_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
                create_data = {"text": content, "media_type": "TEXT"}
                create_headers = {
                    "Authorization": f"Bearer {ACESS_TOKEN}",
                    "Content-Type": "application/json",
                }
                response = requests.post(
                    create_url, json=create_data, headers=create_headers
                )
                if response.ok:
                    creation_id = response.json().get("id")
                    publish_url = (
                        f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
                    )
                    data = {"creation_id": creation_id}
                    headers = {
                        "Authorization": f"Bearer {ACESS_TOKEN}",
                        "Content-Type": "application/json",
                    }
                    requests.post(publish_url, json=data, headers=headers)
                    return {"success": True, "response": "投稿成功"}
                else:
                    return {"success": False, "error": "Threads投稿APIエラー"}
            return {
                "success": False,
                "error": "Threadsクライアントが設定されていません",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_misskey(self, content, image_path=None):
        """Misskeyに投稿する関数（画像対応）"""
        try:
            if "misskey" in self.clients:
                if image_path:
                    with open(image_path, "rb") as f:
                        file_obj = self.clients["misskey"].drive_files_create(file=f)
                    note = self.clients["misskey"].notes_create(
                        text=content,
                        file_ids=[file_obj["id"]],
                        visibility=misskey.enum.NoteVisibility.HOME,
                    )
                else:
                    note = self.clients["misskey"].notes_create(
                        text=content, visibility=misskey.enum.NoteVisibility.HOME
                    )
                return {"success": True, "response": "投稿成功"}
            return {
                "success": False,
                "error": "Misskeyクライアントが設定されていません",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_mastodon(self, content, image_path=None):
        """Mastodonに投稿する関数（画像対応）"""
        try:
            if "mastodon" in self.clients:
                if image_path:
                    media = self.clients["mastodon"].media_post(image_path)
                    status = self.clients["mastodon"].status_post(
                        content, media_ids=[media["id"]]
                    )
                else:
                    status = self.clients["mastodon"].status_post(content)
                return {"success": True, "response": "投稿成功"}
            return {
                "success": False,
                "error": "Mastodonクライアントが設定されていません",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_platforms(self, posts):
        """複数のプラットフォームに投稿する関数

        Args:
            posts: プラットフォーム名をキー、{"content":..., "image_path":...}を値とする辞書

        Returns:
            各プラットフォームの投稿結果を含む辞書
        """
        results = {}
        for platform, post in posts.items():
            content = post.get("content")
            image_path = post.get("image_path")
            if platform == "bluesky" and content:
                results["bluesky"] = self.post_to_bluesky(content, image_path)
            elif platform == "x" and content:
                results["x"] = self.post_to_x(content, image_path)
            elif platform == "threads" and content:
                results["threads"] = self.post_to_threads(content, image_path)
            elif platform == "misskey" and content:
                results["misskey"] = self.post_to_misskey(content, image_path)
            elif platform == "mastodon" and content:
                results["mastodon"] = self.post_to_mastodon(content, image_path)
        return results


# SNSクライアントのインスタンス
sns_client = SnsClient()
