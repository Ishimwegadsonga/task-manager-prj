from flask import Flask, render_template, request,redirect,session, flash
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "mysecretkey123"

 # database setup
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()



#====== users table =============

    cursor.execute('''
       CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
           )
       ''')

   #===== tasks table======
   # 
    cursor.execute('''
       CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL,
        due_date TEXT,
        priority TEXT,
        category TEXT,
        created_at TEXT
           ) 

        ''')  
 
    conn.commit()
    conn.close()

       #------ run database-------
init_db()

       #=------ routes ------

#show login page

@app.route('/')
def home():
    return render_template('practice.html', message="")

# handle login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        return render_template('practice.html', message="please fill all space")

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )
    user = cursor.fetchone()

    conn.close()

    if user:
        stored_password = user[2] # password is 3rd column
        # check if hashed password
        if check_password_hash(stored_password, password):
           session['username'] = username
           return redirect('/dashboard')
    
    return render_template('practice.html', message="wrong username or password")

    

#       register page         
@app.route('/register')
def register():
    return render_template('register.html', message="")



@app.route('/register', methods=['POST'])
def handle_register():
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            return render_template('register.html', message="please fill all field ")

        #---hash password-----
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        #----- check if exists----
        cursor.execute("SELECT * FROM users WHERE username=?",(username,))
        existing_user =cursor.fetchone()

        if existing_user:
            conn.close()
            return render_template('register.html', message="user already exist")
        else:
            cursor.execute(
                "INSERT INTO users(username,password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            conn.close()
            return render_template('practice.html', message="registered successful")



@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    if not username:
        return redirect('/')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    #==== get user id =====

    cursor.execute("SELECT id FROM users WHERE username=?", (username,)) 
    user = cursor.fetchone()
    user_id = user[0]

    #==== search tasks===

    search = request.args.get('search')

    status = request.args.get('status')
    sort = request.args.get('sort')

    if search:

        cursor.execute(
            "SELECT id, title, description, status, due_date, priority, category, created_at FROM tasks WHERE user_id=? AND title LIKE ?",
            (user_id, '%' + search + '%')

        )

    elif status:

           cursor.execute(
            "SELECT id, title, description, status, due_date, priority, category, created_at FROM tasks WHERE user_id=? AND status=?",
            (user_id, status)
        )

    else:
        if sort == "newest":
            
            cursor.execute(
             "SELECT id, title, description, status, due_date, priority, category, created_at FROM tasks WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        )

        elif sort == "oldest":

            cursor.execute(
                "SELECT id, title, description, status, due_date, priority, category, created_at FROM tasks WHERE user_id=? ORDER BY id ASC",
                (user_id,)
            )
        else:
            cursor.execute(
                "SELECT id, title, description, status, due_date, priority, category, created_at FROM tasks WHERE user_id=?",
                (user_id,)
            )

    tasks = cursor.fetchall()

    # ==== task counter=====

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=?",
        (user_id,)
     )
    total_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND status=?",
        (user_id,"completed")
    )

    completed_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*)FROM tasks WHERE user_id=? AND status=?",
        (user_id,"pending")
    )

    pending_tasks = cursor.fetchone()[0]

    #====== progress percentage=====

    if total_tasks > 0:
        progress = int((completed_tasks / total_tasks) * 100)
    else:
        progress = 0

    current_date = datetime.now().strftime("%Y-%m-%d")   

    conn.close()


    return render_template(
        'dashboard.html',
        username=username,
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        progress=progress,
        current_date=current_date
    )

    #=====  add tasks  =====

@app.route('/add_task', methods=['POST'])
def add_task():
    username = session.get('username')
    if not username:
        return redirect('/')

    title = request.form.get('title', '')

    description = request.form.get('description', '')

    due_date = request.form.get('due_date', '')

    priority = request.form.get('priority', '')

    category = request.form.get('category', '') 

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

   #==== get id==== 

    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    user_id = user[0]

    # insert   task====

    cursor.execute(
        "INSERT INTO  tasks(user_id, title, description, status, due_date, priority, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, title, description, "pending", due_date, priority, category, created_at)

     )

    conn.commit()
    conn.close()
    flash("task added successfully")
    return redirect('/dashboard')


  #========  delete task ===============  


@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    username = session.get('username')
    if not username:
        return redirect('/')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id=?",
        (task_id,)
    )    

    conn.commit()
    conn.close()
    flash("task deleted")
    return redirect('/dashboard')

#============== EDITE TASK ============= 

@app.route('/edit_task/<int:task_id>')
def edit_task(task_id):

    username = session.get('username')
    if not username:
        return redirect('/')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id=?",
        (task_id,)
    )

    task = cursor.fetchone()

    conn.close()

    return render_template(
        'task_edit.html',
        task=task
    )

#======update===========

@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):

    username = session.get('username')
    
    if not username:
        return redirect('/')

    new_title = request.form['title']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET title=? WHERE id=?",
        (new_title, task_id)
        
    ) 

    conn.commit()
    conn.close()
    
    flash("task updated")
    return redirect('/dashboard')  

    #======== complete task========= 

@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):

    username = session.get('username')
    if not username:
        return redirect('/')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET status=? WHERE id=?",
        ("completed", task_id)
    ) 

    conn.commit()
    conn.close() 
    
    flash("task completed")
    return redirect('/dashboard')      

        #logout

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')#

# run app
if __name__ =='__main__':
    app.run(debug=True)