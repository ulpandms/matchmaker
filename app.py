from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/game-plan", methods=["GET", "POST"])
def game_plan():
    if request.method == "POST":
        # TODO: handle submitted form data here
        # e.g. name = request.form.get("match_name")
        return redirect(url_for("home"))
    return render_template("game-plan.html")

if __name__ == "__main__":
    app.run(debug=True)
