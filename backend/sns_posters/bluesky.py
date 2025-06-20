from constants import IMAGE_LIMITS


class BlueskyPoster:
    def __init__(self, client):
        self.client = client

    def compress_image(self, compress_image_for_platform, image_path):
        return compress_image_for_platform(
            image_path,
            max_size=IMAGE_LIMITS["bluesky"]["max_size"],
            min_size=IMAGE_LIMITS["bluesky"]["min_size"],
            max_attempts=IMAGE_LIMITS["bluesky"]["max_attempts"],
        )

    def upload_images(self, compress_image_for_platform, image_paths):
        images = []
        for image_path in image_paths:
            buf, err = self.compress_image(compress_image_for_platform, image_path)
            if buf is None:
                return None, err
            blob = self.client.com.atproto.repo.upload_blob(buf)
            images.append({"alt": "image", "image": blob["blob"]})
        return images, None

    def post(self, content, image_paths, compress_image_for_platform):
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
