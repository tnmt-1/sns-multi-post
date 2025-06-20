"""
Blueskyへの投稿処理を担当するクラス。
画像圧縮・アップロード、投稿処理をラップする。

Attributes:
    client: Bluesky APIクライアントインスタンス
"""

from backend.constants import IMAGE_LIMITS


class BlueskyPoster:
    def __init__(self, client):
        """
        BlueskyPosterの初期化。

        Args:
            client: Bluesky APIクライアント
        """
        self.client = client

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
        try:
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
                )
            else:
                self.client.send_post(content)
            return {"success": True, "response": "投稿成功"}
        except Exception as e:
            return {"success": False, "error": str(e)}
