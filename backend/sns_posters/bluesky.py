"""
Blueskyへの投稿処理を担当するクラス。
画像圧縮・アップロード、投稿処理をラップする。

Attributes:
    client: Bluesky APIクライアントインスタンス
"""

from constants import IMAGE_LIMITS
import logging

logger = logging.getLogger(__name__)


class BlueskyPoster:
    def __init__(self, client, username=None, password=None):
        """
        BlueskyPosterの初期化。

        Args:
            client: Bluesky APIクライアント
            username: Blueskyユーザー名（リフレッシュ用）
            password: Blueskyパスワード（リフレッシュ用）
        """
        self.client = client
        self.username = username
        self.password = password

    def compress_image(self, compress_image_for_platform, image_path):
        """
        Bluesky用に画像を圧縮する。

        Args:
            compress_image_for_platform: 圧縮関数
            image_path: 画像ファイルパス
        Returns:
            (圧縮後バッファ, エラー文字列)
        """
        return compress_image_for_platform(
            image_path,
            max_size=IMAGE_LIMITS["bluesky"]["max_size"],
            min_size=IMAGE_LIMITS["bluesky"]["min_size"],
            max_attempts=IMAGE_LIMITS["bluesky"]["max_attempts"],
        )

    def upload_images(self, compress_image_for_platform, image_paths):
        """
        画像をBlueskyにアップロードする。

        Args:
            compress_image_for_platform: 圧縮関数
            image_paths: 画像ファイルパスのリスト
        Returns:
            (アップロード済み画像リスト, エラー文字列)
        """
        images = []
        for image_path in image_paths:
            buf, err = self.compress_image(compress_image_for_platform, image_path)
            if buf is None:
                return None, err
            blob = self.client.com.atproto.repo.upload_blob(buf)
            images.append({"alt": "image", "image": blob["blob"]})
        return images, None

    def post(self, content, image_paths, compress_image_for_platform):
        """
        Blueskyへ投稿を行う。

        Args:
            content: 投稿本文
            image_paths: 画像ファイルパスのリスト
            compress_image_for_platform: 画像圧縮関数
        Returns:
            dict: 投稿結果（success, response/error）
        """

        def try_post():
            images = []
            err = None
            if image_paths:
                images, err = self.upload_images(
                    compress_image_for_platform, image_paths
                )
                if err:
                    return {"success": False, "error": err}
            if images:
                self.client.send_post(
                    content,
                    embed={
                        "$type": "app.bsky.embed.images",
                        "images": images,
                    },
                    langs=["ja"],
                )
            else:
                self.client.send_post(content, langs=["ja"])
            return {"success": True, "response": "投稿成功"}

        try:
            return try_post()
        except Exception as e:
            logger.error(f"Bluesky投稿エラー: {str(e)}", exc_info=True)
            # InvalidTokenエラー時はリフレッシュして再試行
            def is_invalid_token_error(e):
                # 1. e.args[0]がstr型で"InvalidToken"を含む
                if hasattr(e, "args") and e.args:
                    if isinstance(e.args[0], str) and "InvalidToken" in e.args[0]:
                        return True
                    # 2. atproto_client.exceptions.BadRequestError等: e.args[0].content.error == "InvalidToken"
                    if hasattr(e.args[0], "content") and getattr(e.args[0].content, "error", None) == "InvalidToken":
                        return True
                # 3. e.error属性が"InvalidToken"
                if hasattr(e, "error") and getattr(e, "error", None) == "InvalidToken":
                    return True
                return False

            if is_invalid_token_error(e):
                try:
                    # loginにはユーザー名・パスワードが必要
                    if (
                        hasattr(self.client, "login")
                        and self.username
                        and self.password
                    ):
                        self.client.login(self.username, self.password)
                    else:
                        return {
                            "success": False,
                            "error": "Bluesky認証情報が不足しています（ユーザー名・パスワード）",
                        }
                    return try_post()
                except Exception as e2:
                    logger.error(f"Blueskyリフレッシュ失敗: {str(e2)}", exc_info=True)
                    return {"success": False, "error": f"リフレッシュ失敗: {str(e2)}"}
            return {"success": False, "error": str(e)}
