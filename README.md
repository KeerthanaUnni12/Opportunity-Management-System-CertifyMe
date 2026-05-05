# Qatar Foundation Admin Portal (Backend Implementation)

This project is a backend implementation for the Qatar Foundation Admin Portal task provided by CertifyMe (Tech99 Innovations Pvt Ltd).

##  Tech Stack
- Python
- Flask
- SQLite (Database)
- HTML, CSS, JavaScript (Provided UI - unchanged)

##  Key Features

###  Authentication
- Admin Signup with validation
- Secure Login with session handling
- Remember Me functionality
- Forgot Password with token-based reset (expires in 1 hour)

###  Opportunity Management (CRUD)
- View all opportunities created by the logged-in admin
- Add new opportunities using a modal form
- Edit existing opportunities (pre-filled form)
- Delete opportunities with confirmation
- View full opportunity details

###  Data Handling
- All data is stored in SQLite database
- No hardcoded data used
- Opportunities persist across sessions
- Each admin can only access their own data

##  Task Requirements Covered
- Backend built using Flask as required
- Existing UI was NOT modified
- All user stories (US-1.1 to US-2.6) implemented
- Full CRUD operations integrated with frontend

##  Project Structure
backend/
app.py
models.py
templates/
admin.html
static/
admin.js
admin.css
