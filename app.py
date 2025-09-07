from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/event", methods=["GET", "POST"])
def event_info():
    # Placeholder so the Game On CTA works
    if request.method == "POST":
        # TODO: handle event form next
        return redirect(url_for("home"))
    return render_template("event.html")

if __name__ == "__main__":
    app.run(debug=True)
