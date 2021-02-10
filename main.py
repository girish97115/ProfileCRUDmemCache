from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource, request
from flask import jsonify
from marshmallow_sqlalchemy import ModelSchema
from pymemcache.client import base
import ast

client = base.Client(('localhost', 11000))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
api = Api(app)

# mem_cache
# client.set('some_key', 'some value')
# client.get('some_key')
# client.delete('some_key')


class Profile(db.Model):
    __tablename__ = 'profile'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250))
    age = db.Column(db.Integer)
    company = db.Column(db.String(250))
    branch = db.Column(db.String(250))
    creation_date = db.Column(
        db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)

    def __init__(self, name, age, company, branch):
        self.name = name
        self.age = age
        self.company = company
        self.branch = branch


class ProfileSchema(ModelSchema):
    class Meta:
        model = Profile


profile_schema = ProfileSchema()
profiles_schema = ProfileSchema(many=True)


class PostListResource(Resource):
    def get(self):
        notes = Profile.query.all()
        return profiles_schema.dump(notes)

    def post(self):
        name = request.json['name']
        age = request.json['age']
        company = request.json['company']
        branch = request.json['branch']
        profile = Profile(name, age, company, branch)
        db.session.add(profile)
        db.session.commit()
        return profile_schema.dump(profile)


class PostResource(Resource):
    def get(self, profile_id):
        if client.get(str(profile_id)) is None:
            profile = Profile.query.get_or_404(profile_id)
            profile = {'id': profile.id, 'name': profile.name, 'age': profile.age,
                       'company': profile.company, 'branch': profile.branch}
            client.set(str(profile_id), profile)
            print("from_db")

        else:
            profile = ast.literal_eval(
                client.get(str(profile_id)).decode('ascii'))
            print("from_memcache")
        return jsonify(profile)

    def put(self, profile_id):
        note = Profile.query.get_or_404(profile_id)

        if 'name' in request.json:
            note.name = request.json['name']
        if 'age' in request.json:
            note.age = request.json['age']
        if 'company' in request.json:
            note.company = request.json['company']
        if 'branch' in request.json:
            note.branch = request.json['branch']

        db.session.commit()
        profile = Profile.query.get_or_404(profile_id)
        profile = {'id': profile.id, 'name': profile.name, 'age': profile.age,
                   'company': profile.company, 'branch': profile.branch}
        client.set(str(profile_id), profile)
        return profile_schema.dump(note)

    def delete(self, profile_id):
        note = Profile.query.get_or_404(profile_id)
        client.delete(str(profile_id))
        db.session.delete(note)
        db.session.commit()
        return '', 204


api.add_resource(PostListResource, '/profiles')
api.add_resource(PostResource, '/profile/<int:profile_id>')


if __name__ == '__main__':
    app.run(debug=True)
