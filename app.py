from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime
import pytz

app = Flask(__name__)

# 이미지 업로드 설정
app.config['UPLOAD_FOLDER'] = 'static'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB 제한

# 홈 화면: 리뷰 리스트 불러오기
@app.route("/")
def index():
    sort = request.args.get("sort", "date")  # 기본값은 date

    if sort == "rating":
        order_clause = "ORDER BY rating DESC"
    else:
        order_clause = "ORDER BY created_at DESC"

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT id, title, director, rating, comment, poster_filename
        FROM reviews
        {order_clause}
    """)
    reviews = [
        {
            'id': row[0],
            'title': row[1],
            'director': row[2],
            'rating': row[3],
            'comment': row[4],
            'poster': row[5]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return render_template("index.html", reviews=reviews, sort=sort)

# 리뷰 작성 페이지
@app.route("/write")
def write():
    return render_template("write.html")

# 리뷰 저장 처리
@app.route("/save", methods=["POST"])
def save():
    title = request.form['title']
    director = request.form['director']
    rating = int(request.form['rating'])
    comment = request.form['comment']
    detail = request.form['detail']
    author = request.form['author']
    
    # 이미지 업로드 처리
    poster_file = request.files['poster']
    poster_filename = secure_filename(poster_file.filename)
    poster_file.save(os.path.join(app.config['UPLOAD_FOLDER'], poster_filename))

    # 현재 한국 시간 가져오기
    kst = pytz.timezone('Asia/Seoul')
    created_at = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

    # DB 저장
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO reviews (title, director, rating, comment, detail, poster_filename, created_at, author)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, director, rating, comment, detail, poster_filename, created_at, author))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))

# 상세 페이지
@app.route("/review/<int:review_id>")
def review_detail(review_id):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, director, rating, comment, detail, poster_filename, created_at, author
        FROM reviews
        WHERE id = ?
    """, (review_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        review = {
            'id': row[0],
            'title': row[1],           # ✅ 여기 수정됨!
            'director': row[2],
            'rating': row[3],
            'comment': row[4],
            'detail': row[5],
            'poster': row[6],
            'created_at': row[7],
            'author': row[8]
        }
        return render_template("detail.html", review=review)
    else:
        return "리뷰를 찾을 수 없습니다.", 404

# 삭제 기능
@app.route("/delete/<int:review_id>", methods=["POST"])
def delete(review_id):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route("/edit/<int:review_id>")
def edit(review_id):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, director, rating, comment, detail, poster_filename
        FROM reviews
        WHERE id = ?
    """, (review_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        review = {
            'id': row[0],
            'title': row[1],
            'director': row[2],
            'rating': row[3],
            'comment': row[4],
            'detail': row[5],
            'poster': row[6]
        }
        return render_template("edit.html", review=review)
    else:
        return "리뷰를 찾을 수 없습니다.", 404
    
@app.route("/update/<int:review_id>", methods=["POST"])
def update(review_id):
    title = request.form['title']
    director = request.form['director']
    rating = int(request.form['rating'])
    comment = request.form['comment']
    detail = request.form['detail']

    # 포스터 파일이 새로 업로드되었는지 확인
    poster_file = request.files['poster']
    if poster_file and poster_file.filename:
        poster_filename = secure_filename(poster_file.filename)
        poster_file.save(os.path.join(app.config['UPLOAD_FOLDER'], poster_filename))
    else:
        # 기존 포스터 유지
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("SELECT poster_filename FROM reviews WHERE id = ?", (review_id,))
        poster_filename = cursor.fetchone()[0]
        conn.close()

    # DB 업데이트
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE reviews
        SET title = ?, director = ?, rating = ?, comment = ?, detail = ?, poster_filename = ?
        WHERE id = ?
    """, (title, director, rating, comment, detail, poster_filename, review_id))
    conn.commit()
    conn.close()

    return redirect(url_for('review_detail', review_id=review_id))

# 서버 실행
if __name__ == "__main__":
    app.run(debug=True)