import os
import json
import requests
from atproto import Client as AtprotoClient
import tweepy
from mastodon import Mastodon
import misskey
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# 文字数制限の定義
CHARACTER_LIMITS = {
    "bluesky": 300,
    "x": 280,
    "threads": 500,
    "misskey": 3000,
    "mastodon": 500
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
                self.clients["threads"] =threads_instance
        except Exception as e:
            print(f"Misskey setup error: {e}")

        # Mastodonのセットアップ
        try:
            mastodon_token = os.getenv("MASTODON_ACCESS_TOKEN")
            mastodon_instance = os.getenv("MASTODON_INSTANCE_URL")
            if mastodon_token and mastodon_instance:
                mastodon_client = Mastodon(
                    access_token=mastodon_token,
                    api_base_url=mastodon_instance
                )
                self.clients["mastodon"] = mastodon_client
        except Exception as e:
            print(f"Mastodon setup error: {e}")
    def post_to_bluesky(self, content):
        """Blueskyに投稿する関数"""
        try:
            if "bluesky" in self.clients:
                response = self.clients["bluesky"].send_post(content)
                return {"success": True, "response": "投稿成功"}
            return {"success": False, "error": "Blueskyクライアントが設定されていません"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_x(self, content):
        try:
            if "x" in self.clients:
                tweet = self.clients["x"].create_tweet(text=content)
                return {"success": True, "response": "投稿成功"}
            return {"success": False, "error": "Xクライアントが設定されていません"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_threads(self, content):
        try:
            ACESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
            API_BASE_URL = "https://graph.threads.net/v1.0"
            user_url = f"{API_BASE_URL}/me"
            user_headers = {"Authorization": f"Bearer {ACESS_TOKEN}"}
            user_response = requests.get(user_url, headers=user_headers)
            if user_response.ok:
                user_id = user_response.json().get("id")
                create_url= f"https://graph.threads.net/v1.0/{user_id}/threads"
                create_data = {"text": content, "media_type": "TEXT"}
                create_headers = {
                    "Authorization": f"Bearer {ACESS_TOKEN}",
                    "Content-Type": "application/json",
                }
                response = requests.post(create_url, json=create_data, headers=create_headers)
                if response.ok:
                    creation_id = response.json().get("id")
                    publish_url= f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
                    data = {"creation_id": creation_id}
                    headers = {
                        "Authorization": f"Bearer {ACESS_TOKEN}",
                        "Content-Type": "application/json",
                    }
                    requests.post(publish_url, json=data, headers=headers)
                    return {"success": True, "response": "投稿成功"}
            return {"success": False, "error": "Threadsクライアントが設定されていません"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    def post_to_misskey(self, content):
        """Misskeyに投稿する関数"""
        try:
            if "misskey" in self.clients:
                note = self.clients["misskey"].notes_create(text=content)
                return {"success": True, "response": "投稿成功"}
            return {"success": False, "error": "Misskeyクライアントが設定されていません"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_mastodon(self, content):
        """Mastodonに投稿する関数"""
        try:
            if "mastodon" in self.clients:
                status = self.clients["mastodon"].status_post(content)
                return {"success": True, "response": "投稿成功"}
            return {"success": False, "error": "Mastodonクライアントが設定されていません"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_platforms(self, posts):
        """複数のプラットフォームに投稿する関数

        Args:
            posts: プラットフォーム名をキー、投稿内容を値とする辞書

        Returns:
            各プラットフォームの投稿結果を含む辞書
        """
        results = {}

        for platform, content in posts.items():
            if platform == "bluesky" and content:
                results["bluesky"] = self.post_to_bluesky(content)
            elif platform == "x" and content:
                results["x"] = self.post_to_x(content)
            elif platform == "threads" and content:
                results["threads"] = self.post_to_threads(content)
            elif platform == "misskey" and content:
                results["misskey"] = self.post_to_misskey(content)
            elif platform == "mastodon" and content:
                results["mastodon"] = self.post_to_mastodon(content)

        return results

# SNSクライアントのインスタンス
sns_client = SnsClient()
