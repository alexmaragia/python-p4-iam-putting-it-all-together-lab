#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        try:
            data = request.get_json()
            
            # Check if required username is present
            if not data.get('username'):
                return {'errors': ['Username is required']}, 422
                
            # Create new user
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            
            # Set password if provided
            if data.get('password'):
                user.password_hash = data['password']
            else:
                return {'errors': ['Password is required']}, 422

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 201

        except ValueError as e:
            return {'errors': [str(e)]}, 422
            
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username must be unique']}, 422
            
        except Exception as e:
            db.session.rollback()
            return {'errors': ['An error occurred while creating the user']}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401
            
        user = User.query.filter_by(id=user_id).first()
        return {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }

class Login(Resource):
    def post(self):
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.authenticate(password):
                session['user_id'] = user.id
                return {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }
            
            return {'errors': ['Invalid username or password']}, 401
        
        except Exception:
            return {'errors': ['An error occurred during login']}, 401

class Logout(Resource):
    def delete(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401
            
        session.clear()
        return {}, 204

class RecipeIndex(Resource):
    def get(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401

        recipes = Recipe.query.all()
        return [{
            'id': recipe.id,
            'title': recipe.title,
            'instructions': recipe.instructions,
            'minutes_to_complete': recipe.minutes_to_complete,
            'user': {
                'id': recipe.user.id,
                'username': recipe.user.username
            }
        } for recipe in recipes], 200

    def post(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401

        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('title'):
                return {'errors': ['Title is required']}, 422
                
            if not data.get('instructions'):
                return {'errors': ['Instructions are required']}, 422

            recipe = Recipe(
                title=data['title'],
                instructions=data['instructions'],
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=session['user_id']
            )
            
            db.session.add(recipe)
            db.session.commit()

            return {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user': {
                    'id': recipe.user.id,
                    'username': recipe.user.username
                }
            }, 201

        except ValueError as e:
            return {'errors': [str(e)]}, 422
            
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Validation errors']}, 422
            
        except Exception as e:
            db.session.rollback()
            return {'errors': ['An error occurred while creating the recipe']}, 422

# Add resources to API
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)