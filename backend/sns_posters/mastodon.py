"""
Mastodonへの投稿処理を担当するクラス。
画像アップロード・投稿処理をラップする。

Attributes:
    client: Mastodon APIクライアントインスタンス
"""


class MastodonPoster:
    def __init__(self, client):
        """
        MastodonPosterの初期化。

        Args:
            client: Mastodon APIクライアント
        """
        self.client = client

    def upload_images(self, image_paths):
        """
        画像をMastodonにアップロードする。

        Args:
            image_paths: 画像ファイルパスのリスト
        Returns:
            (media_idリスト, エラー文字列)
        """
        media_ids = []
        for image_path in image_paths:
            media = self.client.media_post(image_path)
            media_ids.append(media["id"])
        return media_ids, None

    def post(self, content, image_paths=None):
        """
        Mastodonへ投稿を行う。

        Args:
            content: 投稿本文
            image_paths: 画像ファイルパスのリスト
        Returns:
            dict: 投稿結果（success, response/error）
        """
        try:
            media_ids = []
            if image_paths:
                media_ids, err = self.upload_images(image_paths)
                if err:
                    return {"success": False, "error": err}
            if media_ids:
                self.client.status_post(content, media_ids=media_ids)
            else:
                self.client.status_post(content)
            return {"success": True, "response": "投稿成功"}
        except Exception as e:
            return {"success": False, "error": str(e)}
