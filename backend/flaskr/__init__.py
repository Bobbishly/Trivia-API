import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    present_questions = questions[start:end]

    return present_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.type).all()

        if len(categories) == 0:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'categories': {category.id: category.type for category in categories}
            })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/questions')
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        present_questions = paginate(request, selection)

        categories = Category.query.order_by(Category.type).all()

        if len(present_questions) == 0:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'questions': present_questions,
                'total_questions': len(selection),
                'categories': {category.id: category.type for category in categories},
                'current_category': None
            })


    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route("/questions/<question_id>", methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            question.delete()
            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route("/questions", methods=['POST'])
    def add_new_question():
        body = request.get_json()

        latest_question = body.get('question')
        latest_answer = body.get('answer')
        latest_category = body.get('category')
        latest_difficulty = body.get('difficulty')

        try:
            question = Question(
                question=latest_question, 
                answer=latest_answer, 
                category=latest_category, 
                difficulty=latest_difficulty
                )

            question.insert()

            return jsonify({
                'success': True,
                'created': question.id
            })

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route('/search', methods=['POST'])
    def get_questions_from_search():

        body = request.get_json()
        search_qustions = body.get('searchTerm', None)

        try:
            questions = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search_qustions)))

            questions_formatted = [
              question.format() for question in questions
            ]

            return jsonify({
              'success': True,
              'questions': questions_formatted,
              'total_questions': len(questions.all()),
              'current_category': None,
            })

        except Exception:
            abort(404)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):

        try:
            category_questions = Question.query.filter(
                Question.category == str(category_id)
            ).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in category_questions],
                'total_questions': len(category_questions),
                'current_category': category_id
            })
        except:
            abort(404)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=['POST'])
    def start_quiz():

        try:
            body = request.get_json()

            quiz_category = body.get('quiz_category', None)
            previous_questions = body.get('previous_questions', None)

            if quiz_category['type'] == 'click':
                accessible_questions = Question.query.filter(Question.id.notin_((previous_questions))).all()
            else:
                accessible_questions = Question.query.filter_by(category=quiz_category['id']).filter(Question.id.notin_((previous_questions))).all()

            latest_question = accessible_questions[random.randrange(
                0, len(accessible_questions))].format() if len(accessible_questions) > 0 else None

            return jsonify({
                'success': True,
                'question': latest_question
            })
        except:
            abort(422)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "not found"
        }), 404

    @app.errorhandler(422)
    def can_not_process_request(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "can't procss your request"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "malformed request syntax"
        }), 400

    return app

