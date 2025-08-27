#!/usr/bin/env python3

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
except ImportError:
    print("gql library not installed. Install with: pip install gql[all]")
    sys.exit(1)

def send_order_reminders():
    # Setup GraphQL client
    transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)
    
    # Calculate date 7 days ago
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # GraphQL query to get recent orders
    query = gql("""
        query GetRecentOrders($orderDateGte: DateTime) {
            allOrders(filter: { orderDateGte: $orderDateGte }) {
                edges {
                    node {
                        id
                        orderDate
                        customer {
                            email
                            name
                        }
                    }
                }
            }
        }
    """)
    
    try:
        # Execute the query
        result = client.execute(query, variable_values={
            "orderDateGte": seven_days_ago.isoformat()
        })
        
        # Process results and log
        orders = result['allOrders']['edges']
        timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
        
        with open('/tmp/order_reminders_log.txt', 'a') as log_file:
            log_file.write(f"{timestamp} Processing {len(orders)} recent orders:\n")
            
            for order_edge in orders:
                order = order_edge['node']
                log_file.write(
                    f"{timestamp} Order ID: {order['id']}, "
                    f"Customer: {order['customer']['name']}, "
                    f"Email: {order['customer']['email']}\n"
                )
        
        print("Order reminders processed!")
        
    except Exception as e:
        timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
        with open('/tmp/order_reminders_log.txt', 'a') as log_file:
            log_file.write(f"{timestamp} Error processing order reminders: {str(e)}\n")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    send_order_reminders()