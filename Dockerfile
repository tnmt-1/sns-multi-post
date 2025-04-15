FROM python:3.10-slim

WORKDIR /app

# 必要なパッケージをインストール
COPY ./backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . /app/

# 環境変数の設定
ENV FLASK_APP=backend/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5001

# ポートを公開
EXPOSE 5001

# アプリケーションの実行
CMD ["flask", "run"]
