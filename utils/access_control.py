from functools import wraps
from flask import session, redirect, url_for, flash, request

def login_required(f):
    """Decorator to require login for accessing a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for accessing a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        
        if session.get('role') != 'admin':
            flash('Admin access required for this page.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    """Decorator to require user role or higher for accessing a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        
        if session.get('role') not in ['user', 'admin']:
            flash('User access required for this page.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_user_permissions(role):
    """Get permissions for a given role"""
    permissions = {
        'admin': [
            'upload_images',
            'view_results',
            'flag_predictions',
            'view_admin_dashboard',
            'manage_models',
            'view_logs',
            'retrain_models',
            'manage_users'
        ],
        'user': [
            'upload_images',
            'view_results',
            'flag_predictions'
        ]
    }
    
    return permissions.get(role, [])

def has_permission(permission):
    """Check if current user has a specific permission"""
    if 'role' not in session:
        return False
    
    user_permissions = get_user_permissions(session['role'])
    return permission in user_permissions
