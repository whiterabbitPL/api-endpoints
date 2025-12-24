from flask import Response, request, jsonify
import redis
import mysql.connector
import uuid
import json
import os


redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True
)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'wordpress')
    )

def register_routes(app):

    @app.route('/api/test', methods=['GET'])
    def test_api():
        html = """
            <div class='api-form-01'>
            <h3>Hello world</h3>
            <p>It is a test API result</p>
            </div>
        """
        return Response(html, mimetype='text/html')
    
    @app.route('/api/void', methods=['GET', 'POST'])
    def void_endpoint():
        return Response("", status=200, mimetype='text/plain')

    @app.route('/api/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            if not data or 'user_id' not in data:
                return jsonify({'error': 'user_id is required'}), 400

            user_id = data['user_id']
            session_uuid = str(uuid.uuid4())

            redis_client.setex(user_id, 3600, session_uuid)
            redis_client.setex(f'{session_uuid}-search-context', 3600, '{}')
            redis_client.setex(f'{session_uuid}-account-details', 3600, '{}')

            return jsonify({'uuid': session_uuid}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/keep-alive', methods=['POST'])
    def keep_alive():
        try:
            data = request.get_json()
            if not data or 'user_id' not in data or 'uuid' not in data:
                return jsonify({'error': 'user_id and uuid are required'}), 400

            user_id = data['user_id']
            session_uuid = data['uuid']

            redis_client.expire(user_id, 3600)
            redis_client.expire(f'{session_uuid}-search-context', 3600)
            redis_client.expire(f'{session_uuid}-account-details', 3600)

            return jsonify({'status': 'ok'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/user-info', methods=['POST'])
    def user_info():
        try:
            data = request.get_json()
            if not data or 'user_id' not in data or 'uuid' not in data:
                return jsonify({'error': 'user_id and uuid are required'}), 400

            user_id = data['user_id']
            session_uuid = data['uuid']

            stored_uuid = redis_client.get(user_id)
            if not stored_uuid or stored_uuid != session_uuid:
                return Response('Session not found', status=404, mimetype='text/plain')

            account_details_json = redis_client.get(f'{session_uuid}-account-details')
            if not account_details_json:
                return Response('Session not found', status=404, mimetype='text/plain')

            account_details = json.loads(account_details_json)

            public_data = {k: v for k, v in account_details.items() if k.startswith('public')}

            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT display_name FROM wp_users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()
            db.close()

            html_data = []

            if user and user['display_name']:
                html_data.append({'display_name': user['display_name']})

            for key, value in public_data.items():
                html_data.append({key: value})

            configuration = {
                "headers": "<h3>{value}</h3>",
                "default": "<p><strong>{key}:</strong> {value}</p>"
            }

            html_output = format_html(
                data=html_data,
                configuration=configuration,
                id='user-info',
                headers=['display_name'],
                pictures=[]
            )

            return Response(html_output, status=200, mimetype='text/html')

        except Exception as e:
            return jsonify({'error': str(e)}), 500

def format_html(data, configuration, id, headers, pictures):
    result = [f'<div class="api-form-{id}">']
    for item in data:
        for key, value in item.items():
            if key in headers and "headers" in configuration:
                result.append(configuration["headers"].format(key=key, value=value))
            elif key in pictures and "pictures" in configuration:
                result.append(configuration["pictures"].format(key=key, value=value))
            elif "default" in configuration:
                result.append(configuration["default"].format(key=key, value=value))
    result.append('</div>')
    return '\n'.join(result)
