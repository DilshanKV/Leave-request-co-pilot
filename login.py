from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__,static_url_path='/static')

# In-memory list to store user details
user_data = []

# Global variable to store the current employee_id
current_employee_id = None
current_employee_name = None

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/submit', methods=['POST'])
def submit():
    global current_employee_id,current_employee_name
    employee_id = request.form.get('employeeId')
    name = request.form.get('name')

    if not employee_id or not name:
        return "Please enter both Employee ID and Name."

    user_details = {"Employee ID": employee_id, "Name": name}
    user_data.append(user_details)

    current_employee_id = employee_id

    print("User Data:", user_data)

    return redirect(url_for('redirect_to_youtube'))

@app.route('/redirect_to_youtube')
def redirect_to_youtube():
    return redirect("http://localhost:8501")

# Expose an endpoint to get user details as JSON
@app.route('/get_user_details', methods=['GET'])
def get_user_details():
    return jsonify(user_data)

if __name__ == '__main__':
    app.run(debug=True)
