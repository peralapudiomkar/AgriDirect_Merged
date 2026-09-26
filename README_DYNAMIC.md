# AgriDirect Dynamic Deployment Build

This build converts the Farmer, Buyer and Transporter dashboards into in-page dynamic workspaces.

## Run locally
1. `pip install -r requirements.txt`
2. `python app.py`
3. Open `http://127.0.0.1:5000`

Demo accounts:
- Farmer: farmer@agridirect.com / farmer123
- Buyer: buyer@agridirect.com / buyer123
- Transporter: 9876543210 / transporter123

## Dynamic features
- Farmer crop publishing/removal
- Buyer marketplace and order creation
- Shared orders between buyer/farmer/transporter
- Transporter status updates and live GPS
- Buyer/farmer live tracking
- Farmer suggestions and likes
- Profile and vehicle updates
- Notifications and dashboard statistics
- Government scheme links
- Smart crop advisor, market prices and weather planning
- Telugu/Hindi/English language script retained

## Deployment
`render.yaml` uses Gunicorn. For production, replace JSON file storage with a managed database (PostgreSQL recommended) if you need durable data across redeploys or multiple server instances.
