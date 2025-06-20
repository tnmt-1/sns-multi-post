from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from sns_client import sns_client, get_character_limits
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# .envファイルから環境変数を読み込む
load_dotenv()

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)  # CORS設定を有効に

# Flaskの秘密鍵を設定
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def index():
    """フロントエンドのindex.htmlを返す"""
    return send_from_directory("../frontend", "index.html")


@app.route("/api/platforms", methods=["GET"])
def get_platforms():
    """利用可能なプラットフォームの一覧と文字数制限を返す"""
    platforms = {
        "bluesky": {
            "enabled": "bluesky" in sns_client.clients,
            "limit": get_character_limits()["bluesky"],
        },
        "x": {
            "enabled": "x" in sns_client.clients,
            "limit": get_character_limits()["x"],
        },
        "threads": {
            "enabled": "threads" in sns_client.clients,
            "limit": get_character_limits()["threads"],
        },
        "misskey": {
            "enabled": "misskey" in sns_client.clients,
            "limit": get_character_limits()["misskey"],
        },
        "mastodon": {
            "enabled": "mastodon" in sns_client.clients,
            "limit": get_character_limits()["mastodon"],
        },
    }
    return jsonify(platforms)


@app.route("/api/post", methods=["POST"])
def post_to_sns():
    """選択されたSNSに投稿する（画像対応・複数画像）"""
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        # multipartの場合
        post_data_json = request.form.get("postData")
        if not post_data_json:
            return jsonify({"success": False, "error": "postDataがありません"}), 400
        data = json.loads(post_data_json)
        # 複数画像対応
        image_files = []
        image_paths = []
        for key in sorted(request.files):
            if key.startswith("image"):
                file = request.files.get(key)
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(image_path)
                    image_files.append(file)
                    image_paths.append(image_path)
    else:
        # application/jsonの場合
        data = request.json
        image_paths = []

    if not data:
        return jsonify({"success": False, "error": "データが送信されていません"}), 400

    posts = {}
    for platform in ["bluesky", "x", "threads", "misskey", "mastodon"]:
        if platform in data and data[platform]["selected"]:
            posts[platform] = {
                "content": data[platform]["content"],
                "image_paths": image_paths if image_paths else None,
            }

    if not posts:
        return jsonify(
            {"success": False, "error": "投稿先のSNSが選択されていません"}
        ), 400

    # 各プラットフォームに投稿
    results = sns_client.post_to_platforms(posts)

    # 全体の成功・失敗を判定
    all_success = all(result.get("success", False) for result in results.values())

    # 1SNSのみの場合はトップレベルに展開
    if len(results) == 1:
        platform, result = next(iter(results.items()))
        response = {"platform": platform, **result}
        return jsonify(response)

    return jsonify({"success": all_success, "results": results})


@app.route("/api/character_limits", methods=["GET"])
def character_limits():
    """各SNSの文字数制限を返す"""
    return jsonify(get_character_limits())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
