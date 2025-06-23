"""
Threadsへの投稿処理を担当するクラス。
画像投稿は未対応。

Attributes:
    access_token: Threads API用アクセストークン
"""

import logging

logger = logging.getLogger(__name__)


class ThreadsPoster:
    def __init__(self, access_token):
        """
        ThreadsPosterの初期化。

        Args:
            access_token: Threads API用アクセストークン
        """
        self.access_token = access_token

    def post(self, content, image_paths=None):
        """
        Threadsへ投稿を行う。
        画像投稿は未対応。

        Args:
            content: 投稿本文
            image_paths: 画像ファイルパスのリスト（未使用）
        Returns:
            dict: 投稿結果（success, response/error）
        """
        import requests

        if image_paths:
            return {"success": False, "error": "Threadsは画像投稿に未対応です"}
        try:
            API_BASE_URL = "https://graph.threads.net/v1.0"
            user_url = f"{API_BASE_URL}/me"
            user_headers = {"Authorization": f"Bearer {self.access_token}"}
            user_response = requests.get(user_url, headers=user_headers)
            if user_response.ok:
                user_id = user_response.json().get("id")
                create_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
                create_data = {"text": content, "media_type": "TEXT"}
                create_headers = {
                    "Authorization": f"Bearer {self.access_token}",
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
                        "Authorization": f"Bearer {self.access_token}",
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
            logger.error(f"Threads投稿エラー: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
