import os
import uuid
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Post, Like, Comment, Category
from sqlalchemy import func
from forms import LoginForm, RegistrationForm, PostForm, CommentForm, EditProfileForm, SearchForm

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    
    query = Post.query.order_by(Post.created_at.desc())
    posts = query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Invalid username or password')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_post():
    form = PostForm()
    if form.validate_on_submit():
        # Handle file upload
        file = form.image.data
        if file:
            # Generate unique filename
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save and resize image
            image = Image.open(file.stream)
            # Resize image to max 1080px width while maintaining aspect ratio
            if image.width > 1080:
                ratio = 1080 / image.width
                new_height = int(image.height * ratio)
                image = image.resize((1080, new_height), Image.Resampling.LANCZOS)
            
            image.save(filepath, optimize=True, quality=85)
            
            # Create post
            post = Post()
            post.caption = form.caption.data
            post.image_filename = filename
            post.category_id = None  # Categories are not visible to regular users
            post.hashtags = form.hashtags.data
            post.user_id = current_user.id
            db.session.add(post)
            db.session.commit()
            flash('Photo shared successfully!')
            return redirect(url_for('index'))
    
    return render_template('upload.html', form=form)

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('profile.html', user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username, current_user.email)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        
        # Handle profile image upload
        if form.profile_image.data:
            # Generate unique filename
            filename = secure_filename(form.profile_image.data.filename)
            filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Resize and save image
            image = Image.open(form.profile_image.data)
            # Make it square and smaller for profile pictures
            size = min(image.size)
            image = image.crop((
                (image.width - size) // 2,
                (image.height - size) // 2,
                (image.width + size) // 2,
                (image.height + size) // 2
            ))
            image = image.resize((200, 200), Image.Resampling.LANCZOS)
            image.save(filepath, optimize=True, quality=85)
            
            # Delete old profile image if exists
            if current_user.profile_image:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_image)
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            current_user.profile_image = filename
        
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('profile', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    return render_template('edit_profile.html', form=form)

@app.route('/like/<int:post_id>')
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if like:
        # Unlike the post
        db.session.delete(like)
        db.session.commit()
        flash('Post unliked!')
    else:
        # Check if user has reached daily like limit
        if not current_user.can_like_more():
            flash(f'You have reached your daily limit of {current_user.daily_likes_limit} likes. Try again tomorrow!')
            return redirect(request.referrer or url_for('index'))
        
        # Like the post
        like = Like()
        like.user_id = current_user.id
        like.post_id = post_id
        db.session.add(like)
        db.session.commit()
        flash('Post liked!')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment()
        comment.content = form.content.data
        comment.user_id = current_user.id
        comment.post_id = post_id
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/search')
def search():
    form = SearchForm()
    users = []
    posts = []
    
    if request.args.get('query'):
        query = request.args.get('query')
        # Search users
        users = User.query.filter(User.username.contains(query)).limit(10).all()
        # Search posts by caption or hashtags
        posts = Post.query.filter(
            db.or_(Post.caption.contains(query), Post.hashtags.contains(query))
        ).order_by(Post.created_at.desc()).limit(20).all()
    
    return render_template('search.html', form=form, users=users, posts=posts, query=request.args.get('query', ''))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = post.comments.order_by(Comment.created_at.desc()).all()
    comment_form = CommentForm()
    return render_template('view_post.html', post=post, comments=comments, comment_form=comment_form)

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    # Get top posts by likes for ranking
    top_posts = db.session.query(Post, func.count(Like.id).label('like_count')).\
        outerjoin(Like).\
        group_by(Post.id).\
        order_by(func.count(Like.id).desc()).\
        limit(10).all()
    
    categories = Category.query.all()
    total_users = User.query.count()
    total_posts = Post.query.count()
    
    return render_template('admin/dashboard.html', 
                         top_posts=top_posts, 
                         categories=categories,
                         total_users=total_users,
                         total_posts=total_posts)

@app.route('/admin/categories')
@login_required
def admin_categories():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/create', methods=['GET', 'POST'])
@login_required
def admin_create_category():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if name:
            # Check if category already exists
            existing = Category.query.filter_by(name=name).first()
            if existing:
                flash('Category already exists!')
            else:
                category = Category()
                category.name = name
                category.description = description
                category.created_by = current_user.id
                db.session.add(category)
                db.session.commit()
                flash(f'Category "{name}" created successfully!')
                return redirect(url_for('admin_categories'))
        else:
            flash('Category name is required!')
    
    return render_template('admin/create_category.html')

@app.route('/admin/categories/<int:category_id>/toggle')
@login_required
def admin_toggle_category(category_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    category = Category.query.get_or_404(category_id)
    category.is_active = not category.is_active
    db.session.commit()
    
    status = "activated" if category.is_active else "deactivated"
    flash(f'Category "{category.name}" has been {status}.')
    return redirect(url_for('admin_categories'))

@app.route('/admin/ranking')
@login_required
def admin_ranking():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    # Get all posts ranked by likes
    posts_with_likes = db.session.query(Post, func.count(Like.id).label('like_count')).\
        outerjoin(Like).\
        group_by(Post.id).\
        order_by(func.count(Like.id).desc()).\
        all()
    
    return render_template('admin/ranking.html', posts_with_likes=posts_with_likes)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    # Get all users with their stats
    users = db.session.query(
        User, 
        func.count(Post.id).label('post_count'),
        func.count(Like.id).label('likes_given')
    ).outerjoin(Post, User.id == Post.user_id)\
     .outerjoin(Like, User.id == Like.user_id)\
     .group_by(User.id)\
     .order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting admin accounts
    if user.is_admin:
        flash('Cannot delete admin accounts.')
        return redirect(url_for('admin_users'))
    
    # Delete all user's posts and associated files
    for post in user.posts:
        # Delete associated likes and comments
        Like.query.filter_by(post_id=post.id).delete()
        Comment.query.filter_by(post_id=post.id).delete()
        
        # Delete the image file
        if post.image_filename:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
    
    # Delete profile image if exists
    if user.profile_image:
        profile_path = os.path.join(app.config['UPLOAD_FOLDER'], user.profile_image)
        if os.path.exists(profile_path):
            os.remove(profile_path)
    
    # Delete all user's likes and comments
    Like.query.filter_by(user_id=user.id).delete()
    Comment.query.filter_by(user_id=user.id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} has been deleted successfully.')
    return redirect(url_for('admin_users'))

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if user can delete this post (owner or admin)
    if current_user.id != post.user_id and not current_user.is_admin:
        flash('You cannot delete this post.')
        return redirect(url_for('index'))
    
    # Delete associated likes and comments first
    Like.query.filter_by(post_id=post.id).delete()
    Comment.query.filter_by(post_id=post.id).delete()
    
    # Delete the image file
    if post.image_filename:
        image_path = os.path.join(app.root_path, 'static', 'uploads', post.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Delete the post
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted successfully.')
    return redirect(url_for('index'))

