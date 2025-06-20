class MastodonPoster:
    def __init__(self, client):
        self.client = client

    def upload_images(self, image_paths):
        media_ids = []
        for image_path in image_paths:
            media = self.client.media_post(image_path)
            media_ids.append(media["id"])
        return media_ids, None

    def post(self, content, image_paths=None):
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
