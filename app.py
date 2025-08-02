from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import uuid

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///civictrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

# Create uploads directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='reported')
    votes = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    reporter_id = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'location': self.location,
            'status': self.status,
            'votes': self.votes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'latitude': self.latitude,
            'longitude': self.longitude
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False)
    issues_reported = db.Column(db.Integer, default=0)
    votes_cast = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

# HTML Template (Complete Frontend)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CivicTrack - Report Local Issues</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .logo {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .tagline {
            font-size: 1.2rem;
            opacity: 0.9;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }

        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }

        .issues-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .issue-item {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .issue-item:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }

        .issue-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }

        .issue-meta {
            font-size: 0.9rem;
            color: #666;
            display: flex;
            justify-content: space-between;
        }

        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .status-reported { background: #fff3cd; color: #856404; }
        .status-progress { background: #d4edda; color: #155724; }
        .status-resolved { background: #d1ecf1; color: #0c5460; }

        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #666;
            font-size: 0.9rem;
        }

        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }

        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }

        .loading {
            opacity: 0.6;
            pointer-events: none;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .stats {
                grid-template-columns: 1fr;
            }
        }

        .pulse {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo pulse">🏛️ CivicTrack</div>
            <div class="tagline">Real-time Civic Issue Reporting & Tracking</div>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="totalIssues">Loading...</div>
                <div class="stat-label">Total Reports</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="resolvedIssues">Loading...</div>
                <div class="stat-label">Resolved</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="activeUsers">Loading...</div>
                <div class="stat-label">Active Citizens</div>
            </div>
        </div>

        <div class="main-content">
            <div class="card">
                <h2>🚨 Report New Issue</h2>
                <div class="success-message" id="successMessage"></div>
                <div class="error-message" id="errorMessage"></div>
                
                <form id="issueForm">
                    <div class="form-group">
                        <label for="issueTitle">Issue Title</label>
                        <input type="text" id="issueTitle" placeholder="Brief description" required>
                    </div>

                    <div class="form-group">
                        <label for="issueCategory">Category</label>
                        <select id="issueCategory" required>
                            <option value="">Select Category</option>
                            <option value="roads">🛣️ Roads (potholes, obstructions)</option>
                            <option value="lighting">💡 Lighting (broken lights)</option>
                            <option value="water">💧 Water Supply (leaks, pressure)</option>
                            <option value="cleanliness">🗑️ Cleanliness (garbage, bins)</option>
                            <option value="safety">⚠️ Public Safety (manholes, wiring)</option>
                            <option value="obstructions">🚫 Obstructions (fallen trees)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="issueDescription">Description</label>
                        <textarea id="issueDescription" rows="4" placeholder="Detailed description" required></textarea>
                    </div>

                    <div class="form-group">
                        <label for="issueLocation">Location</label>
                        <input type="text" id="issueLocation" placeholder="Street address or landmark" required>
                    </div>

                    <button type="submit" class="btn" id="submitBtn">Submit Report</button>
                </form>
            </div>

            <div class="card">
                <h2>📍 Live Issues Feed</h2>
                <div class="issues-list" id="issuesList">
                    <div style="text-align: center; padding: 20px; color: #666;">
                        Loading issues...
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '';
        
        // Category icons
        const categoryIcons = {
            roads: "🛣️",
            lighting: "💡",
            water: "💧",
            cleanliness: "🗑️",
            safety: "⚠️",
            obstructions: "🚫"
        };

        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadIssues();
            loadStats();
            
            // Refresh data every 30 seconds
            setInterval(() => {
                loadIssues();
                loadStats();
            }, 30000);
        });

        // Handle form submission
        document.getElementById('issueForm').addEventListener('submit', function(e) {
            e.preventDefault();
            submitIssue();
        });

        async function submitIssue() {
            const form = document.getElementById('issueForm');
            const submitBtn = document.getElementById('submitBtn');
            const successMsg = document.getElementById('successMessage');
            const errorMsg = document.getElementById('errorMessage');
            
            // Hide previous messages
            successMsg.style.display = 'none';
            errorMsg.style.display = 'none';
            
            // Show loading state
            submitBtn.textContent = 'Submitting...';
            submitBtn.disabled = true;
            
            const issueData = {
                title: document.getElementById('issueTitle').value,
                category: document.getElementById('issueCategory').value,
                description: document.getElementById('issueDescription').value,
                location: document.getElementById('issueLocation').value,
                reporter_id: 'user_' + Math.random().toString(36).substr(2, 9)
            };
            
            try {
                const response = await fetch('/api/issues', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(issueData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    successMsg.textContent = '✅ Issue reported successfully! ID: ' + result.id;
                    successMsg.style.display = 'block';
                    form.reset();
                    loadIssues();
                    loadStats();
                } else {
                    throw new Error('Failed to submit issue');
                }
            } catch (error) {
                errorMsg.textContent = '❌ Error submitting issue. Please try again.';
                errorMsg.style.display = 'block';
            } finally {
                submitBtn.textContent = 'Submit Report';
                submitBtn.disabled = false;
            }
        }

        async function loadIssues() {
            try {
                const response = await fetch('/api/issues');
                const issues = await response.json();
                displayIssues(issues);
            } catch (error) {
                console.error('Error loading issues:', error);
            }
        }

        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('totalIssues').textContent = stats.total_issues;
                document.getElementById('resolvedIssues').textContent = stats.resolved_issues;
                document.getElementById('activeUsers').textContent = stats.active_users;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        function displayIssues(issues) {
            const issuesList = document.getElementById('issuesList');
            
            if (issues.length === 0) {
                issuesList.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">No issues reported yet.</div>';
                return;
            }
            
            issuesList.innerHTML = '';
            
            issues.slice(0, 10).forEach(issue => {
                const issueElement = createIssueElement(issue);
                issuesList.appendChild(issueElement);
            });
        }

        function createIssueElement(issue) {
            const issueDiv = document.createElement('div');
            issueDiv.className = 'issue-item fade-in';
            issueDiv.onclick = () => voteForIssue(issue.id);
            
            const statusClass = `status-${issue.status}`;
            const statusText = issue.status.charAt(0).toUpperCase() + issue.status.slice(1);
            const icon = categoryIcons[issue.category] || "📋";
            const timeAgo = getTimeAgo(new Date(issue.created_at));
            
            issueDiv.innerHTML = `
                <div class="issue-title">${icon} ${issue.title}</div>
                <div style="margin: 8px 0; color: #666; font-size: 0.9rem;">
                    ${issue.description}
                </div>
                <div class="issue-meta">
                    <div>📍 ${issue.location} • ${timeAgo}</div>
                    <div>
                        <span class="status-badge ${statusClass}">${statusText}</span>
                        <span style="margin-left: 10px;">👍 ${issue.votes}</span>
                    </div>
                </div>
            `;
            
            return issueDiv;
        }

        async function voteForIssue(issueId) {
            try {
                const response = await fetch(`/api/issues/${issueId}/vote`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ user_id: 'user_' + Math.random().toString(36).substr(2, 9) })
                });
                
                if (response.ok) {
                    loadIssues();
                    loadStats();
                }
            } catch (error) {
                console.error('Error voting:', error);
            }
        }

        function getTimeAgo(date) {
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);
            
            if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
            if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
            if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
            return `${Math.floor(diffInSeconds / 86400)}d ago`;
        }
    </script>
</body>
</html>
'''

# Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/issues', methods=['GET'])
def get_issues():
    issues = Issue.query.order_by(Issue.created_at.desc()).all()
    return jsonify([issue.to_dict() for issue in issues])

@app.route('/api/issues', methods=['POST'])
def create_issue():
    try:
        data = request.get_json()
        
        # Input validation
        required_fields = ['title', 'description', 'category', 'location']
        for field in required_fields:
            if not data.get(field) or not data.get(field).strip():
                return jsonify({'error': f'{field} is required'}), 400
        
        # Sanitize inputs
        title = data['title'].strip()[:200]
        description = data['description'].strip()[:1000]
        category = data['category'].strip()
        location = data['location'].strip()[:200]
        
        # Validate category
        valid_categories = ['roads', 'lighting', 'water', 'cleanliness', 'safety', 'obstructions']
        if category not in valid_categories:
            return jsonify({'error': 'Invalid category'}), 400
        
        issue = Issue(
            title=title,
            description=description,
            category=category,
            location=location,
            reporter_id=data.get('reporter_id', 'anonymous')
        )
        
        db.session.add(issue)
        db.session.commit()
        
        return jsonify({
            'message': 'Issue created successfully',
            'id': issue.id,
            'issue': issue.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create issue'}), 500

@app.route('/api/issues/<int:issue_id>/vote', methods=['POST'])
def vote_issue(issue_id):
    try:
        issue = Issue.query.get_or_404(issue_id)
        issue.votes += 1
        db.session.commit()
        
        return jsonify({
            'message': 'Vote recorded',
            'votes': issue.votes
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to record vote'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_issues = Issue.query.count()
    resolved_issues = Issue.query.filter_by(status='resolved').count()
    active_users = db.session.query(Issue.reporter_id).distinct().count()
    
    return jsonify({
        'total_issues': total_issues,
        'resolved_issues': resolved_issues,
        'active_users': max(active_users, 1)
    })

@app.route('/api/issues/<int:issue_id>/status', methods=['PUT'])
def update_status(issue_id):
    try:
        data = request.get_json()
        issue = Issue.query.get_or_404(issue_id)
        
        valid_statuses = ['reported', 'progress', 'resolved']
        new_status = data.get('status')
        
        if new_status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        issue.status = new_status
        issue.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Status updated',
            'issue': issue.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update status'}), 500

 # Initialize database
with app.app_context():
    db.create_all()
    
    # Add sample data if database is empty
    if Issue.query.count() == 0:
        sample_issues = [
            Issue(
                title="Large pothole on Main Street",
                description="Deep pothole causing traffic issues and vehicle damage",
                category="roads",
                location="Main Street near City Hall",
                status="reported",
                votes=12
            ),
            Issue(
                title="Broken street light",
                description="Street light not working for 3 days, creating safety concerns",
                category="lighting",
                location="Park Avenue & 5th Street",
                status="progress",
                votes=8
            ),
            Issue(
                title="Water leak on sidewalk",
                description="Continuous water leak creating puddles and wasting water",
                category="water",
                location="Oak Street",
                status="resolved",
                votes=15
            )
        ]
        
        for issue in sample_issues:
            db.session.add(issue)
        
        db.session.commit()
    
    # Add sample data if database is empty
    if Issue.query.count() == 0:
        sample_issues = [
            Issue(
                title="Large pothole on Main Street",
                description="Deep pothole causing traffic issues and vehicle damage",
                category="roads",
                location="Main Street near City Hall",
                status="reported",
                votes=12
            ),
            Issue(
                title="Broken street light",
                description="Street light not working for 3 days, creating safety concerns",
                category="lighting",
                location="Park Avenue & 5th Street",
                status="progress",
                votes=8
            ),
            Issue(
                title="Water leak on sidewalk",
                description="Continuous water leak creating puddles and wasting water",
                category="water",
                location="Oak Street",
                status="resolved",
                votes=15
            )
        ]
        
        for issue in sample_issues:
            db.session.add(issue)
        
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)