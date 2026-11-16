import os
from shopkhata import create_app

app = create_app()

if __name__ == '__main__':
    # Default to port 5001 to avoid macOS Control Center AirPlay Receiver conflict on port 5000
    port = int(os.environ.get('PORT', 5001))
    print(f"\n==================================================")
    print(f"ShopKhata is running live at http://127.0.0.1:{port}")
    print(f"Demo Credentials: username = demo | password = demo123")
    print(f"==================================================\n")
    app.run(debug=True, host='0.0.0.0', port=port)
