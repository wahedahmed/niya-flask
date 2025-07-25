from flask import Flask, render_template, request, redirect, session, jsonify
from datetime import date
import sqlite3
import random
import datetime

app = Flask(__name__)
app.secret_key = "niya_secret"

MOTIVATIONS = [
    "كل يوم بداية جديدة 💪",
    "نيتك اليوم تصنع غدك ✨",
    "ابدأ ولا تتردد!",
    "إحنا مستنيين نشوف حلمك يتحقق 😄"
]

QUOTES = [
    "كل يوم فرصة جديدة لنية جميلة 💛",
    "وجودك هنا يهمنا… شاركنا نيتك وأدعم غيرك!",
    "كل كلمة دعم منك بتغير يوم حد غيرك.",
    "احنا هنا عيلة… وأنت ركن مهم فيها 🤍",
    "لا يوجد شيء أجمل من نية صافية وبداية جديدة.",
    "إحنا هنا عشان نكبر سوا، خطوة بخطوة.",
    "كل نية بتكتبها بتنور طريقك وطريق حد تاني.",
    "خليك دايمًا سبب في نشر الأمل! 🌱",
    "حتى لو نيتك بسيطة… ليها معنى كبير عندنا.",
]

BAD_WORDS = [
    'غبي', 'احمق', 'قذر', 'غبية', 'بشع', 'حقير', 'خرا', 'عبيط', 'تفوو', 'خنزير', 'سخيف', 'وسخ'
]

def init_db():
    con = sqlite3.connect('niya.db')
    cur = con.cursor()
    # users table
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')
    # intentions table
    cur.execute('''CREATE TABLE IF NOT EXISTS intentions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        created_at DATE,
        is_public INTEGER
    )''')
    # comments table
    cur.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intention_id INTEGER,
        user_id INTEGER,
        text TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    # likes table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            intention_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, intention_id)
        )
    ''')
    con.commit()
    con.close()

init_db()

# دالة تحويل الوقت لصيغة "منذ..."
def time_ago(dt):
    now = datetime.datetime.now()
    if isinstance(dt, str):
        try:
            dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        except:
            dt = datetime.datetime.strptime(dt, "%Y-%m-%d")
    diff = now - dt
    seconds = diff.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = diff.days
    if seconds < 60:
        return "الآن"
    elif minutes < 60:
        return f"منذ {int(minutes)} دقيقة"
    elif hours < 24:
        return f"منذ {int(hours)} ساعة"
    elif days == 1:
        return "أمس"
    elif days < 7:
        return f"منذ {days} أيام"
    else:
        return dt.strftime("%d/%m/%Y")

# تسجيل مستخدم جديد
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        con = sqlite3.connect('niya.db')
        cur = con.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?', (username,))
        if cur.fetchone():
            error = "اسم المستخدم موجود بالفعل!"
        else:
            cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            con.commit()
            con.close()
            return redirect('/login')
        con.close()
    return render_template('register.html', error=error)

# تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        con = sqlite3.connect('niya.db')
        cur = con.cursor()
        cur.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        con.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/')
        else:
            error = "بيانات خاطئة!"
    return render_template('login.html', error=error)

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# الصفحة الرئيسية - عرض كل النوايا العامة + احصائيات + اقتباسات + ترحيب
@app.route('/', methods=['GET'])
def home():
    if 'user_id' not in session:
        return redirect('/login')
    hour = datetime.datetime.now().hour
    username = session.get('username', 'زائر جميل')
    greeting = "صباح النور" if hour < 12 else ("مساء الورد" if hour < 18 else "مساء الخير")
    quote = random.choice(QUOTES)
    con = sqlite3.connect('niya.db')
    cur = con.cursor()
    cur.execute('SELECT COUNT(*) FROM intentions WHERE is_public = 1')
    public_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM comments')
    comments_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM users')
    users_count = cur.fetchone()[0]
    cur.execute('''
        SELECT intentions.id, intentions.text, intentions.created_at
        FROM intentions
        WHERE intentions.is_public = 1
        ORDER BY intentions.created_at DESC
    ''')
    raw_intentions = cur.fetchall()
    intentions = []
    likes_dict = {}
    user_likes = set()
    for i in raw_intentions:
        # عد اللايكات
        cur.execute('SELECT COUNT(*) FROM likes WHERE intention_id=?', (i[0],))
        likes_dict[i[0]] = cur.fetchone()[0]
        # هل المستخدم ضغط لايك؟
        cur.execute('SELECT 1 FROM likes WHERE user_id=? AND intention_id=?', (session['user_id'], i[0]))
        if cur.fetchone():
            user_likes.add(i[0])
        # عرض التاريخ "منذ..."
        intentions.append((i[0], i[1], time_ago(i[2])))
    comments_dict = {}
    for i in intentions:
        cur.execute('''
            SELECT comments.text, comments.created_at
            FROM comments
            WHERE comments.intention_id = ?
            ORDER BY comments.created_at ASC
        ''', (i[0],))
        comments_dict[i[0]] = cur.fetchall()
    con.close()
    motivation = random.choice(MOTIVATIONS)
    return render_template(
        'home.html',
        username=username,
        greeting=greeting,
        quote=quote,
        public_count=public_count,
        comments_count=comments_count,
        users_count=users_count,
        motivation=motivation,
        intentions=intentions,
        comments_dict=comments_dict,
        likes_dict=likes_dict,
        user_likes=user_likes
    )

# تفعيل/إلغاء الإعجاب على النوايا (AJAX)
@app.route('/like/<int:intention_id>', methods=['POST'])
def like_intention(intention_id):
    if 'user_id' not in session:
        return jsonify({'status':'error', 'msg':'Unauthorized'}), 401
    user_id = session['user_id']
    con = sqlite3.connect('niya.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM likes WHERE user_id=? AND intention_id=?', (user_id, intention_id))
    liked = cur.fetchone()
    if liked:
        cur.execute('DELETE FROM likes WHERE user_id=? AND intention_id=?', (user_id, intention_id))
        liked = False
    else:
        cur.execute('INSERT OR IGNORE INTO likes (user_id, intention_id) VALUES (?, ?)', (user_id, intention_id))
        liked = True
    con.commit()
    cur.execute('SELECT COUNT(*) FROM likes WHERE intention_id=?', (intention_id,))
    count = cur.fetchone()[0]
    con.close()
    return jsonify({'liked': liked, 'count': count})

# نشر نية جديدة
@app.route('/new', methods=['GET', 'POST'])
def new_intention():
    if 'user_id' not in session:
        return redirect('/login')
    error = None
    if request.method == 'POST':
        text = request.form['text']
        if len(text.strip()) < 4:
            error = "اكتب نية مفيدة يا نجم!"
        elif any(bad in text for bad in BAD_WORDS):
            error = "لسانك عسل يا نجم، النية دي مش مقبولة!"
        else:
            con = sqlite3.connect('niya.db')
            cur = con.cursor()
            cur.execute('INSERT INTO intentions (user_id, text, created_at, is_public) VALUES (?, ?, date("now"), 1)', (session['user_id'], text))
            con.commit()
            con.close()
            return redirect('/')
    return render_template('new.html', error=error)

# التعليق على النوايا
@app.route('/comment/<int:intention_id>', methods=['POST'])
def comment(intention_id):
    if 'user_id' not in session:
        return redirect('/login')
    comment_text = request.form['comment']
    if any(bad in comment_text for bad in BAD_WORDS):
        return "<div style='color:red;padding:1em'>لسانك عسل يا نجم، ما تجرحش الناس! <a href='/'>رجوع</a></div>"
    con = sqlite3.connect('niya.db')
    cur = con.cursor()
    cur.execute('INSERT INTO comments (intention_id, user_id, text) VALUES (?, ?, ?)', (intention_id, session['user_id'], comment_text))
    con.commit()
    con.close()
    return redirect('/')

# صفحة البروفايل وعرض النوايا الخاصة بك
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    con = sqlite3.connect('niya.db')
    cur = con.cursor()
    cur.execute('SELECT username FROM users WHERE id=?', (session['user_id'],))
    username = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM intentions WHERE user_id=?', (session['user_id'],))
    intentions_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM comments WHERE user_id=?', (session['user_id'],))
    comments_count = cur.fetchone()[0]
    cur.execute('SELECT id, text, created_at, is_public FROM intentions WHERE user_id=? ORDER BY created_at DESC', (session['user_id'],))
    my_intentions = cur.fetchall()
    comments_for_my_intentions = {}
    for i in my_intentions:
        cur.execute('''
            SELECT comments.text, comments.created_at
            FROM comments
            WHERE comments.intention_id = ?
            ORDER BY comments.created_at ASC
        ''', (i[0],))
        comments_for_my_intentions[i[0]] = cur.fetchall()
    con.close()
    return render_template(
        'profile.html',
        username=username,
        intentions_count=intentions_count,
        comments_count=comments_count,
        my_intentions=my_intentions,
        comments_for_my_intentions=comments_for_my_intentions
    )

# تعديل نية
@app.route('/edit/<int:intention_id>', methods=['GET', 'POST'])
def edit_intention(intention_id):
    if 'user_id' not in session:
        return redirect('/login')
    con = sqlite3.connect('niya.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM intentions WHERE id=? AND user_id=?', (intention_id, session['user_id']))
    intention = cur.fetchone()
    if not intention:
        con.close()
        return redirect('/profile')
    if request.method == 'POST':
        new_text = request.form['text']
        is_public = 1 if 'is_public' in request.form else 0
        if len(new_text.strip()) < 4:
            con.close()
            return render_template('edit.html', intention=intention, error="النية قصيرة جدًا!")
        elif any(bad in new_text for bad in BAD_WORDS):
            con.close()
            return render_template('edit.html', intention=intention, error="لسانك عسل يا نجم، النية دي مش مقبولة!")
        cur.execute('UPDATE intentions SET text=?, is_public=? WHERE id=?', (new_text, is_public, intention_id))
        con.commit()
        con.close()
        return redirect('/profile')
    con.close()
    return render_template('edit.html', intention=intention, error=None)

# حذف نية
@app.route('/delete/<int:intention_id>')
def delete_intention(intention_id):
    if 'user_id' not in session:
        return redirect('/login')
    con = sqlite3.connect('niya.db')
    cur = con.cursor()
    cur.execute('DELETE FROM intentions WHERE id=? AND user_id=?', (intention_id, session['user_id']))
    con.commit()
    con.close()
    return redirect('/profile')

# شغّل السيرفر
if __name__ == "__main__":
    app.run(debug=True)
