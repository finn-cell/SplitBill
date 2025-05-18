from flask import Flask, request, jsonify, render_template
from splitter import ExpenseSplitter

app = Flask(__name__)
splitter = ExpenseSplitter(participants=["A", "B", "C"])

@app.route("/")
def index():
    # Render the HTML file (放在 templates 資料夾中)
    return render_template("home.html")

@app.route("/add_participant", methods=["POST"])
def add_participant():
    data = request.json
    participant = data["participant"]
    splitter.add_participant(participant)
    return jsonify({"message": f"Participant '{participant}' added successfully"})

@app.route("/delete_participant", methods=["POST"])
def delete_participant():
    data = request.json
    participant = data["participant"]
    splitter.delete_participant(participant)
    return jsonify({"message": f"Participant '{participant}' deleted successfully"})

@app.route("/get_participants", methods=["GET"])
def get_participants():
    return jsonify({"participants": splitter.get_participant()})

@app.route("/refresh_expenses", methods=["POST"])
def refresh_expenses():
    splitter.refresh_expenses()
    return jsonify({"message": "All expenses have been refreshed"})

@app.route("/delete_expense", methods=["POST"])
def delete_expense():
    data = request.json
    index = data["index"]
    splitter.delete_expense(index)
    return jsonify({"message": f"Expense at index {index} deleted successfully"})


if __name__ == "__main__":
    app.run(debug=True)
