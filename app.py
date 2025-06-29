from flask import Flask, render_template, request, jsonify
from assistant_core import reply, greet

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/greet")
def greet_route():
    return jsonify({"response": greet()})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"response": "No message received."}), 400
    user_msg = data["message"]

    try:
        bot_msg = reply(user_msg)
    except Exception:
        bot_msg = "Oops! Something went wrong."

    return jsonify({"response": bot_msg})

if __name__ == "__main__":
    app.run(debug=True)  
