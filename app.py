import os
from shopkhata import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # 5000 clashes with macOS AirPlay
    # Bind to localhost only by default. To open the app from your phone on the
    # same Wi-Fi, run:  HOST=0.0.0.0 python app.py
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    print("\n" + "=" * 50)
    print(f"ShopKhata is running at http://127.0.0.1:{port}")
    print("Demo login: username = demo | password = demo123")
    print("=" * 50 + "\n")
    app.run(debug=debug, host=host, port=port)
