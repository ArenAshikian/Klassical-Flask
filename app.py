from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from webforms import LoginForm, PostForm, UserForm, PasswordForm, NamerForm
from sqlalchemy import MetaData
from webforms import CommentForm

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


#Flask instance

app = Flask(__name__)
#add database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
#secret key
app.config['SECRET_KEY'] = "KLASSICLE"

#intialize database
#updated/added to fix error since SQLite3 doesn't support ALTER table
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db, render_as_batch=True)

app.app_context().push()

#Flask_Login things
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

#Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            #check hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Logged In Successfully.")
                return redirect(url_for('dashboard'))
            else:
                flash("Incorrect Password, Try again.")
        else:
            flash("User Credentials Do Not Exist, Try Again.")

    return render_template('login.html', form=form)

#Logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('Logged Out Successfully.')
    return redirect(url_for('login'))


#Create Dashbooard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("dashboard.html", form=form, name_to_update=name_to_update)
        except:
            db.session.commit()
            flash("User Failed to Update!")
            return render_template("dashboard.html", form=form, name_to_update=name_to_update)
    else:
        return render_template("dashboard.html", form=form, name_to_update=name_to_update, id=id)

    return render_template('dashboard.html')



@app.route('/posts')
def posts():
    # Get the posts from the database
    posts = Posts.query.order_by(Posts.date_posted).all()

    # Create a comment form
    form = CommentForm()  # You need to create the CommentForm

    # Query comments for each post and store them in a dictionary
    comments = {}
    for post in posts:
        comments[post.id] = Comment.query.filter_by(post_id=post.id).all()

    return render_template("posts.html", posts=posts, form=form, comments=comments)



#individual post page 
@app.route('/posts/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)

#delete posts 
@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id:
        try:
            #updating the db
            db.session.delete(post_to_delete)
            db.session.commit()

            #message
            flash("Post Deleted Successfully!")

            #grab all posts in db
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts=posts)
        
        except:
            #Error message
            flash("Error, Post was not deleted!")

            #grab all posts in db
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts=posts)
    else:
        #message
        flash("You can't delete this post!")

        #grab all posts in db
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)




#edit post page
@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data

        #update db
        db.session.add(post)
        db.session.commit()
        flash("Post Updated Successfully!")
        return redirect(url_for('post', id=post.id))
    
    if current_user.id == post.poster_id:
        form.title.data = post.title 
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    else:
        flash("You can't edit this post!")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)

#comments    
@app.route('/posts/comment/<int:id>', methods=['POST'])
@login_required
def add_comment(id):
    form = CommentForm()
    if form.validate_on_submit():
        post = Posts.query.get_or_404(id)
        comment = Comment(text=form.text.data, user_id=current_user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        flash("Comment added successfully!")
        return redirect(url_for('post', id=post.id))
    else:
        flash("Error adding comment.")
    return redirect(url_for('post', id=id))



#add post page
@app.route('/add-post', methods = ['GET', 'POST'])
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data, content=form.content.data, poster_id=poster)
        # clear form
        form.title.data = ''
        form.content.data = ''

        #add post data to db
        db.session.add(post)
        db.session.commit()

        #success message
        flash("Post Submitted Successfully!")

        #redirect to the webpage
    return render_template("add_post.html", form=form)

#JSON
@app.route('/date')
def get_current_date():
    favorite_pizza = {
        ""
    }
    return {"Date": date.today()}


@app.route('/')

#def index():
#   return "<h1>Hello world!</h1>"

def index():
   first_name = "Dilhan"

   favorite_pizza = ["pepperoni", "Cheese", "Mushrooms", 41]
   return render_template("index.html", first_name=first_name, favorite_pizza=favorite_pizza)


#localhost:5000/user/Dilhan
@app.route('/user/<name>')

def user(name):
   return render_template("user.html", user_name=name)

#Invalid URL
#Error Handling Code
@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400

@app.errorhandler(401)
def unauthorized(e):
    return render_template('401.html'), 401

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(413)
def content_too_large(e):
    return render_template('413.html'), 413

@app.errorhandler(415)
def unsupported_media(e):
    return render_template('415.html'), 415

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Create pw test page
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
   email = None
   password = None
   pw_to_check = None
   passed = None
   form = PasswordForm()

   # validate form
   if form.validate_on_submit():
       email = form.email.data
       password = form.password_hash.data
       form.email.data = ''
       form.password_hash.data = ''
       #look up user by email address
       pw_to_check = Users.query.filter_by(email=email).first()

       #check hashed pw
       passed = check_password_hash(pw_to_check.password_hash, password)


   return render_template("test_pw.html", email = email, password = password, 
                                          pw_to_check = pw_to_check, 
                                          passed = passed, 
                                          form = form)


# Create name page
@app.route('/name', methods=['GET', 'POST'])
def name():
   name = None
   form = NamerForm()
   # validate form
   if form.validate_on_submit():
       name = form.name.data
       form.name.data = ''
   return render_template("name.html", name = name, form = form)

#add user
@app.route('/user/add', methods = ['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            #hash password
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = Users(name=form.name.data, email=form.email.data, password_hash=hashed_pw)
            #csuf student validation
            if '@csu.fullerton.edu' not in user.email:
                flash("You are not a CSUF Student!")
                return render_template("add_user.html", form=form, name=name)
        
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.email.data = ''
        form.password_hash = ''
        flash("User Added Successfully!")
    our_users = Users.query.order_by(Users.date_added)

    return render_template("add_user.html", form=form, name=name, our_users=our_users)

#update user info
@app.route('/update/<int:id>', methods = ['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("update.html", form=form, name_to_update=name_to_update)
        except:
            db.session.commit()
            flash("User Failed to Update!")
            return render_template("update.html", form=form, name_to_update=name_to_update)
    else:
        return render_template("update.html", form=form, name_to_update=name_to_update, id=id)

@app.route('/delete/<int:id>')
def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    name = None
    form = UserForm()

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully!")
        our_users = Users.query.order_by(Users.date_added)
        return render_template("add_user.html", form=form, name=name, our_users=our_users)
    
    except:
        flash("User was not deleted!")
        return render_template("add_user.html", form=form, name=name, our_users=our_users)
    
# post model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Add a relationship to the Comment model
    comments = db.relationship('Comment', backref='post', lazy='dynamic')


#create model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    #password code
    password_hash = db.Column(db.String(128))
    #user can have many posts
    posts = db.relationship('Posts', backref='poster')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute!')
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
         
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
# Define the Comment model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Define a relationship to the Users model
    user = db.relationship('Users', backref='comments')


    def __init__(self, text, user_id, post_id):
        self.text = text
        self.user_id = user_id
        self.post_id = post_id
    
    @app.route('/posts/edit-comment/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_comment(id):
        comment_to_edit = Comment.query.get_or_404(id)

        # Ensure only the author of the comment can edit it
        if current_user.id == comment_to_edit.user_id:
            form = CommentForm()

            if form.validate_on_submit():
                comment_to_edit.text = form.text.data
                db.session.commit()
                flash("Comment Updated Successfully!")
                return redirect(url_for('post', id=comment_to_edit.post_id))
            
            form.text.data = comment_to_edit.text
            return render_template('edit_comment.html', form=form, comment_to_edit=comment_to_edit)
        else:
            flash("You can't edit this comment!")
            return redirect(url_for('post', id=comment_to_edit.post_id))


    @app.route('/posts/delete-comment/<int:id>')
    @login_required
    def delete_comment(id):
        comment_to_delete = Comment.query.get_or_404(id)
        post_id = comment_to_delete.post_id

        # Ensure only the author of the comment can delete it
        if current_user.id == comment_to_delete.user_id:
            db.session.delete(comment_to_delete)
            db.session.commit()
            flash("Comment Deleted Successfully!")
        else:
            flash("You can't delete this comment!")

        return redirect(url_for('post', id=post_id))

    
    
    # Create a string representation of the comment
    def __repr__(self):
        return f'<Comment {self.id}>'

