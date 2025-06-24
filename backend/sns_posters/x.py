"""
X（旧Twitter）への投稿処理を担当するクラス。
画像アップロード・投稿処理をラップする。

Attributes:
    client: X APIクライアントインスタンス
"""

import os
import logging
from constants import IMAGE_LIMITS

from requests_oauthlib import OAuth1
import requests

logger = logging.getLogger(__name__)


class XPoster:
    def __init__(self, client):
        """
        XPosterの初期化。

        Args:
            client: X APIクライアント
        """
        self.client = client

    def upload_images(self, image_paths):
        """
        画像をXにアップロードする。

        Args:
            image_paths: 画像ファイルパスのリスト
        Returns:
            (media_idリスト, エラー文字列)
        """
        media_ids = []
        x_api_key = os.getenv("X_API_KEY")
        x_api_secret = os.getenv("X_API_SECRET")
        x_access_token = os.getenv("X_ACCESS_TOKEN")
        x_access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
        oauth = OAuth1(x_api_key, x_api_secret, x_access_token, x_access_token_secret)
        upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        for image_path in image_paths:
            with open(image_path, "rb") as f:
                files = {"media": f}
                resp = requests.post(upload_url, files=files, auth=oauth)
            if resp.status_code != 200:
                return None, f"media/upload失敗: {resp.text}"
            media_id = resp.json().get("media_id_string")
            media_ids.append(media_id)
        return media_ids, None

    def post(self, content, image_paths):
        """
        Xへ投稿を行う。

        Args:
            content: 投稿本文
            image_paths: 画像ファイルパスのリスト
        Returns:
            dict: 投稿結果（success, response/error）
        """
        try:
            media_ids = []
            err = None
            if image_paths:
                max_images = IMAGE_LIMITS["x"]["max_images"]
                if len(image_paths) > max_images:
                    return {"success": False, "error": f"画像は{max_images}枚までです"}
                media_ids, err = self.upload_images(image_paths)
                if err:
                    return {"success": False, "error": err}
            if media_ids:
                self.client.create_tweet(text=content, media_ids=media_ids)
            else:
                self.client.create_tweet(text=content)
            return {"success": True, "response": "投稿成功"}
        except Exception as e:
            logger.error(f"X投稿エラー: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
