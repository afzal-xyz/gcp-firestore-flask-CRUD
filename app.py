# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Cloud Endpoints sample application.

Demonstrates how to create a simple REST API as well as how to secure it using
Google Cloud Endpoints.
"""
from flask import Flask, request
from flask_restful import Resource, Api, abort, reqparse
from google.cloud import firestore

# Project ID is determined by the GCLOUD_PROJECT environment variable
db = firestore.Client()
app = Flask(__name__)
api = Api(app)


def abort_if_task_doesnt_exist(task_id):
    tasks_ref = db.collection('Tasks')
    ref = tasks_ref.where(u'taskid', u'==', task_id)
    if not ref:
        abort(404, message="Task {} doesn't exist".format(task_id))


parser = reqparse.RequestParser()
parser.add_argument('name')
parser.add_argument('description')
parser.add_argument('priority')


class Task(object):
    def __init__(self, name, description, priority='low'):
        self.name = name
        self.description = description
        self.priority = priority

    def to_dict(self):
        task = {
            'name': self.name,
            'description': self.description,
            'priority': self.priority
        }
        return task

    def __repr__(self):
        return 'Task(name={}, description={}, priority={})'.format(self.name, self.description, self.priority)


class TaskList(Resource):
    def get(self):
        tasks_ref = db.collection('Tasks')
        docs = tasks_ref.stream()
        tasks = {}
        for doc in docs:
            tasks[doc.id]= doc.to_dict()
        return tasks

    def post(self):
        args = parser.parse_args()
        task = Task(name=args['name'], description=args['description'], priority=args['priority'])
        db.collection('Tasks').add(task.to_dict())
        return task.to_dict(), 201


class TaskListById(Resource):
    def get(self, taskid):
        doc_ref = db.collection('Tasks').document(taskid)
        if doc_ref:
            return doc_ref.get().to_dict()
        return None

    def put(self, taskid):
        args = parser.parse_args()
        tasks_ref = db.collection('Tasks')
        tasks_ref.document(taskid).update({"name": args['name'], "description": args['description'], "priority": args['priority']})
        return True, 201

    def delete(self, taskid):
        tasks_ref = db.collection('Tasks')
        tasks_ref.document(taskid).delete()
        return True, 201


api.add_resource(TaskList, '/tasks')
api.add_resource(TaskListById, '/tasks/<taskid>')

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
