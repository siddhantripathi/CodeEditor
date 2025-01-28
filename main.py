import functions_framework
from app import app

@functions_framework.http
def handler(request):
    return app(request.environ, lambda x, y: []) 