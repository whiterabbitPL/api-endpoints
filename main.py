from flask import Response

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

def format_html():
    pass
