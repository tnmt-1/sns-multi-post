import misskey


class MisskeyPoster:
    def __init__(self, client):
        self.client = client

    def upload_images(self, image_paths):
        file_ids = []
        for image_path in image_paths:
            with open(image_path, "rb") as f:
                file_obj = self.client.drive_files_create(file=f)
            file_ids.append(file_obj["id"])
        return file_ids, None

    def post(self, content, image_paths=None):
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
            return {"success": False, "error": str(e)}
