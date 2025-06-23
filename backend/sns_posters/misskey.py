import logging

import misskey

logger = logging.getLogger(__name__)


class MisskeyPoster:
    """
    Misskeyへの投稿処理を担当するクラス。
    画像アップロードやノート投稿のラッパー。
    """

    def __init__(self, client):
        """
        MisskeyPosterの初期化。
        Args:
            client: Misskeyクライアントインスタンス
        """
        self.client = client

    def upload_images(self, image_paths):
        """
        画像ファイルをMisskeyにアップロードし、file_idリストを返す。
        Args:
            image_paths: 画像ファイルパスのリスト
        Returns:
            (file_ids, None) or (None, error_message)
        """
        file_ids = []
        for image_path in image_paths:
            with open(image_path, "rb") as f:
                file_obj = self.client.drive_files_create(file=f)
            file_ids.append(file_obj["id"])
        return file_ids, None

    def post(self, content, image_paths=None):
        """
        Misskeyにノートを投稿する。
        Args:
            content: 投稿テキスト
            image_paths: 画像ファイルパスのリスト（省略可）
        Returns:
            投稿結果のdict
        """
        try:
            file_ids = []
            if image_paths:
                file_ids, err = self.upload_images(image_paths)
                if err:
                    return {"success": False, "error": err}
            if file_ids:
                self.client.notes_create(
                    text=content,
                    file_ids=file_ids,
                    visibility=misskey.enum.NoteVisibility.HOME,
                )
            else:
                self.client.notes_create(
                    text=content, visibility=misskey.enum.NoteVisibility.HOME
                )
            return {"success": True, "response": "投稿成功"}
        except Exception as e:
            logger.error(f"Misskey投稿エラー: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
