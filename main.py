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
    
    @app.route('/api/void', methods=['GET', 'POST'])
    def void_endpoint():
        return Response("", status=200, mimetype='text/plain')

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
