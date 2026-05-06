"""
Field Operations API — Flask Application Entry Point
"""
from flask import Flask, jsonify
from flask_cors import CORS
import time

from db.database import init_db
from routes.auth_routes import auth_bp
from routes.task_routes import task_bp
from routes.visit_routes import visit_bp
from routes.dashboard_routes import dashboard_bp
from routes.report_routes import report_bp


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # CORS configuration
    CORS(app, origins=['http://localhost:5173', 'http://localhost:3000'], supports_credentials=True)

    # Initialize database (creates tables)
    init_db()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(task_bp, url_prefix='/api/tasks')
    app.register_blueprint(visit_bp, url_prefix='/api/visits')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(report_bp, url_prefix='/api/reports')

    # Request logging
    @app.before_request
    def log_request_start():
        from flask import request as req
        req._start_time = time.time()

    @app.after_request
    def log_request_end(response):
        from flask import request as req
        if hasattr(req, '_start_time') and req.path.startswith('/api'):
            duration = int((time.time() - req._start_time) * 1000)
            print(f"{req.method} {req.path} {response.status_code} {duration}ms")
        return response

    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'name': 'Field Operations API',
            'version': '1.0.0',
            'status': 'running',
            'docs': 'Use the frontend at http://localhost:5173',
            'health': '/api/health'
        })

    # Health check
    @app.route('/api/health')
    def health():
        from datetime import datetime, timezone
        return jsonify({'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()})

    # Global error handler
    @app.errorhandler(Exception)
    def handle_error(e):
        print(f"Unhandled error: {e}")
        return jsonify({'error': 'Internal server error.'}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    print(f"\n🚀 Field Operations API running on http://localhost:5000")
    print(f"   Health check: http://localhost:5000/api/health\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
