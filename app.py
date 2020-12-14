import os
from dotenv import load_dotenv
import pymongo
import datetime
from bson.objectid import ObjectId
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_pymongo import PyMongo
import bcrypt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

############ TO DO #############

# fix it so contributors can edit and delete their own patterns, but admins can edit and delete everyone's patterns
# add moment.js to clean up date added and date modified appearance in patterns and users
# improve appearance of menu
# ensure each role has access to appropriate menu choices
# fix password so it hashes with bcrypt
# fix print messages in functions so you can see what is happening on the server

################################



## necessary for python-dotenv ##
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

mongo = os.getenv('MONGO')

client = pymongo.MongoClient(mongo)

db = client['pattern_app'] # Mongo collection
users = db['users'] # Mongo document
roles = db['roles'] # Mongo document
categories = db['categories']
patterns = db['patterns']

login = LoginManager()
login.init_app(app)
login.login_view = 'login'

@login.user_loader
def load_user(username):
    u = users.find_one({"email": username})
    if not u:
        return None
    return User(username=u['email'], role=u['role'], id=u['_id'])

class User:
    def __init__(self, id, username, role):
        self._id = id
        self.username = username
        self.role = role

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username

'''
    @staticmethod
    def check_password(password_hash, password):
        return check_password_hash(password_hash, password)
'''

### custom wrap to determine role access  ### 
def roles_required(*role_names):
    def decorator(original_route):
        @wraps(original_route)
        def decorated_route(*args, **kwargs):
            if not current_user.is_authenticated:
                print('The user is not authenticated.')
                return redirect(url_for('login'))
            
            print(current_user.role)
            print(role_names)
            if not current_user.role in role_names:
                print('The user does not have this role.')
                return redirect(url_for('login'))
            else:
                print('The user is in this role.')
                return original_route(*args, **kwargs)
        return decorated_route
    return decorator


@app.route('/', methods=['GET', 'POST'])
def index():
    #show records from the last day
    #today = datetime.datetime.today()
    #timedelta = datetime.timedelta(1) #one day old
    #return render_template('index.html', all_patterns=patterns.find({"date_added": {"$gt": today - timedelta}}))

    # unauthenticated users can see the 10 newest patterns in the database
    return render_template('index.html', all_patterns=patterns.find().sort([("_id", -1)]).limit(10)) #sort newest first, limit to 10 records returned

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        print("inside post")
        form = request.form
        search_term = form['search_string']
        if (search_term != ''):
            return render_template('index.html', all_patterns=patterns.find({'$text': {'$search': search_term}}))
        return url_for("index")
    print("get request")
    return url_for("index")

# unauthenticated users can view the about page
@app.route('/about')
def about():
    return render_template('about.html')

# unauthenticated users can see a message on the registration page
@app.route('/register')
def register():
    return 'Contact the site administrator for an account.'

# unauthenticated users can view the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = users.find_one({"email": request.form['username']})
        if user and user['password'] == request.form['password']:
            user_obj = User(username=user['email'], role=user['role'], id=user['_id'])
            login_user(user_obj)
            next_page = request.args.get('next')

            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
                return redirect(next_page)
            flash("Logged in successfully!", category='success')
            return redirect(request.args.get("next") or url_for("index"))

        flash("Wrong username or password!", category='danger')
    return render_template('login.html')

# authenticated users can logout
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))

# authenticated users can view their account details
@app.route('/my-account/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('user', 'contributor', 'admin')
def my_account(user_id):
    edit_account = users.find_one({'_id': ObjectId(user_id)})
    if edit_account:
        return render_template('my-account.html', user=edit_account)
    flash('User not found.', 'warning')
    return redirect(url_for('index'))

# authenticated users can update their account details
@app.route('/update-myaccount/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('user', 'contributor', 'admin')
def update_myaccount(user_id):
    if request.method == 'POST':
        form = request.form

        password = request.form['password']

        users.update({'_id': ObjectId(user_id)},
            {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'email': form['email'],
            'password': password,
            'role': form['role'],
            'date_added': form['date_added'],
            'date_modified': datetime.datetime.now()
            })
        update_account = users.find_one({'_id': ObjectId(user_id)})
        flash(update_account['email'] + ' has been updated.', 'success')
        return redirect(url_for('index'))
    return redirect(url_for('index'))


##########  Admin functionality -- User management ##########

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_users():
    return render_template('user-admin.html', all_roles=roles.find(), all_users=users.find())

@app.route('/admin/add-user', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_add_user():
    if request.method == 'POST':
        form = request.form
        
        password = request.form['password']
        
        email = users.find_one({"email": request.form['email']})
        if email:
            flash('This email is already registered.', 'warning')
            return 'This email has already been registered.'
        new_user = {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'email': form['email'],
            'password': password,
            'role': form['role'],
            'date_added': datetime.datetime.now(),
            'date_modified': datetime.datetime.now()
        }
        users.insert_one(new_user)
        flash(new_user['email'] + ' user has been added.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('user-admin.html', all_roles=roles.find(), all_users=users.find())

@app.route('/admin/delete-user/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_delete_user(user_id):
    delete_user = users.find_one({'_id': ObjectId(user_id)})
    if delete_user:
        users.delete_one(delete_user)
        flash(delete_user['email'] + ' has been deleted.', 'danger')
        return redirect(url_for('admin_users'))
    flash('User not found.', 'warning')
    return redirect(url_for('admin_users'))

@app.route('/admin/edit-user/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_edit_user(user_id):
    edit_user = users.find_one({'_id': ObjectId(user_id)})
    if edit_user:
        return render_template('edit-user.html', user=edit_user, all_roles=roles.find())
    flash('User not found.', 'warning')
    return redirect(url_for('admin_users'))

@app.route('/admin/update-user/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_update_user(user_id):
    if request.method == 'POST':
        form = request.form

        password = request.form['password']

        users.update({'_id': ObjectId(user_id)},
            {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'email': form['email'],
            'password': password,
            'role': form['role'],
            'date_added': form['date_added'],
            'date_modified': datetime.datetime.now()
            })
        update_user = users.find_one({'_id': ObjectId(user_id)})
        flash(update_user['email'] + ' has been updated.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('user-admin.html', all_roles=roles.find(), all_users=users.find())


##########  Admin Functionality - Pattern Categories ##########

@app.route('/patterns/add-category', methods=['POST'])
@login_required
@roles_required('admin')
def add_category():
    if request.method == 'POST':
        form = request.form
        category = users.find_one({"category_name": request.form['new_category']})
        if category:
            flash('This category is already registerd.', 'warning')
            return url_for('/admin_users')
        new_category = {
            'category_name': form['new_category'],
        }
        categories.insert_one(new_category)
        flash(new_category['category_name'] + ' has been added.', 'success')
        return redirect(url_for('admin_patterns'))
    return render_template('pattern-admin.html', all_categories=categories.find())

@app.route('/patterns/delete_category/<category_id>', methods=['GET'])
@login_required
@roles_required('admin')
def delete_category(category_id):
    delete_category = categories.find_one({'_id': ObjectId(category_id)})
    if delete_category:
        categories.delete_one(delete_category)
        flash(delete_category['category_name'] + ' has been deleted.', 'danger')
        return redirect(url_for('admin_patterns'))
    flash('Pattern not found.', 'warning')
    return redirect(url_for('admin_patterns'))

    

##########  Patterns ##########

# authenticated users can view all the patterns
@app.route('/patterns', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'contributor', 'user')
def view_patterns():
    return render_template('patterns.html', all_patterns=patterns.find())

# authenticated users can print a pattern
@app.route('/patterns/print-pattern/<pattern_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'contributor', 'user')
def print_pattern(pattern_id):
    print_pattern = patterns.find_one({'_id': ObjectId(pattern_id)})
    if print_pattern:
        return render_template('print-pattern.html', pattern=print_pattern)
    flash('Pattern not found.', 'danger')
    return redirect(url_for('view_patterns'))

# administrators users can manage all patterns
@app.route('/patterns/admin', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_patterns():
    return render_template('pattern-admin.html', all_categories=categories.find(), all_patterns=patterns.find())

# administrators and contributors can add new patterns
@app.route('/patterns/add-pattern', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'contributor')
def add_pattern():
    if request.method == 'POST':
        form = request.form
              
        new_pattern = {
            'pattern_name': form['pattern_name'],
            'category': form['category'],
            'pattern_image': form['pattern_image'],
            'ingredients': form.getlist('ingredients'),
            'preparation': form.getlist('steps'),
            'notes': form['notes'],
            'pattern_owner': form['pattern_owner'],
            'added_by': form['added_by'],
            'date_added': datetime.datetime.now(),
            'date_modified': datetime.datetime.now()
        }
        patterns.insert_one(new_pattern)
        flash('New pattern has been added.', 'success')
        return redirect(url_for('view_patterns'))
    return render_template('new-pattern.html', all_categories=categories.find())

@app.route('/create', methods=['POST'])
def create():
    if 'pattern_image' in request.files:
        pattern_image = request.files['pattern_image']
        mongo.save_files(pattern_image.filename, pattern_image)
        monogo.db.users.insert({'username' : request.form.get('username'), 'pattern_image_name' : pattern_image.filename}
        )
    return 'Done!'

@app.route('/file/<filename>')
def file(filename):
    return mongo.send_file(filename)

@app.route('/profile/<username>')
def profile(username):
    user = mongo.db.users.find_one_or_404({'username' : username})
    return f'''
        <h1>{username}</h1>
        <img src="{url_for('file', filename=user['pattern_image_name'])}">
    '''

@app.route('/patterns/edit-pattern/<pattern_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def edit_pattern(pattern_id):
    edit_pattern = patterns.find_one({'_id': ObjectId(pattern_id)})
    if edit_pattern:
        return render_template('edit-pattern.html', pattern=edit_pattern, all_categories=categories.find())
    flash('Pattern not found.', 'danger')
    return redirect(url_for('admin_patterns'))

@app.route('/patterns/update-pattern/<pattern_id>', methods=['POST'])
@login_required
@roles_required('admin')
def update_pattern(pattern_id):
    if request.method == 'POST':
        form = request.form
        patterns.update({'_id': ObjectId(pattern_id)},
            {
            'pattern_name': form['pattern_name'],
            'category': form['category'],
            'pattern_image': form['pattern_image'],
            'ingredients': form.getlist('ingredients'),
            'preparation': form.getlist('steps'),
            'notes': form['notes'],
            'pattern_owner': form['pattern_owner'],
            'added_by': form['added_by'],
            'date_added': form['date_added'],
            'date_modified': datetime.datetime.now()
            })
        update_pattern = patterns.find_one({'_id': ObjectId(pattern_id)})
        flash(update_pattern['pattern_name'] + ' has been updated.', 'success')
        return redirect(url_for('view_patterns'))
    return render_template('edit-pattern.html', all_categories=categories.find())

# administrators can delete patterns
@app.route('/patterns/delete-pattern/<pattern_id>', methods=['POST'])
@login_required
@roles_required('admin')
def delete_pattern(pattern_id):
    delete_pattern = patterns.find_one({'_id': ObjectId(pattern_id)})
    if delete_pattern:
        patterns.delete_one(delete_pattern)
        flash(delete_pattern['pattern_name'] + ' has been deleted.', 'danger')
        return redirect(url_for('view_patterns'))
    flash('pattern not found.', 'warning')
    return redirect(url_for('view_patterns'))


if __name__ == "__main__":
    app.run(debug=True)
