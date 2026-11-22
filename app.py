"""Flask entry point: serves the dashboard and the two analysis APIs."""
import os
import traceback

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from data import get_historical_data
from market import analyze_market
from smc import analyze_smc

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/market/<symbol>")
def api_market(symbol):
    try:
        df = get_historical_data(symbol, period="3mo", interval="1h")
        if df is None:
            return jsonify({"success": False, "message": f"No data for {symbol}"})
        a = analyze_market(df, symbol)
        if a is None:
            return jsonify({"success": False, "message": "Analysis failed"})
        return jsonify({"success": True, "analysis": a})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/api/smc/<symbol>")
def api_smc(symbol):
    try:
        df = get_historical_data(symbol, period="3mo", interval="1h")
        if df is None:
            return jsonify({"success": False, "message": f"No data for {symbol}"})
        a = analyze_smc(df, symbol)
        if a is None:
            return jsonify({"success": False, "message": "Analysis failed - check terminal for error"})
        return jsonify({"success": True, "analysis": a})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Error: {e}"})


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    print(f"Trading dashboard: http://{host}:{port}")
    app.run(debug=debug, host=host, port=port)
