from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import pickle
import mysql.connector



# Flask application
app = Flask(__name__)
app.secret_key = '1123'

# Establish MySQL database connection
dbCon = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  # Replace with your MySQL password
    database="tv_show_recommendations"
)

similarity = pickle.load(open('similarity.pkl','rb'))
shows_dict = pickle.load(open('shows_dictionary.pkl','rb'))
shows_list = pd.DataFrame(shows_dict)

def recommended_shows(showname):
    show_index = shows_list[shows_list['title']==showname].index[0]
    distances = similarity[show_index]
    sorted_shows_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x:x[1])[1:6]
    recommended_shows=[]
    for i in sorted_shows_list:
        recommended_shows.append(shows_list.iloc[i[0]].title)
    return recommended_shows

cursor = dbCon.cursor()


# Home page
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']

        insert_query = "INSERT INTO users (name, username, password) VALUES (%s, %s, %s)"
        insert_data = (name, username, password)

        try:
            cursor.execute(insert_query, insert_data)
            dbCon.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Registration failed. Error: {err}', 'error')

    return render_template('home.html')  # or whatever your home template is

@app.route('/home', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        select_query = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(select_query, (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('user_panel'))
        else:
            flash('Login failed. Check your username and password.', 'error')

    return render_template('home.html')

# User logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('home'))

# User panel
@app.route('/panel', methods=['GET', 'POST'])
def user_panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        title = request.form.get('title')
        genre = request.form.get('genre')
        release_year = request.form.get('release_year')
        episodes = request.form.get('episodes')
        rating = request.form.get('rating')
        country = request.form.get('country')
        language = request.form.get('language')
        description = request.form.get('description')
        cast = request.form.get('cast')

        # Insert the new TV show into the database
        insert_show_query = """
        INSERT INTO tv_shows (title, genre, release_year, episodes, rating,  country, language, description, cast,user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """
        try:
            cursor.execute(insert_show_query, (title, genre, release_year, episodes, rating, country, language, description, cast,user_id))
            dbCon.commit()
            flash('TV Show added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f'Failed to add TV show. Error: {err}', 'danger')

    return render_template('panel.html', shows=shows_list['title'])



# Recommendations page
@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    user_id = session['user_id']

    # Fetch user preferences from the database
    select_preferences_query = "SELECT title FROM tv_shows WHERE user_id=%s"
    cursor.execute(select_preferences_query, (user_id,))
    preferred_shows = [row[0] for row in cursor.fetchall()]

    recommendations_list = [recommended_shows(show) for show in preferred_shows] 

    return render_template('recommendations.html', recommendations=recommendations_list)

# popularity attributes
@app.route('/attributes')
def popularity_attributes():
    return render_template('popularity_attributes.html')

if __name__ == '__main__':
    app.run(debug=True)
